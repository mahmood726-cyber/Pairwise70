"""
TruthCert Decision Gates (B6, B7, B8, B9)

B6: Human escalation decision
B7: Gold standard comparison
B8: Adversarial cross-family testing
B9: Terminal state decision
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Callable
from abc import ABC
import hashlib

from ..core.primitives import GateOutcome, TerminalState
from .witness_gates import BaseGate, WitnessExtraction


class EscalationGate(BaseGate):
    """
    Gate B6 - Human Escalation

    Determines if human review is required based on:
    - Low confidence scores
    - Ambiguous extractions
    - Novel document structures
    - High-stakes endpoints
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        ambiguity_threshold: float = 0.3,
        auto_escalate_endpoints: Optional[List[str]] = None,
    ):
        super().__init__("B6")
        self.confidence_threshold = confidence_threshold
        self.ambiguity_threshold = ambiguity_threshold
        self.auto_escalate_endpoints = auto_escalate_endpoints or [
            "mortality", "death", "survival", "safety", "adverse"
        ]

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Determine if human escalation is required.
        """
        witnesses: List[WitnessExtraction] = getattr(context, 'witness_results', [])
        scope_lock = getattr(context, 'scope_lock', None)
        consensus = getattr(context, 'consensus_values', {})

        escalation_reasons = []

        # Check confidence scores
        low_confidence_fields = self._check_confidence(witnesses)
        if low_confidence_fields:
            escalation_reasons.append({
                "type": "low_confidence",
                "fields": low_confidence_fields,
            })

        # Check for ambiguous extractions
        ambiguous_fields = self._check_ambiguity(witnesses)
        if ambiguous_fields:
            escalation_reasons.append({
                "type": "ambiguous_extraction",
                "fields": ambiguous_fields,
            })

        # Check for high-stakes endpoints
        if scope_lock and self._is_high_stakes_endpoint(scope_lock.endpoint):
            escalation_reasons.append({
                "type": "high_stakes_endpoint",
                "endpoint": scope_lock.endpoint,
            })

        # Check for sparse extractions
        if len(consensus) < 3:
            escalation_reasons.append({
                "type": "sparse_extraction",
                "field_count": len(consensus),
            })

        if escalation_reasons:
            # Escalation is an informational gate - doesn't fail verification
            # but marks for human review
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,  # Gate passes but flags for review
                details={
                    "escalation_required": True,
                    "reasons": escalation_reasons,
                },
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={"escalation_required": False},
        )

    def _check_confidence(
        self,
        witnesses: List[WitnessExtraction],
    ) -> List[Dict[str, Any]]:
        """Find fields with low confidence scores."""
        low_confidence = []

        # Aggregate confidence by field
        field_confidences: Dict[str, List[float]] = {}
        for w in witnesses:
            for field, conf in w.confidence_scores.items():
                field_confidences.setdefault(field, []).append(conf)

        for field, scores in field_confidences.items():
            avg_conf = sum(scores) / len(scores)
            if avg_conf < self.confidence_threshold:
                low_confidence.append({
                    "field": field,
                    "avg_confidence": avg_conf,
                    "threshold": self.confidence_threshold,
                })

        return low_confidence

    def _check_ambiguity(
        self,
        witnesses: List[WitnessExtraction],
    ) -> List[Dict[str, Any]]:
        """Find fields with ambiguous extractions."""
        ambiguous = []

        # Get all fields
        all_fields: Set[str] = set()
        for w in witnesses:
            all_fields.update(w.extractions.keys())

        for field in all_fields:
            values = [
                w.extractions[field]
                for w in witnesses
                if field in w.extractions
            ]

            if len(values) < 2:
                continue

            # Check variance for numeric values
            if all(isinstance(v, (int, float)) for v in values):
                mean_val = sum(values) / len(values)
                if mean_val != 0:
                    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
                    cv = (variance ** 0.5) / abs(mean_val)

                    if cv > self.ambiguity_threshold:
                        ambiguous.append({
                            "field": field,
                            "coefficient_of_variation": cv,
                            "values": values,
                        })
            else:
                # Categorical - check disagreement rate
                unique_values = len(set(str(v) for v in values))
                disagreement_rate = (unique_values - 1) / len(values)

                if disagreement_rate > self.ambiguity_threshold:
                    ambiguous.append({
                        "field": field,
                        "disagreement_rate": disagreement_rate,
                        "values": [str(v) for v in values],
                    })

        return ambiguous

    def _is_high_stakes_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint is high-stakes requiring review."""
        endpoint_lower = endpoint.lower()
        return any(term in endpoint_lower for term in self.auto_escalate_endpoints)


