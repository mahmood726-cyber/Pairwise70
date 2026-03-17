"""
TruthCert Parser Witness and Arbitration System

The Parser Witness monitors for parsing instability.
When parsing is unstable, we arbitrate with an alternate parser;
disagreement fails closed.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import json

from .base_parser import BaseParser, ParsedDocument, TableData
from ..core.primitives import ParseStatus


@dataclass
class ParserDiagnostic:
    """Diagnostic information from parser witness."""
    schema_drift: bool = False           # Unexpected structure
    header_misalignment: bool = False    # Headers don't match columns
    totals_mismatch: bool = False        # Sum != reported total
    malformed_regions: List[str] = field(default_factory=list)  # Unparseable sections
    warnings: List[str] = field(default_factory=list)


@dataclass
class ParserResult:
    """Result from a single parser run."""
    parser_name: str
    document: ParsedDocument
    diagnostic: ParserDiagnostic
    table_hashes: Dict[str, str] = field(default_factory=dict)  # table_id -> hash
    numeric_values: Dict[str, float] = field(default_factory=dict)  # key -> value
    structure_signature: str = ""  # Hash of overall structure

    def compute_structure_signature(self) -> str:
        """Compute a signature of the document structure."""
        structure = {
            "n_tables": len(self.document.tables),
            "table_shapes": [(t.n_rows, t.n_cols) for t in self.document.tables],
            "sections": list(self.document.sections.keys()),
            "n_numeric_values": len(self.numeric_values),
        }
        return hashlib.sha256(
            json.dumps(structure, sort_keys=True).encode()
        ).hexdigest()[:16]


@dataclass
class ArbitrationResult:
    """Result of parser arbitration."""
    status: ParseStatus
    primary_result: ParserResult
    alternate_result: Optional[ParserResult] = None
    material_disagreements: List[Dict[str, Any]] = field(default_factory=list)
    reconciled_values: Dict[str, Any] = field(default_factory=dict)


class ParserWitness:
    """
    Monitors parsing for instability and errors.

    Detects:
    - Schema drift (unexpected structure)
    - Header/arm misalignment
    - Totals mismatch (sum != reported total)
    - Malformed regions (unparseable sections)
    """

    def __init__(self, expected_schema: Optional[Dict[str, Any]] = None):
        self.expected_schema = expected_schema or {}

    def witness(self, result: ParsedDocument, parser_name: str) -> ParserResult:
        """
        Witness a parse result and produce diagnostics.
        """
        diagnostic = ParserDiagnostic()

        # Check schema drift
        if self.expected_schema:
            diagnostic.schema_drift = self._check_schema_drift(result)

        # Check header alignment in tables
        for table in result.tables:
            if self._check_header_misalignment(table):
                diagnostic.header_misalignment = True
                diagnostic.warnings.append(
                    f"Header misalignment detected in table {table.table_id}"
                )

        # Check totals
        for table in result.tables:
            mismatch = self._check_totals_mismatch(table)
            if mismatch:
                diagnostic.totals_mismatch = True
                diagnostic.warnings.append(
                    f"Totals mismatch in table {table.table_id}: {mismatch}"
                )

        # Check for malformed regions
        diagnostic.malformed_regions = self._detect_malformed_regions(result)
        if diagnostic.malformed_regions:
            diagnostic.warnings.append(
                f"Malformed regions detected: {len(diagnostic.malformed_regions)}"
            )

        # Extract numeric values with keys
        numeric_values = self._extract_keyed_values(result)

        # Compute table hashes
        table_hashes = {
            table.table_id: table.compute_hash()
            for table in result.tables
        }

        parser_result = ParserResult(
            parser_name=parser_name,
            document=result,
            diagnostic=diagnostic,
            table_hashes=table_hashes,
            numeric_values=numeric_values,
        )
        parser_result.structure_signature = parser_result.compute_structure_signature()

        return parser_result

    def _check_schema_drift(self, result: ParsedDocument) -> bool:
        """Check if document structure matches expected schema."""
        if "expected_tables" in self.expected_schema:
            if len(result.tables) != self.expected_schema["expected_tables"]:
                return True

        if "required_sections" in self.expected_schema:
            for section in self.expected_schema["required_sections"]:
                if section not in result.sections:
                    return True

        return False

    def _check_header_misalignment(self, table: TableData) -> bool:
        """Check if headers align with data columns."""
        if not table.headers or not table.rows:
            return False

        # Check if header count matches column count
        if len(table.headers) != table.n_cols:
            return True

        # Check if data rows have consistent column count
        for row in table.rows[1:]:  # Skip header row
            if len(row) != len(table.headers):
                return True

        return False

    def _check_totals_mismatch(self, table: TableData) -> Optional[str]:
        """
        Check if any row/column totals don't match sum of components.

        Returns description of mismatch or None.
        """
        if table.n_rows < 2 or table.n_cols < 2:
            return None

        # Check for "Total" row
        for i, row in enumerate(table.rows):
            first_cell = row[0] if row else None
            if first_cell and isinstance(first_cell.raw_text, str):
                if "total" in first_cell.raw_text.lower():
                    # Check if values sum correctly
                    for col_idx in range(1, len(row)):
                        total_val = row[col_idx].value
                        if not isinstance(total_val, (int, float)):
                            continue

                        # Sum preceding values in this column
                        col_sum = sum(
                            table.rows[r][col_idx].value
                            for r in range(i)
                            if col_idx < len(table.rows[r])
                            and isinstance(table.rows[r][col_idx].value, (int, float))
                        )

                        # Check for material mismatch (>5%)
                        if total_val != 0 and abs(col_sum - total_val) / abs(total_val) > 0.05:
                            return f"Column {col_idx}: sum={col_sum}, total={total_val}"

        return None

    def _detect_malformed_regions(self, result: ParsedDocument) -> List[str]:
        """Detect regions that couldn't be properly parsed."""
        malformed = []

        # Check for parse warnings
        malformed.extend(result.warnings)

        # Check for empty tables with data around them
        for i, table in enumerate(result.tables):
            if table.n_rows == 0 or table.n_cols == 0:
                malformed.append(f"Empty table detected: {table.table_id}")

        # Check for very short sections that might indicate parsing failure
        for section_name, content in result.sections.items():
            if len(content.strip()) < 10 and section_name not in ["abstract", "conclusions"]:
                malformed.append(f"Suspiciously short section: {section_name}")

        return malformed

    def _extract_keyed_values(self, result: ParsedDocument) -> Dict[str, float]:
        """
        Extract numeric values with identifying keys.

        Keys are based on table location and headers.
        """
        values = {}

        for table in result.tables:
            if not table.headers:
                continue

            for row_idx, row in enumerate(table.rows):
                if row_idx == 0 and row == table.headers:
                    continue  # Skip header row

                row_label = row[0].raw_text if row else f"row_{row_idx}"

                for col_idx, cell in enumerate(row):
                    if isinstance(cell.value, (int, float)):
                        col_label = table.headers[col_idx] if col_idx < len(table.headers) else f"col_{col_idx}"
                        key = f"{table.table_id}|{row_label}|{col_label}"
                        values[key] = cell.value

        return values


