"""
TruthCert Failure Memory System

Implements RAG-based learning from past failures.
Supports similarity search and structural warning injection.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
import numpy as np
from datetime import datetime


@dataclass
class FailurePattern:
    """A detected failure pattern from the ledger."""
    signature: str
    count: int
    source_contexts: List[str]
    correction_hints: List[str]
    embedding: Optional[np.ndarray] = None


class SimilaritySearch:
    """
    Simple similarity search for failure patterns.
    Uses cosine similarity on embeddings.
    """

    def __init__(self):
        self.patterns: List[FailurePattern] = []
        self.embeddings: Optional[np.ndarray] = None

    def add_pattern(self, pattern: FailurePattern) -> None:
        """Add a failure pattern to the search index."""
        self.patterns.append(pattern)
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the embedding index."""
        embeddings = []
        for p in self.patterns:
            if p.embedding is not None:
                embeddings.append(p.embedding)
            else:
                # Generate a simple hash-based pseudo-embedding if none provided
                embeddings.append(self._pseudo_embedding(p.signature))

        if embeddings:
            self.embeddings = np.array(embeddings)

    def _pseudo_embedding(self, text: str, dim: int = 768) -> np.ndarray:
        """Generate a deterministic pseudo-embedding from text."""
        # Use hash to create reproducible embedding
        h = hashlib.sha256(text.encode()).digest()
        # Expand hash to fill embedding dimensions
        expanded = h * (dim // 32 + 1)
        arr = np.frombuffer(expanded[:dim], dtype=np.uint8).astype(np.float32)
        # Normalize
        arr = (arr - 127.5) / 127.5
        return arr / (np.linalg.norm(arr) + 1e-8)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> List[Tuple[FailurePattern, float]]:
        """
        Search for similar failure patterns.

        Returns list of (pattern, similarity_score) tuples.
        """
        if self.embeddings is None or len(self.patterns) == 0:
            return []

        # Normalize query
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)

        # Compute cosine similarities
        similarities = np.dot(self.embeddings, query_norm)

        # Get top-k above threshold
        indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in indices:
            sim = similarities[idx]
            if sim >= threshold:
                results.append((self.patterns[idx], float(sim)))

        return results


class FailureMemory:
    """
    Memory system for learning from past failures.
    Implements Gate B10 (RAG) functionality.

    Critical Rule: structure_only = True
    Never inject content hints, only structural warnings.
    """

    def __init__(self):
        self.similarity_search = SimilaritySearch()
        self.pattern_count: Dict[str, int] = {}

    def record_failure(
        self,
        signature: str,
        source_context: str,
        correction_hint: str,
        embedding: Optional[np.ndarray] = None,
    ) -> None:
        """Record a failure for future learning."""
        # Update pattern count
        self.pattern_count[signature] = self.pattern_count.get(signature, 0) + 1

        # Check if pattern already exists
        for pattern in self.similarity_search.patterns:
            if pattern.signature == signature:
                pattern.count = self.pattern_count[signature]
                pattern.source_contexts.append(source_context)
                pattern.correction_hints.append(correction_hint)
                return

        # Add new pattern
        pattern = FailurePattern(
            signature=signature,
            count=1,
            source_contexts=[source_context],
            correction_hints=[correction_hint],
            embedding=embedding,
        )
        self.similarity_search.add_pattern(pattern)

    def get_structural_warnings(
        self,
        document_features: Dict[str, Any],
        top_k: int = 3,
    ) -> List[str]:
        """
        Get STRUCTURAL warnings based on similar past failures.

        Critical Rule: Returns only structural hints, never content.
        """
        warnings = []

        # Generate embedding for document features
        feature_text = json.dumps(document_features, sort_keys=True)
        query_embedding = self.similarity_search._pseudo_embedding(feature_text)

        # Search for similar failures
        similar = self.similarity_search.search(
            query_embedding,
            top_k=top_k,
            threshold=0.4,
        )

        for pattern, similarity in similar:
            if pattern.count >= 3:  # Only warn about recurring patterns
                # Extract structural warning (not content!)
                warning = self._extract_structural_warning(pattern)
                if warning:
                    warnings.append(warning)

        return warnings

    def _extract_structural_warning(self, pattern: FailurePattern) -> Optional[str]:
        """
        Extract a structural warning from a failure pattern.

        CRITICAL: This must NEVER include content hints.
        Only structural characteristics allowed.
        """
        sig = pattern.signature.lower()

        # Map signatures to structural warnings
        structural_warnings = {
            "table_misalignment": "WARNING: Document contains tables that may have alignment issues. Verify row-column correspondence carefully.",
            "multi_table": "WARNING: Document contains multiple tables. Ensure values are extracted from the correct table.",
            "header_mismatch": "WARNING: Table headers may not match expected schema. Verify column identification.",
            "footnote_confusion": "WARNING: Document contains footnotes that may affect value interpretation. Check for footnote indicators.",
            "unit_inconsistency": "WARNING: Document may contain inconsistent units. Verify unit conversion.",
            "timepoint_ambiguity": "WARNING: Multiple timepoints present. Verify correct timepoint extraction.",
            "arm_label_variation": "WARNING: Treatment arm labels may vary. Verify arm identification.",
            "derived_vs_raw": "WARNING: Document contains both raw and derived values. Distinguish source carefully.",
            "ci_format_variation": "WARNING: Confidence intervals may use non-standard formats. Verify CI parsing.",
            "missing_data_codes": "WARNING: Document may use non-standard missing data codes. Check for NR, NA, ND, etc.",
        }

        for key, warning in structural_warnings.items():
            if key in sig:
                return warning

        # Generic structural warning for unknown patterns
        if pattern.count >= 5:
            return f"WARNING: Similar documents have failed extraction {pattern.count} times. Exercise extra caution."

        return None

    def get_recurring_patterns(self, min_count: int = 3) -> List[FailurePattern]:
        """Get failure patterns that occur frequently."""
        return [
            p for p in self.similarity_search.patterns
            if p.count >= min_count
        ]

    def suggest_validator(
        self,
        pattern: FailurePattern,
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest a new validator rule based on a failure pattern.

        Part of validator discovery pipeline.
        """
        if pattern.count < 3:
            return None

        # Analyze correction hints for commonalities
        hints = pattern.correction_hints
        if not hints:
            return None

        return {
            "pattern_description": pattern.signature,
            "occurrence_count": pattern.count,
            "proposed_check": self._infer_check_from_hints(hints),
            "estimated_coverage": min(0.8, pattern.count / 10),
            "confidence": min(0.9, pattern.count / 20),
            "source_contexts": pattern.source_contexts[:3],  # Sample contexts
        }

    def _infer_check_from_hints(self, hints: List[str]) -> str:
        """Infer a validation check from correction hints."""
        # Simple keyword-based inference
        hint_text = " ".join(hints).lower()

        if "swap" in hint_text or "reversed" in hint_text:
            return "arm_value_swap_check"
        elif "unit" in hint_text:
            return "unit_consistency_check"
        elif "table" in hint_text:
            return "table_structure_validation"
        elif "total" in hint_text or "sum" in hint_text:
            return "totals_reconciliation_check"
        elif "timepoint" in hint_text:
            return "timepoint_alignment_check"
        else:
            return "general_consistency_check"