class GoldStandardGate(BaseGate):
    """
    Gate B7 - Gold Standard Comparison

    Compares extractions against known gold standard when available.
    Used for validation against manually curated datasets.
    """

    def __init__(
        self,
        gold_standards: Optional[Dict[str, Dict[str, Any]]] = None,
        tolerance: float = 0.01,
    ):
        super().__init__("B7")
        self.gold_standards = gold_standards or {}
        self.tolerance = tolerance

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Compare extractions against gold standard if available.
        """
        consensus = getattr(context, 'consensus_values', {})
        scope_lock = getattr(context, 'scope_lock', None)

        if not scope_lock:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,
                details={"gold_standard_available": False},
            )

        # Look up gold standard by source hash
        gold_key = scope_lock.source_hash
        if gold_key not in self.gold_standards:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,
                details={"gold_standard_available": False},
            )

        gold = self.gold_standards[gold_key]
        discrepancies = []

        # Compare each field
        for field, expected in gold.items():
            if field not in consensus:
                discrepancies.append({
                    "field": field,
                    "expected": expected,
                    "extracted": None,
                    "type": "missing",
                })
                continue

            extracted = consensus[field]

            # Numeric comparison
            if isinstance(expected, (int, float)) and isinstance(extracted, (int, float)):
                if expected != 0:
                    pct_diff = abs(expected - extracted) / abs(expected)
                    if pct_diff > self.tolerance:
                        discrepancies.append({
                            "field": field,
                            "expected": expected,
                            "extracted": extracted,
                            "pct_difference": pct_diff,
                            "type": "numeric_mismatch",
                        })
            else:
                # String comparison
                if str(expected).lower() != str(extracted).lower():
                    discrepancies.append({
                        "field": field,
                        "expected": expected,
                        "extracted": extracted,
                        "type": "categorical_mismatch",
                    })

        if discrepancies:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Gold standard mismatch: {len(discrepancies)} discrepancies",
                details={
                    "gold_standard_available": True,
                    "discrepancies": discrepancies,
                },
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "gold_standard_available": True,
                "fields_validated": len(gold),
                "all_match": True,
            },
        )

    def register_gold_standard(
        self,
        source_hash: str,
        gold_values: Dict[str, Any],
    ) -> None:
        """Register a gold standard for a document."""
        self.gold_standards[source_hash] = gold_values


class AdversarialGate(BaseGate):
    """
    Gate B8 - Adversarial Cross-Family Testing

    FROZEN INVARIANT:
    - Must test with different model family than primary witnesses
    - Adversarial model acts as challenger
    - Disagreement triggers failure (fail-closed)
    """

    def __init__(
        self,
        adversarial_threshold: float = 0.05,
        require_different_family: bool = True,
    ):
        super().__init__("B8")
        self.adversarial_threshold = adversarial_threshold
        self.require_different_family = require_different_family

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Run adversarial cross-family validation.
        """
        witnesses: List[WitnessExtraction] = getattr(context, 'witness_results', [])
        consensus = getattr(context, 'consensus_values', {})

        if not witnesses:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason="No witnesses for adversarial testing",
            )

        # Identify model families used
        families = set(w.model_family for w in witnesses)

        if len(families) < 2:
            if self.require_different_family:
                return GateOutcome(
                    gate_id=self.gate_id,
                    passed=False,
                    failure_reason="Cannot run adversarial test: need multiple model families",
                    details={
                        "families": list(families),
                        "required_families": 2,
                    },
                )

        # Group witnesses by family
        family_groups: Dict[str, List[WitnessExtraction]] = {}
        for w in witnesses:
            family_groups.setdefault(w.model_family, []).append(w)

        # Compare consensus between families
        disagreements = self._find_cross_family_disagreements(family_groups, consensus)

        if disagreements:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Adversarial disagreement: {len(disagreements)} fields",
                details={
                    "disagreements": disagreements,
                    "families": list(families),
                },
            )

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "adversarial_test": "passed",
                "families_tested": list(families),
                "fields_validated": len(consensus),
            },
        )

    def _find_cross_family_disagreements(
        self,
        family_groups: Dict[str, List[WitnessExtraction]],
        consensus: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find disagreements between model families."""
        disagreements = []

        # Compute per-family consensus
        family_consensus: Dict[str, Dict[str, Any]] = {}
        for family, witnesses in family_groups.items():
            fc = {}
            all_fields: Set[str] = set()
            for w in witnesses:
                all_fields.update(w.extractions.keys())

            for field in all_fields:
                values = [
                    w.extractions[field]
                    for w in witnesses
                    if field in w.extractions
                ]
                if values:
                    if all(isinstance(v, (int, float)) for v in values):
                        fc[field] = sum(values) / len(values)
                    else:
                        # Most common
                        from collections import Counter
                        fc[field] = Counter(str(v) for v in values).most_common(1)[0][0]

            family_consensus[family] = fc

        # Compare families
        families = list(family_groups.keys())
        for i, f1 in enumerate(families):
            for f2 in families[i + 1:]:
                fc1 = family_consensus[f1]
                fc2 = family_consensus[f2]

                common_fields = set(fc1.keys()) & set(fc2.keys())

                for field in common_fields:
                    v1 = fc1[field]
                    v2 = fc2[field]

                    # Numeric comparison
                    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                        if v1 != 0:
                            pct_diff = abs(v1 - v2) / abs(v1)
                            if pct_diff > self.adversarial_threshold:
                                disagreements.append({
                                    "field": field,
                                    "family1": f1,
                                    "value1": v1,
                                    "family2": f2,
                                    "value2": v2,
                                    "pct_difference": pct_diff,
                                })
                    else:
                        # String comparison
                        if str(v1) != str(v2):
                            disagreements.append({
                                "field": field,
                                "family1": f1,
                                "value1": str(v1),
                                "family2": f2,
                                "value2": str(v2),
                            })

        return disagreements


class TerminalGate(BaseGate):
    """
    Gate B9 - Terminal State Decision

    Final decision gate that determines SHIPPED or REJECTED.

    FROZEN INVARIANT:
    - Any prior gate failure → REJECTED (fail-closed)
    - All gates pass → SHIPPED
    - No intermediate states allowed
    """

    def __init__(self, critical_gates: Optional[List[str]] = None):
        super().__init__("B9")
        self.critical_gates = critical_gates or [
            "B1", "B1.5", "B3", "B4", "B8"
        ]

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Make terminal SHIP/REJECT decision.
        """
        gate_outcomes: Dict[str, GateOutcome] = getattr(context, 'gate_outcomes', {})

        # Check all previous gates
        failed_gates = []
        for gate_id, outcome in gate_outcomes.items():
            if gate_id == self.gate_id:
                continue  # Skip self

            if not outcome.passed:
                failed_gates.append({
                    "gate_id": gate_id,
                    "reason": outcome.failure_reason,
                    "is_critical": gate_id in self.critical_gates,
                })

        # Determine terminal state
        critical_failures = [g for g in failed_gates if g["is_critical"]]

        if critical_failures:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Critical gate failures: {[g['gate_id'] for g in critical_failures]}",
                details={
                    "terminal_state": TerminalState.REJECTED.value,
                    "failed_gates": failed_gates,
                    "critical_failures": critical_failures,
                },
            )

        if failed_gates:
            # Non-critical failures - still reject but with different reason
            return GateOutcome(
                gate_id=self.gate_id,
                passed=False,
                failure_reason=f"Gate failures: {[g['gate_id'] for g in failed_gates]}",
                details={
                    "terminal_state": TerminalState.REJECTED.value,
                    "failed_gates": failed_gates,
                },
            )

        # All gates passed - SHIP
        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "terminal_state": TerminalState.SHIPPED.value,
                "all_gates_passed": True,
            },
        )

    def compute_terminal_state(self, context: Any) -> TerminalState:
        """Compute terminal state from context."""
        outcome = self.evaluate(context)
        if outcome.passed:
            return TerminalState.SHIPPED
        return TerminalState.REJECTED