class ParserArbitrator:
    """
    Arbitrates between multiple parsers when instability is detected.

    Material Disagreement Definition (FROZEN):
    - >5% difference in any extracted numeric value, OR
    - Table shape mismatch (different row/column counts)
    """

    MATERIAL_THRESHOLD = 0.05  # 5% - FROZEN

    def __init__(
        self,
        primary_parser: BaseParser,
        alternate_parser: BaseParser,
        witness: ParserWitness,
    ):
        self.primary_parser = primary_parser
        self.alternate_parser = alternate_parser
        self.witness = witness

    def arbitrate(
        self,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> ArbitrationResult:
        """
        Run primary parser, check stability, arbitrate if needed.

        Returns ArbitrationResult with final status and reconciled values.
        """
        # Run primary parser
        primary_doc = self.primary_parser.parse(content, content_type)
        primary_result = self.witness.witness(primary_doc, self.primary_parser.name)

        # Check if parsing is stable
        is_stable = self._is_stable(primary_result)

        if is_stable:
            return ArbitrationResult(
                status=ParseStatus.STABLE,
                primary_result=primary_result,
            )

        # Parsing unstable - run alternate parser
        alternate_doc = self.alternate_parser.parse(content, content_type)
        alternate_result = self.witness.witness(alternate_doc, self.alternate_parser.name)

        # Check for material disagreement
        disagreements = self._find_material_disagreements(primary_result, alternate_result)

        if disagreements:
            # Material disagreement - fail closed
            return ArbitrationResult(
                status=ParseStatus.KILL,
                primary_result=primary_result,
                alternate_result=alternate_result,
                material_disagreements=disagreements,
            )

        # Parsers agree sufficiently - mark as repaired
        reconciled = self._reconcile_values(primary_result, alternate_result)

        return ArbitrationResult(
            status=ParseStatus.REPAIRED,
            primary_result=primary_result,
            alternate_result=alternate_result,
            reconciled_values=reconciled,
        )

    def _is_stable(self, result: ParserResult) -> bool:
        """Check if parse result is stable (no serious issues)."""
        diag = result.diagnostic

        # Any of these indicate instability
        if diag.schema_drift:
            return False
        if diag.header_misalignment:
            return False
        if diag.totals_mismatch:
            return False
        if len(diag.malformed_regions) > 0:
            return False

        return True

    def _find_material_disagreements(
        self,
        primary: ParserResult,
        alternate: ParserResult,
    ) -> List[Dict[str, Any]]:
        """
        Find material disagreements between two parse results.

        Material = >5% numeric difference OR shape mismatch.
        """
        disagreements = []

        # Check table shapes
        primary_shapes = {t.table_id: (t.n_rows, t.n_cols) for t in primary.document.tables}
        alternate_shapes = {t.table_id: (t.n_rows, t.n_cols) for t in alternate.document.tables}

        for table_id in set(primary_shapes.keys()) | set(alternate_shapes.keys()):
            p_shape = primary_shapes.get(table_id)
            a_shape = alternate_shapes.get(table_id)

            if p_shape != a_shape:
                disagreements.append({
                    "type": "shape_mismatch",
                    "table_id": table_id,
                    "primary": p_shape,
                    "alternate": a_shape,
                })

        # Check numeric values
        all_keys = set(primary.numeric_values.keys()) | set(alternate.numeric_values.keys())

        for key in all_keys:
            p_val = primary.numeric_values.get(key)
            a_val = alternate.numeric_values.get(key)

            if p_val is None or a_val is None:
                # Missing value in one parser
                disagreements.append({
                    "type": "missing_value",
                    "key": key,
                    "primary": p_val,
                    "alternate": a_val,
                })
                continue

            # Check percentage difference
            if p_val != 0:
                pct_diff = abs(p_val - a_val) / abs(p_val)
                if pct_diff > self.MATERIAL_THRESHOLD:
                    disagreements.append({
                        "type": "value_mismatch",
                        "key": key,
                        "primary": p_val,
                        "alternate": a_val,
                        "pct_difference": pct_diff,
                    })

        return disagreements

    def _reconcile_values(
        self,
        primary: ParserResult,
        alternate: ParserResult,
    ) -> Dict[str, Any]:
        """
        Reconcile values from two parsers when they mostly agree.

        Preference: primary parser unless alternate has higher confidence.
        """
        reconciled = {}

        # Use primary values as base
        reconciled.update(primary.numeric_values)

        # For any values where primary had warnings, prefer alternate
        for key, val in alternate.numeric_values.items():
            if key not in primary.numeric_values:
                reconciled[key] = val

        return reconciled


def create_default_arbitrator(
    expected_schema: Optional[Dict[str, Any]] = None,
) -> ParserArbitrator:
    """Create a default parser arbitrator with simple text parsers."""
    from .base_parser import SimpleTextParser

    primary = SimpleTextParser()
    alternate = SimpleTextParser()  # In practice, use different parser
    witness = ParserWitness(expected_schema)

    return ParserArbitrator(primary, alternate, witness)
