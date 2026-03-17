"""
Tests for TruthCert verification gates.

Tests verify gate logic and FROZEN invariants.
"""

import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Any

from truthcert.gates.witness_gates import (
    WitnessGate,
    HeterogeneityGate,
    BlindspotGate,
    WitnessExtraction,
)
from truthcert.gates.validation_gates import (
    StructuralGate,
    AntiMixingGate,
    SemanticGate,
)
from truthcert.gates.decision_gates import (
    AdversarialGate,
    TerminalGate,
)
from truthcert.core.primitives import ScopeLock, GateOutcome, TerminalState


@dataclass
class MockContext:
    """Mock verification context for testing."""
    witness_results: List[WitnessExtraction] = field(default_factory=list)
    consensus_values: Dict[str, Any] = field(default_factory=dict)
    gate_outcomes: Dict[str, GateOutcome] = field(default_factory=dict)
    scope_lock: ScopeLock = None


class TestWitnessGate:
    """Test B1 - Witness Agreement Gate."""

    def test_frozen_thresholds(self):
        """Test FROZEN agreement thresholds."""
        gate = WitnessGate()

        # These are FROZEN values
        assert gate.AGREEMENT_MAJORITY == 0.80
        assert gate.AGREEMENT_STRONG == 0.70
        assert gate.MIN_WITNESSES == 3

    def test_insufficient_witnesses(self):
        """Test failure when too few witnesses."""
        gate = WitnessGate(min_witnesses=3)
        context = MockContext(witness_results=[
            WitnessExtraction(
                witness_id="w1",
                model_name="gpt-4",
                model_family="openai",
                extractions={"hr": 0.85},
                confidence_scores={"hr": 0.9},
                tokens_used=1000,
                cost_usd=0.03,
            ),
        ])

        outcome = gate.evaluate(context)

        assert outcome.passed == False
        assert "Insufficient witnesses" in outcome.failure_reason

    def test_sufficient_agreement(self):
        """Test passing with sufficient agreement."""
        gate = WitnessGate(min_witnesses=3, numeric_tolerance=0.01)

        # Create witnesses that agree
        witnesses = [
            WitnessExtraction(
                witness_id=f"w{i}",
                model_name="gpt-4",
                model_family="openai",
                extractions={"hr": 0.85 + 0.001 * i},  # Within tolerance
                confidence_scores={"hr": 0.9},
                tokens_used=1000,
                cost_usd=0.03,
            )
            for i in range(3)
        ]

        context = MockContext(witness_results=witnesses)
        outcome = gate.evaluate(context)

        assert outcome.passed == True


class TestHeterogeneityGate:
    """Test B1.5 - Model Heterogeneity Gate."""

    def test_frozen_min_families(self):
        """Test FROZEN minimum families requirement."""
        gate = HeterogeneityGate()
        assert gate.MIN_FAMILIES == 2

    def test_insufficient_heterogeneity(self):
        """Test failure with single model family."""
        gate = HeterogeneityGate()

        # All same family
        witnesses = [
            WitnessExtraction(
                witness_id=f"w{i}",
                model_name="gpt-4",
                model_family="openai",  # All OpenAI
                extractions={},
                confidence_scores={},
                tokens_used=1000,
                cost_usd=0.03,
            )
            for i in range(3)
        ]

        context = MockContext(witness_results=witnesses)
        outcome = gate.evaluate(context)

        assert outcome.passed == False
        assert "model diversity" in outcome.failure_reason.lower()

    def test_sufficient_heterogeneity(self):
        """Test passing with multiple model families."""
        gate = HeterogeneityGate()

        witnesses = [
            WitnessExtraction(
                witness_id="w1",
                model_name="gpt-4",
                model_family="openai",
                extractions={},
                confidence_scores={},
                tokens_used=1000,
                cost_usd=0.03,
            ),
            WitnessExtraction(
                witness_id="w2",
                model_name="claude-3",
                model_family="anthropic",  # Different family
                extractions={},
                confidence_scores={},
                tokens_used=1000,
                cost_usd=0.03,
            ),
        ]

        context = MockContext(witness_results=witnesses)
        outcome = gate.evaluate(context)

        assert outcome.passed == True


