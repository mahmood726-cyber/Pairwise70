"""
Tests for TruthCert core primitives.

Tests verify FROZEN invariants are correctly implemented.
"""

import pytest
from datetime import datetime

from truthcert.core.primitives import (
    ScopeLock,
    PolicyAnchor,
    CleanState,
    TerminalState,
    GateOutcome,
    Thresholds,
    WitnessConfig,
    CostBudget,
    FeatureFlags,
    PromotionPolicy,
    PROMOTION_RATES,
)


class TestScopeLock:
    """Test ScopeLock frozen dataclass."""

    def test_scope_lock_creation(self):
        """Test creating a scope lock."""
        scope = ScopeLock(
            endpoint="overall survival",
            entities=("treatment", "placebo"),
            units="months",
            timepoint="12 months",
            inclusion_snippet="randomized controlled trial",
            source_hash="abc123",
        )

        assert scope.endpoint == "overall survival"
        assert scope.entities == ("treatment", "placebo")
        assert scope.units == "months"
        assert scope.timepoint == "12 months"

    def test_scope_lock_is_frozen(self):
        """Test that scope lock is immutable."""
        scope = ScopeLock(
            endpoint="pfs",
            entities=("drug_a", "drug_b"),
            units="days",
            timepoint="6 months",
            inclusion_snippet="",
            source_hash="xyz789",
        )

        with pytest.raises(AttributeError):
            scope.endpoint = "os"  # Should fail - frozen

    def test_scope_lock_hash_equality(self):
        """Test scope locks with same values are equal."""
        scope1 = ScopeLock(
            endpoint="os",
            entities=("a", "b"),
            units="m",
            timepoint="12m",
            inclusion_snippet="",
            source_hash="h1",
        )
        scope2 = ScopeLock(
            endpoint="os",
            entities=("a", "b"),
            units="m",
            timepoint="12m",
            inclusion_snippet="",
            source_hash="h1",
        )

        assert scope1 == scope2
        assert hash(scope1) == hash(scope2)


class TestTerminalState:
    """Test terminal states - FROZEN values."""

    def test_terminal_states_exist(self):
        """Test all required terminal states exist."""
        assert TerminalState.DRAFT.value == "DRAFT"
        assert TerminalState.SHIPPED.value == "SHIPPED"
        assert TerminalState.REJECTED.value == "REJECTED"

    def test_only_three_states(self):
        """Test that only three terminal states exist (FROZEN)."""
        assert len(TerminalState) == 3


class TestThresholds:
    """Test threshold values - FROZEN."""

    def test_default_thresholds(self):
        """Test default threshold values match spec."""
        thresholds = Thresholds()

        # FROZEN values from spec
        assert thresholds.numeric_tolerance == 0.005
        assert thresholds.agreement_majority == 0.80
        assert thresholds.agreement_strong == 0.70
        assert thresholds.blindspot_correlation == 0.6
        assert thresholds.parser_material_threshold == 0.05

    def test_thresholds_frozen(self):
        """Test thresholds dataclass is frozen."""
        thresholds = Thresholds()

        with pytest.raises(AttributeError):
            thresholds.agreement_majority = 0.5  # Should fail


class TestPromotionRates:
    """Test promotion rates - FROZEN."""

    def test_promotion_rates(self):
        """Test FROZEN promotion rates."""
        # These are FROZEN values
        assert PROMOTION_RATES["shadow_to_active"] == 0.85
        assert PROMOTION_RATES["active_to_deprecated"] == 0.95


class TestWitnessConfig:
    """Test witness configuration."""

    def test_default_config(self):
        """Test default witness config."""
        config = WitnessConfig()

        assert config.min_witnesses == 3  # Minimum per spec
        assert config.max_witnesses == 5
        assert config.require_heterogeneity == True  # REQUIRED

    def test_config_frozen(self):
        """Test config is frozen."""
        config = WitnessConfig()

        with pytest.raises(AttributeError):
            config.min_witnesses = 1  # Should fail


class TestPolicyAnchor:
    """Test PolicyAnchor immutability."""

    def test_policy_anchor_creation(self):
        """Test creating a policy anchor."""
        policy = PolicyAnchor(
            scope_lock_ref="scope_001",
            validator_version="3.1.0",
            timestamp=datetime.utcnow(),
            thresholds=Thresholds(),
            witness_config=WitnessConfig(),
            cost_budget=CostBudget(),
            features=FeatureFlags(),
            promotion_policy=PromotionPolicy.SHADOW_FIRST,
        )

        assert policy.scope_lock_ref == "scope_001"
        assert policy.validator_version == "3.1.0"

    def test_policy_anchor_frozen(self):
        """Test policy anchor is immutable."""
        policy = PolicyAnchor(
            scope_lock_ref="ref",
            validator_version="1.0",
            timestamp=datetime.utcnow(),
            thresholds=Thresholds(),
            witness_config=WitnessConfig(),
            cost_budget=CostBudget(),
            features=FeatureFlags(),
            promotion_policy=PromotionPolicy.SHADOW_FIRST,
        )

        with pytest.raises(AttributeError):
            policy.validator_version = "2.0"  # Should fail


class TestCleanState:
    """Test CleanState initialization."""

    def test_clean_state_default(self):
        """Test CleanState starts empty."""
        state = CleanState()

        assert len(state.extracted_values) == 0
        assert len(state.witness_outputs) == 0
        assert state.consensus is None
        assert state.terminal_state == TerminalState.DRAFT

    def test_clean_state_mutable(self):
        """Test CleanState can be updated."""
        state = CleanState()
        state.extracted_values["hr"] = 0.85
        state.terminal_state = TerminalState.SHIPPED

        assert state.extracted_values["hr"] == 0.85
        assert state.terminal_state == TerminalState.SHIPPED


class TestGateOutcome:
    """Test GateOutcome structure."""

    def test_passing_gate(self):
        """Test a passing gate outcome."""
        outcome = GateOutcome(
            gate_id="B1",
            passed=True,
            details={"witness_count": 3},
        )

        assert outcome.gate_id == "B1"
        assert outcome.passed == True
        assert outcome.failure_reason is None

    def test_failing_gate(self):
        """Test a failing gate outcome."""
        outcome = GateOutcome(
            gate_id="B3",
            passed=False,
            failure_reason="CI does not contain point estimate",
            details={"point": 0.5, "ci": [0.6, 0.8]},
        )

        assert outcome.passed == False
        assert "CI does not contain" in outcome.failure_reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
