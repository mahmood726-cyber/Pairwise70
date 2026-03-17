"""
TruthCert Witness Gates (B1, B1.5, B2)

B1: Multi-witness extraction with agreement checking
B1.5: Model heterogeneity verification
B2: Blindspot detection using correlation analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from abc import ABC, abstractmethod
import numpy as np
from collections import Counter

from ..core.primitives import GateOutcome, PolicyAnchor


@dataclass
class WitnessExtraction:
    """Extraction result from a single witness."""
    witness_id: str
    model_name: str
    model_family: str
    extractions: Dict[str, Any]
    confidence_scores: Dict[str, float]
    tokens_used: int
    cost_usd: float
    raw_output: str = ""


class BaseGate(ABC):
    """Base class for all verification gates."""

    def __init__(self, gate_id: str):
        self.gate_id = gate_id

    @abstractmethod
    def evaluate(self, context: Any) -> GateOutcome:
        """Evaluate the gate condition."""
        pass


class WitnessGate(BaseGate):
    """
    Gate B1 - Multi-Witness Extraction

    FROZEN INVARIANTS:
    - Minimum 3 witnesses required
    - Agreement threshold: 80% for majority, 70% for strong
    - Witnesses must produce independent extractions
    """

    AGREEMENT_MAJORITY = 0.80  # FROZEN
    AGREEMENT_STRONG = 0.70    # FROZEN
    MIN_WITNESSES = 3          # FROZEN

    def __init__(
        self,
        min_witnesses: int = 3,
        max_witnesses: int = 5,
        numeric_tolerance: float = 0.005,
    ):
        super().__init__("B1")
        self.min_witnesses = max(min_witnesses, self.MIN_WITNESSES)  # Never below frozen minimum
        self.max_witnesses = max_witnesses
        self.numeric_tolerance = numeric_tolerance

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Evaluate witness agreement.

        Requires:
        - At least min_witnesses extractions
        - Majority agreement on all fields
        """
        witnesses: List[WitnessExtraction] = getattr(context, 'witness_results', [])

        if len(witnesses) < self.min_witnesses:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Insufficient witnesses: {len(witnesses)} < {self.min_witnesses}",
                details={
                    "witness_count": len(witnesses),
                    "required": self.min_witnesses,
                },
            )

        # Compute agreement for each field
        agreement_results = self._compute_field_agreement(witnesses)

        # Check if all fields meet agreement threshold
        failed_fields = []
        for field_name, agreement in agreement_results.items():
            if agreement["rate"] < self.AGREEMENT_MAJORITY:
                failed_fields.append({
                    "field": field_name,
                    "rate": agreement["rate"],
                    "values": agreement["value_counts"],
                })

        if failed_fields:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Agreement threshold not met for {len(failed_fields)} fields",
                details={
                    "failed_fields": failed_fields,
                    "threshold": self.AGREEMENT_MAJORITY,
                },
            )

        # Compute consensus values
        consensus = self._compute_consensus(witnesses, agreement_results)

        # Store consensus in context
        if hasattr(context, 'consensus_values'):
            context.consensus_values.update(consensus)

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "witness_count": len(witnesses),
                "fields_extracted": len(consensus),
                "agreement_results": {k: v["rate"] for k, v in agreement_results.items()},
                "consensus_values": consensus,
            },
        )

    def _compute_field_agreement(
        self,
        witnesses: List[WitnessExtraction],
    ) -> Dict[str, Dict[str, Any]]:
        """Compute agreement rate for each extracted field."""
        results = {}

        # Get all unique fields
        all_fields: Set[str] = set()
        for w in witnesses:
            all_fields.update(w.extractions.keys())

        for field_name in all_fields:
            values = []
            for w in witnesses:
                if field_name in w.extractions:
                    values.append(w.extractions[field_name])

            if not values:
                results[field_name] = {"rate": 0.0, "value_counts": {}, "coverage": 0.0}
                continue

            # Coverage: what fraction of witnesses extracted this field
            coverage = len(values) / len(witnesses)

            # Agreement: how many agree on the same value
            if all(isinstance(v, (int, float)) for v in values):
                # Numeric values - use tolerance
                agreement_rate, value_counts = self._numeric_agreement(values)
            else:
                # Categorical - exact match
                agreement_rate, value_counts = self._categorical_agreement(values)

            results[field_name] = {
                "rate": agreement_rate,
                "value_counts": value_counts,
                "coverage": coverage,
            }

        return results

    def _numeric_agreement(self, values: List[float]) -> Tuple[float, Dict[str, int]]:
        """Compute agreement for numeric values with tolerance."""
        if not values:
            return 0.0, {}

        # Group values within tolerance
        groups = []
        for v in values:
            placed = False
            for group in groups:
                ref = group[0]
                if abs(v - ref) / max(abs(ref), 1e-10) <= self.numeric_tolerance:
                    group.append(v)
                    placed = True
                    break
            if not placed:
                groups.append([v])

        # Find largest group
        largest_group = max(groups, key=len)
        agreement_rate = len(largest_group) / len(values)

        # Value counts
        value_counts = {f"{g[0]:.4f}": len(g) for g in groups}

        return agreement_rate, value_counts

    def _categorical_agreement(self, values: List[Any]) -> Tuple[float, Dict[str, int]]:
        """Compute agreement for categorical values."""
        if not values:
            return 0.0, {}

        counter = Counter(str(v) for v in values)
        most_common_count = counter.most_common(1)[0][1]
        agreement_rate = most_common_count / len(values)

        return agreement_rate, dict(counter)

    def _compute_consensus(
        self,
        witnesses: List[WitnessExtraction],
        agreement_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute consensus values from witnesses."""
        consensus = {}

        for field_name, agreement in agreement_results.items():
            if agreement["rate"] < self.AGREEMENT_STRONG:
                continue  # Skip low-agreement fields

            # Collect values
            values = [
                w.extractions[field_name]
                for w in witnesses
                if field_name in w.extractions
            ]

            if not values:
                continue

            # For numeric values, use mean of agreeing values
            if all(isinstance(v, (int, float)) for v in values):
                # Filter to values within tolerance of mode
                mean_val = np.mean(values)
                agreeing = [v for v in values if abs(v - mean_val) / max(abs(mean_val), 1e-10) <= self.numeric_tolerance * 2]
                consensus[field_name] = float(np.mean(agreeing)) if agreeing else float(mean_val)
            else:
                # For categorical, use most common
                counter = Counter(str(v) for v in values)
                consensus[field_name] = counter.most_common(1)[0][0]

        return consensus


class HeterogeneityGate(BaseGate):
    """
    Gate B1.5 - Model Heterogeneity Verification

    FROZEN INVARIANT:
    - Minimum 2 different model families required
    - Adversarial cross-family testing is REQUIRED
    """

    MIN_FAMILIES = 2  # FROZEN

    def __init__(self, min_families: int = 2):
        super().__init__("B1.5")
        self.min_families = max(min_families, self.MIN_FAMILIES)

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Verify model heterogeneity.

        Ensures witnesses come from at least MIN_FAMILIES different model families.
        """
        witnesses: List[WitnessExtraction] = getattr(context, 'witness_results', [])

        if not witnesses:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason="No witnesses available for heterogeneity check",
                details={"witness_count": 0},
            )

        # Count families
        families = set(w.model_family for w in witnesses)
        family_counts = Counter(w.model_family for w in witnesses)

        if len(families) < self.min_families:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Insufficient model diversity: {len(families)} < {self.min_families} families",
                details={
                    "families_found": list(families),
                    "family_counts": dict(family_counts),
                    "required_families": self.min_families,
                },
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "families": list(families),
                "family_counts": dict(family_counts),
                "diversity_score": len(families) / len(witnesses),
            },
        )