class TestStructuralGate:
    """Test B3 - Structural Validation Gate."""

    def test_ci_containment_pass(self):
        """Test CI containment check passes."""
        gate = StructuralGate()

        context = MockContext(consensus_values={
            "hr_point": 0.85,
            "hr_ci_lower": 0.72,
            "hr_ci_upper": 0.99,
        })

        outcome = gate.evaluate(context)
        assert outcome.passed == True

    def test_ci_containment_fail(self):
        """Test CI containment check fails."""
        gate = StructuralGate()

        context = MockContext(consensus_values={
            "hr_point": 0.60,  # Outside CI
            "hr_ci_lower": 0.72,
            "hr_ci_upper": 0.99,
        })

        outcome = gate.evaluate(context)
        assert outcome.passed == False

    def test_negative_sample_size(self):
        """Test negative sample size is rejected."""
        gate = StructuralGate()

        context = MockContext(consensus_values={
            "sample_size": -10,
        })

        outcome = gate.evaluate(context)
        assert outcome.passed == False

    def test_positive_ratio_validation(self):
        """Test that ratios must be positive."""
        gate = StructuralGate()

        context = MockContext(consensus_values={
            "hr": -0.5,  # Hazard ratio can't be negative
        })

        outcome = gate.evaluate(context)
        assert outcome.passed == False


class TestAntiMixingGate:
    """Test B4 - Anti-Mixing Gate."""

    def test_no_mixing_detected(self):
        """Test gate passes when no mixing detected."""
        gate = AntiMixingGate()

        scope = ScopeLock(
            endpoint="os",
            entities=("treatment", "control"),
            units="months",
            timepoint="12m",
            inclusion_snippet="",
            source_hash="h1",
        )

        context = MockContext(
            consensus_values={
                "treatment_events": 50,
                "control_events": 75,
            },
            scope_lock=scope,
        )

        outcome = gate.evaluate(context)
        assert outcome.passed == True


class TestAdversarialGate:
    """Test B8 - Adversarial Gate."""

    def test_requires_multiple_families(self):
        """Test adversarial gate requires multiple model families."""
        gate = AdversarialGate(require_different_family=True)

        # Single family
        witnesses = [
            WitnessExtraction(
                witness_id=f"w{i}",
                model_name="gpt-4",
                model_family="openai",
                extractions={"hr": 0.85},
                confidence_scores={},
                tokens_used=1000,
                cost_usd=0.03,
            )
            for i in range(3)
        ]

        context = MockContext(witness_results=witnesses)
        outcome = gate.evaluate(context)

        assert outcome.passed == False


class TestTerminalGate:
    """Test B9 - Terminal State Decision Gate."""

    def test_all_pass_ships(self):
        """Test that all gates passing leads to SHIPPED."""
        gate = TerminalGate()

        context = MockContext(gate_outcomes={
            "B1": GateOutcome(gate_id="B1", passed=True),
            "B1.5": GateOutcome(gate_id="B1.5", passed=True),
            "B3": GateOutcome(gate_id="B3", passed=True),
        })

        outcome = gate.evaluate(context)
        assert outcome.passed == True
        assert outcome.details["terminal_state"] == TerminalState.SHIPPED.value

    def test_failure_rejects(self):
        """Test that any critical gate failure leads to REJECTED."""
        gate = TerminalGate(critical_gates=["B1", "B3"])

        context = MockContext(gate_outcomes={
            "B1": GateOutcome(gate_id="B1", passed=True),
            "B3": GateOutcome(
                gate_id="B3",
                passed=False,
                failure_reason="CI violation",
            ),
        })

        outcome = gate.evaluate(context)
        assert outcome.passed == False
        assert outcome.details["terminal_state"] == TerminalState.REJECTED.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
