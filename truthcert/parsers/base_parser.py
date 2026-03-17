"""
Base Parser Classes

Defines the interface for document parsers and table extraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import hashlib


@dataclass
class TableCell:
    """A single cell in a table."""
    value: Any
    row: int
    col: int
    raw_text: str = ""
    is_header: bool = False
    span_rows: int = 1
    span_cols: int = 1


@dataclass
class TableData:
    """Extracted table data with structure information."""
    rows: List[List[TableCell]]
    headers: List[str] = field(default_factory=list)
    n_rows: int = 0
    n_cols: int = 0
    source_page: Optional[int] = None
    source_region: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    table_id: str = ""

    def __post_init__(self):
        if self.rows:
            self.n_rows = len(self.rows)
            self.n_cols = max(len(row) for row in self.rows) if self.rows else 0

    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        """Get cell at position."""
        if 0 <= row < len(self.rows) and 0 <= col < len(self.rows[row]):
            return self.rows[row][col]
        return None

    def get_column(self, col: int) -> List[TableCell]:
        """Get all cells in a column."""
        return [row[col] for row in self.rows if col < len(row)]

    def get_row(self, row: int) -> List[TableCell]:
        """Get all cells in a row."""
        if 0 <= row < len(self.rows):
            return self.rows[row]
        return []

    def compute_hash(self) -> str:
        """Compute hash of table structure and content."""
        data = {
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "headers": self.headers,
            "values": [[c.value for c in row] for row in self.rows],
        }
        import json
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "headers": self.headers,
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "data": [[c.value for c in row] for row in self.rows],
            "table_id": self.table_id,
        }


@dataclass
class ParsedDocument:
    """Result of parsing a document."""
    text: str
    tables: List[TableData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    parser_name: str = ""
    parse_time_ms: int = 0

    def get_table_by_id(self, table_id: str) -> Optional[TableData]:
        """Find table by ID."""
        for table in self.tables:
            if table.table_id == table_id:
                return table
        return None

    def get_section(self, name: str) -> Optional[str]:
        """Get a named section."""
        # Try exact match
        if name in self.sections:
            return self.sections[name]
        # Try case-insensitive match
        name_lower = name.lower()
        for key, value in self.sections.items():
            if key.lower() == name_lower:
                return value
        return None


class BaseParser(ABC):
    """
    Abstract base class for document parsers.

    All parsers must implement the parse method and provide
    consistent output format for arbitration.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def parse(self, content: bytes, content_type: str = "application/pdf") -> ParsedDocument:
        """
        Parse document content.

        Args:
            content: Raw document bytes
            content_type: MIME type of the document

        Returns:
            ParsedDocument with extracted text, tables, and metadata
        """
        pass

    @abstractmethod
    def can_parse(self, content_type: str) -> bool:
        """Check if this parser supports the given content type."""
        pass

    def extract_numeric_values(self, text: str) -> List[Tuple[float, str]]:
        """
        Extract numeric values with their context.

        Returns list of (value, surrounding_text) tuples.
        """
        import re

        # Pattern for numbers (including decimals, percentages, scientific notation)
        pattern = r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?(?:\s*%)?'

        results = []
        for match in re.finditer(pattern, text):
            value_str = match.group()
            try:
                # Handle percentage
                if '%' in value_str:
                    value = float(value_str.replace('%', '').strip()) / 100
                else:
                    value = float(value_str)

                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                results.append((value, context))
            except ValueError:
                continue

        return results

    def detect_table_structure(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Detect potential table regions in text.

        Returns list of detected table regions with boundaries.
        """
        import re

        tables = []
        current_table = None
        table_line_pattern = re.compile(r'[\|\t]|(\s{2,})')

        for i, line in enumerate(lines):
            # Check if line looks like a table row
            is_table_line = bool(table_line_pattern.search(line)) and len(line.split()) >= 2

            if is_table_line:
                if current_table is None:
                    current_table = {"start": i, "lines": []}
                current_table["lines"].append(line)
            else:
                if current_table and len(current_table["lines"]) >= 2:
                    current_table["end"] = i
                    tables.append(current_table)
                current_table = None

        # Handle table at end of document
        if current_table and len(current_table["lines"]) >= 2:
            current_table["end"] = len(lines)
            tables.append(current_table)

        return tables


class SimpleTextParser(BaseParser):
    """
    Simple text-based parser for basic document extraction.
    Used as a fallback or for plain text documents.
    """

    def __init__(self):
        super().__init__("simple_text")

    def can_parse(self, content_type: str) -> bool:
        return content_type in ["text/plain", "text/html", "application/pdf"]

    def parse(self, content: bytes, content_type: str = "text/plain") -> ParsedDocument:
        import time
        start_time = time.time()

        # Decode content
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')

        # Split into lines
        lines = text.split('\n')

        # Detect sections
        sections = self._detect_sections(lines)

        # Detect tables
        table_regions = self.detect_table_structure(lines)
        tables = []

        for i, region in enumerate(table_regions):
            table = self._parse_table_region(region["lines"])
            if table:
                table.table_id = f"table_{i+1}"
                tables.append(table)

        parse_time = int((time.time() - start_time) * 1000)

        return ParsedDocument(
            text=text,
            tables=tables,
            metadata={"line_count": len(lines)},
            sections=sections,
            parser_name=self.name,
            parse_time_ms=parse_time,
        )

    def _detect_sections(self, lines: List[str]) -> Dict[str, str]:
        """Detect document sections by headings."""
        import re

        sections = {}
        current_section = "introduction"
        current_content = []

        # Common section headings
        section_patterns = [
            (r'^(?:abstract|summary)\s*:?\s*$', 'abstract'),
            (r'^(?:introduction|background)\s*:?\s*$', 'introduction'),
            (r'^(?:methods?|materials?\s+and\s+methods?)\s*:?\s*$', 'methods'),
            (r'^(?:results?)\s*:?\s*$', 'results'),
            (r'^(?:discussion)\s*:?\s*$', 'discussion'),
            (r'^(?:conclusions?)\s*:?\s*$', 'conclusions'),
            (r'^(?:references?|bibliography)\s*:?\s*$', 'references'),
        ]

        for line in lines:
            line_lower = line.strip().lower()

            # Check if this is a section heading
            new_section = None
            for pattern, section_name in section_patterns:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    new_section = section_name
                    break

            if new_section:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = new_section
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _parse_table_region(self, lines: List[str]) -> Optional[TableData]:
        """Parse lines that appear to be a table."""
        import re

        if len(lines) < 2:
            return None

        rows = []
        max_cols = 0

        for line in lines:
            # Split by common delimiters
            if '|' in line:
                cells = [c.strip() for c in line.split('|') if c.strip()]
            elif '\t' in line:
                cells = [c.strip() for c in line.split('\t') if c.strip()]
            else:
                # Split by multiple spaces
                cells = re.split(r'\s{2,}', line.strip())

            if cells:
                row = [
                    TableCell(
                        value=self._parse_cell_value(c),
                        row=len(rows),
                        col=i,
                        raw_text=c,
                    )
                    for i, c in enumerate(cells)
                ]
                rows.append(row)
                max_cols = max(max_cols, len(cells))

        if not rows:
            return None

        # Try to identify headers (first row if it looks like headers)
        headers = []
        if rows and all(isinstance(c.value, str) for c in rows[0]):
            headers = [c.raw_text for c in rows[0]]

        return TableData(rows=rows, headers=headers)

    def _parse_cell_value(self, text: str) -> Any:
        """Parse a cell value to appropriate type."""
        text = text.strip()

        # Try float
        try:
            if '%' in text:
                return float(text.replace('%', '').strip()) / 100
            return float(text)
        except ValueError:
            pass

        # Try int
        try:
            return int(text)
        except ValueError:
            pass

        # Return as string
        return text