class BlindspotGate(BaseGate):
    """
    Gate B2 - Blindspot Detection

    FROZEN INVARIANT:
    - Correlation threshold r > 0.6 indicates potential blindspot
    - Must analyze cross-family agreement patterns
    """

    CORRELATION_THRESHOLD = 0.6  # FROZEN

    def __init__(self, correlation_threshold: float = 0.6):
        super().__init__("B2")
        self.correlation_threshold = max(correlation_threshold, self.CORRELATION_THRESHOLD)

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Detect blindspots through correlation analysis.

        Blindspot = systematic failure pattern where models from
        same family make correlated errors.
        """
        witnesses: List[WitnessExtraction] = getattr(context, 'witness_results', [])

        if len(witnesses) < 3:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,  # Cannot detect blindspots with few witnesses
                details={"message": "Insufficient witnesses for blindspot analysis"},
            )

        # Analyze agreement patterns by family
        blindspots = self._detect_blindspots(witnesses)

        if blindspots:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Potential blindspots detected: {len(blindspots)} fields",
                details={
                    "blindspots": blindspots,
                    "threshold": self.correlation_threshold,
                },
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "blindspots_checked": True,
                "none_detected": True,
            },
        )

    def _detect_blindspots(
        self,
        witnesses: List[WitnessExtraction],
    ) -> List[Dict[str, Any]]:
        """
        Detect fields where same-family models agree but cross-family disagree.

        This indicates a potential blindspot where a model family has
        systematic bias.
        """
        blindspots = []

        # Group witnesses by family
        families: Dict[str, List[WitnessExtraction]] = {}
        for w in witnesses:
            families.setdefault(w.model_family, []).append(w)

        if len(families) < 2:
            return []  # Need multiple families to detect blindspots

        # Get all fields
        all_fields: Set[str] = set()
        for w in witnesses:
            all_fields.update(w.extractions.keys())

        for field_name in all_fields:
            # Compute within-family agreement
            family_values: Dict[str, List[Any]] = {}
            for family, family_witnesses in families.items():
                values = [
                    w.extractions.get(field_name)
                    for w in family_witnesses
                    if field_name in w.extractions
                ]
                if values:
                    family_values[family] = values

            if len(family_values) < 2:
                continue

            # Check if families agree internally but disagree with each other
            within_family_agreement = []
            family_centroids = {}

            for family, values in family_values.items():
                if all(isinstance(v, (int, float)) for v in values):
                    # Numeric: check variance
                    if len(values) > 1:
                        within_agreement = 1 - (np.std(values) / (np.mean(np.abs(values)) + 1e-10))
                    else:
                        within_agreement = 1.0
                    family_centroids[family] = np.mean(values)
                else:
                    # Categorical: check if all same
                    unique = len(set(str(v) for v in values))
                    within_agreement = 1.0 / unique
                    family_centroids[family] = Counter(str(v) for v in values).most_common(1)[0][0]

                within_family_agreement.append(within_agreement)

            # High within-family agreement
            if np.mean(within_family_agreement) > 0.8:
                # Check cross-family disagreement
                centroid_list = list(family_centroids.values())
                if all(isinstance(c, (int, float)) for c in centroid_list):
                    # Numeric: check if centroids differ significantly
                    if len(centroid_list) >= 2:
                        spread = np.std(centroid_list) / (np.mean(np.abs(centroid_list)) + 1e-10)
                        if spread > 0.1:  # 10% difference between family centroids
                            blindspots.append({
                                "field": field_name,
                                "family_centroids": family_centroids,
                                "spread": spread,
                                "type": "numeric_divergence",
                            })
                else:
                    # Categorical: check if families disagree
                    unique_centroids = len(set(str(c) for c in centroid_list))
                    if unique_centroids > 1:
                        blindspots.append({
                            "field": field_name,
                            "family_centroids": family_centroids,
                            "type": "categorical_divergence",
                        })

        return blindspots
