"""
TruthCert Lane A - Exploration Lane

Handles DRAFT mode extraction with fast, best-effort parsing.
No strict verification - bundles are tagged as DRAFT for human review.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json

from ..core.primitives import (
    ScopeLock,
    PolicyAnchor,
    CleanState,
    TerminalState,
    OutputType,
    ParseStatus,
)
from ..parsers.base_parser import BaseParser, ParsedDocument, TableData


@dataclass
class ExtractionCandidate:
    """A candidate extraction from a document."""
    field_name: str
    value: Any
    confidence: float
    source_location: str  # e.g., "table_1:row_3:col_2"
    raw_text: str
    context: str  # Surrounding text for human review


@dataclass
class DraftBundle:
    """
    A bundle in DRAFT state - not verified, for human review.

    DRAFT bundles bypass verification gates but are clearly
    marked as unverified. They can be promoted to verification
    lane later.
    """
    bundle_id: str
    scope_lock: ScopeLock
    extractions: List[ExtractionCandidate] = field(default_factory=list)
    document: Optional[ParsedDocument] = None
    parse_status: ParseStatus = ParseStatus.STABLE
    warnings: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_hash: str = ""

    @property
    def terminal_state(self) -> TerminalState:
        """DRAFT bundles are always in DRAFT state."""
        return TerminalState.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "bundle_id": self.bundle_id,
            "terminal_state": self.terminal_state.value,
            "scope_lock": {
                "endpoint": self.scope_lock.endpoint,
                "entities": list(self.scope_lock.entities),
                "units": self.scope_lock.units,
                "timepoint": self.scope_lock.timepoint,
                "inclusion_snippet": self.scope_lock.inclusion_snippet,
                "source_hash": self.scope_lock.source_hash,
            },
            "extractions": [
                {
                    "field_name": e.field_name,
                    "value": e.value,
                    "confidence": e.confidence,
                    "source_location": e.source_location,
                    "raw_text": e.raw_text,
                    "context": e.context,
                }
                for e in self.extractions
            ],
            "parse_status": self.parse_status.value,
            "warnings": self.warnings,
            "created_at": self.created_at.isoformat(),
            "source_hash": self.source_hash,
        }


class ExplorationLane:
    """
    Lane A - Exploration Mode

    Fast, best-effort extraction without rigorous verification.
    Produces DRAFT bundles for human review or later promotion
    to verification lane.

    Use Cases:
    - Initial document triage
    - Quick preview of extractable data
    - Research/exploration where DRAFT quality is acceptable
    """

    def __init__(
        self,
        parser: BaseParser,
        confidence_threshold: float = 0.5,
    ):
        self.parser = parser
        self.confidence_threshold = confidence_threshold
        self._bundle_counter = 0

    def explore(
        self,
        content: bytes,
        scope_lock: ScopeLock,
        content_type: str = "application/pdf",
        extraction_hints: Optional[Dict[str, Any]] = None,
    ) -> DraftBundle:
        """
        Explore a document and produce a DRAFT bundle.

        Args:
            content: Raw document bytes
            scope_lock: The scope lock defining extraction targets
            content_type: MIME type of document
            extraction_hints: Optional hints for extraction (field patterns, etc.)

        Returns:
            DraftBundle with extracted candidates
        """
        # Generate bundle ID
        self._bundle_counter += 1
        bundle_id = f"draft_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self._bundle_counter:04d}"

        # Compute source hash
        source_hash = hashlib.sha256(content).hexdigest()[:16]

        # Parse document
        try:
            document = self.parser.parse(content, content_type)
            parse_status = ParseStatus.STABLE
        except Exception as e:
            # Best-effort - continue even on parse errors
            document = ParsedDocument(
                text="",
                warnings=[f"Parse error: {str(e)}"],
                parser_name=self.parser.name,
            )
            parse_status = ParseStatus.KILL

        # Extract candidates based on scope lock
        extractions = self._extract_candidates(
            document,
            scope_lock,
            extraction_hints or {},
        )

        # Collect warnings
        warnings = list(document.warnings)
        if parse_status == ParseStatus.KILL:
            warnings.append("Document parsing failed - extractions may be incomplete")
        if not extractions:
            warnings.append("No extraction candidates found matching scope lock")

        return DraftBundle(
            bundle_id=bundle_id,
            scope_lock=scope_lock,
            extractions=extractions,
            document=document,
            parse_status=parse_status,
            warnings=warnings,
            source_hash=source_hash,
        )

    def _extract_candidates(
        self,
        document: ParsedDocument,
        scope_lock: ScopeLock,
        hints: Dict[str, Any],
    ) -> List[ExtractionCandidate]:
        """
        Extract candidate values based on scope lock.

        This is best-effort extraction - tries multiple strategies
        and returns all plausible candidates with confidence scores.
        """
        candidates = []

        # Strategy 1: Table-based extraction
        candidates.extend(self._extract_from_tables(document, scope_lock, hints))

        # Strategy 2: Text pattern extraction
        candidates.extend(self._extract_from_text(document, scope_lock, hints))

        # Strategy 3: Section-based extraction
        candidates.extend(self._extract_from_sections(document, scope_lock, hints))

        # Filter by confidence threshold
        candidates = [c for c in candidates if c.confidence >= self.confidence_threshold]

        # Deduplicate by field name and value
        seen = set()
        unique_candidates = []
        for c in candidates:
            key = (c.field_name, str(c.value))
            if key not in seen:
                seen.add(key)
                unique_candidates.append(c)

        return unique_candidates

    def _extract_from_tables(
        self,
        document: ParsedDocument,
        scope_lock: ScopeLock,
        hints: Dict[str, Any],
    ) -> List[ExtractionCandidate]:
        """Extract candidates from tables."""
        candidates = []

        # Target entities from scope lock
        target_entities = set(e.lower() for e in scope_lock.entities)
        target_endpoint = scope_lock.endpoint.lower()

        for table in document.tables:
            # Check if table might be relevant
            table_text = " ".join(
                " ".join(str(c.value) for c in row)
                for row in table.rows
            ).lower()

            if not any(entity in table_text for entity in target_entities):
                continue

            # Search for endpoint-related data
            for row_idx, row in enumerate(table.rows):
                if row_idx == 0 and table.headers:
                    continue  # Skip header row

                row_label = str(row[0].raw_text).lower() if row else ""

                for col_idx, cell in enumerate(row):
                    # Get column header
                    col_header = ""
                    if col_idx < len(table.headers):
                        col_header = table.headers[col_idx].lower()

                    # Check relevance
                    relevance_score = self._compute_relevance(
                        row_label,
                        col_header,
                        str(cell.value),
                        target_entities,
                        target_endpoint,
                    )

                    if relevance_score > 0 and cell.value is not None:
                        # Determine field name
                        field_name = self._infer_field_name(
                            row_label,
                            col_header,
                            target_endpoint,
                        )

                        # Get context
                        context = self._get_table_context(table, row_idx, col_idx)

                        candidates.append(ExtractionCandidate(
                            field_name=field_name,
                            value=cell.value,
                            confidence=min(0.9, relevance_score),
                            source_location=f"{table.table_id}:row_{row_idx}:col_{col_idx}",
                            raw_text=cell.raw_text,
                            context=context,
                        ))

        return candidates

    def _extract_from_text(
        self,
        document: ParsedDocument,
        scope_lock: ScopeLock,
        hints: Dict[str, Any],
    ) -> List[ExtractionCandidate]:
        """Extract candidates from document text using patterns."""
        import re
        candidates = []

        text = document.text
        target_endpoint = scope_lock.endpoint.lower()

        # Common patterns for numeric values with context
        patterns = [
            # "HR 0.85 (95% CI: 0.72-0.99)"
            (r'(?:HR|hazard ratio)[:\s]+(\d+\.?\d*)\s*(?:\(|,)?\s*(?:95%?\s*CI)?[:\s]*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',
             "hazard_ratio"),
            # "OR 2.15 (1.3-3.1)"
            (r'(?:OR|odds ratio)[:\s]+(\d+\.?\d*)\s*\((\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\)',
             "odds_ratio"),
            # "RR 1.25 (0.98, 1.56)"
            (r'(?:RR|risk ratio|relative risk)[:\s]+(\d+\.?\d*)\s*\((\d+\.?\d*)\s*[,–-]\s*(\d+\.?\d*)\)',
             "risk_ratio"),
            # "mean difference -2.5 (95% CI: -4.1 to -0.9)"
            (r'(?:mean difference|MD)[:\s]+([-]?\d+\.?\d*)\s*.*?(\d+\.?\d*)\s*to\s*([-]?\d+\.?\d*)',
             "mean_difference"),
            # "p = 0.003" or "p < 0.001"
            (r'p\s*[=<]\s*(\d+\.?\d*)',
             "p_value"),
            # "n = 245"
            (r'n\s*=\s*(\d+)',
             "sample_size"),
        ]

        for pattern, field_base in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get context around match
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                # Check relevance to endpoint
                if target_endpoint not in context.lower():
                    continue

                # Extract value(s)
                groups = match.groups()
                if len(groups) >= 3:
                    # Point estimate with CI
                    candidates.append(ExtractionCandidate(
                        field_name=f"{field_base}_point",
                        value=float(groups[0]),
                        confidence=0.7,
                        source_location=f"text:{match.start()}",
                        raw_text=match.group(0),
                        context=context,
                    ))
                    candidates.append(ExtractionCandidate(
                        field_name=f"{field_base}_ci_lower",
                        value=float(groups[1]),
                        confidence=0.7,
                        source_location=f"text:{match.start()}",
                        raw_text=match.group(0),
                        context=context,
                    ))
                    candidates.append(ExtractionCandidate(
                        field_name=f"{field_base}_ci_upper",
                        value=float(groups[2]),
                        confidence=0.7,
                        source_location=f"text:{match.start()}",
                        raw_text=match.group(0),
                        context=context,
                    ))
                elif len(groups) == 1:
                    candidates.append(ExtractionCandidate(
                        field_name=field_base,
                        value=float(groups[0]),
                        confidence=0.6,
                        source_location=f"text:{match.start()}",
                        raw_text=match.group(0),
                        context=context,
                    ))

        return candidates

    def _extract_from_sections(
        self,
        document: ParsedDocument,
        scope_lock: ScopeLock,
        hints: Dict[str, Any],
    ) -> List[ExtractionCandidate]:
        """Extract candidates from named sections."""
        candidates = []

        # Results section is most likely to contain outcome data
        results_section = document.get_section("results")
        if not results_section:
            return candidates

        # Use text extraction on results section
        text_candidates = self._extract_from_text(
            ParsedDocument(
                text=results_section,
                parser_name=document.parser_name,
            ),
            scope_lock,
            hints,
        )

        # Boost confidence for results section
        for c in text_candidates:
            c.confidence = min(0.95, c.confidence + 0.1)
            c.source_location = f"section:results:{c.source_location}"

        candidates.extend(text_candidates)
        return candidates

    def _compute_relevance(
        self,
        row_label: str,
        col_header: str,
        cell_value: str,
        target_entities: set,
        target_endpoint: str,
    ) -> float:
        """Compute relevance score for a cell."""
        score = 0.0

        combined_text = f"{row_label} {col_header}".lower()

        # Check for entity match
        for entity in target_entities:
            if entity in combined_text:
                score += 0.4
                break

        # Check for endpoint match
        if target_endpoint in combined_text:
            score += 0.4

        # Check if cell contains numeric value
        try:
            float(cell_value.replace("%", "").replace(",", ""))
            score += 0.2
        except (ValueError, AttributeError):
            pass

        return score

    def _infer_field_name(
        self,
        row_label: str,
        col_header: str,
        target_endpoint: str,
    ) -> str:
        """Infer a field name from row/column context."""
        # Clean up labels
        row_clean = row_label.strip().lower().replace(" ", "_")[:30]
        col_clean = col_header.strip().lower().replace(" ", "_")[:30]

        if row_clean and col_clean:
            return f"{row_clean}_{col_clean}"
        elif row_clean:
            return row_clean
        elif col_clean:
            return col_clean
        else:
            return target_endpoint.lower().replace(" ", "_")

    def _get_table_context(
        self,
        table: TableData,
        row_idx: int,
        col_idx: int,
    ) -> str:
        """Get context around a table cell."""
        context_parts = []

        # Add table ID
        context_parts.append(f"Table: {table.table_id}")

        # Add headers
        if table.headers:
            context_parts.append(f"Headers: {', '.join(table.headers)}")

        # Add row context
        if 0 <= row_idx < len(table.rows):
            row = table.rows[row_idx]
            row_text = " | ".join(str(c.value) for c in row)
            context_parts.append(f"Row: {row_text}")

        return "\n".join(context_parts)

    def batch_explore(
        self,
        documents: List[Tuple[bytes, str]],
        scope_lock: ScopeLock,
        extraction_hints: Optional[Dict[str, Any]] = None,
    ) -> List[DraftBundle]:
        """
        Explore multiple documents.

        Args:
            documents: List of (content, content_type) tuples
            scope_lock: Shared scope lock for all documents
            extraction_hints: Optional extraction hints

        Returns:
            List of DraftBundles
        """
        return [
            self.explore(content, scope_lock, content_type, extraction_hints)
            for content, content_type in documents
        ]
