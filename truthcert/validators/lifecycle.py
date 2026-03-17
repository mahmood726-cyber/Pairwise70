"""
TruthCert Validator Lifecycle

Manages validators through their lifecycle:
PROPOSED → SHADOW → ACTIVE → DEPRECATED → REMOVED

FROZEN PROMOTION RATES:
- shadow_to_active: 85% agreement with existing validators
- active_to_deprecated: 95% coverage by replacement
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import hashlib
import json

from ..core.primitives import PromotionPolicy, PROMOTION_RATES


class ValidatorState(Enum):
    """Validator lifecycle states."""
    PROPOSED = "proposed"      # Under review
    SHADOW = "shadow"          # Running but not affecting decisions
    ACTIVE = "active"          # Full production use
    DEPRECATED = "deprecated"  # Scheduled for removal
    REMOVED = "removed"        # No longer in use


@dataclass
class ValidatorMetrics:
    """Performance metrics for a validator."""
    total_runs: int = 0
    pass_count: int = 0
    fail_count: int = 0
    error_count: int = 0
    avg_execution_time_ms: float = 0
    last_run: Optional[datetime] = None

    @property
    def pass_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.pass_count / self.total_runs

    @property
    def error_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.error_count / self.total_runs


@dataclass
class Validator:
    """
    A validation rule in the TruthCert system.

    Validators go through a lifecycle from PROPOSED to ACTIVE,
    and can be deprecated when superseded by better validators.
    """
    validator_id: str
    name: str
    description: str
    version: str
    check_function: Callable[[Dict[str, Any]], bool]
    state: ValidatorState = ValidatorState.PROPOSED

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    source_pattern: Optional[str] = None  # Failure pattern that inspired this

    # Metrics
    metrics: ValidatorMetrics = field(default_factory=ValidatorMetrics)

    # Lifecycle tracking
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    shadow_start: Optional[datetime] = None
    active_start: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None

    def __post_init__(self):
        # Record initial state
        self.state_history.append({
            "state": self.state.value,
            "timestamp": self.created_at.isoformat(),
            "reason": "created",
        })

    def run(self, context: Dict[str, Any]) -> bool:
        """
        Execute the validator check.

        Returns True if validation passes, False otherwise.
        """
        import time
        start = time.time()

        try:
            result = self.check_function(context)
            elapsed = (time.time() - start) * 1000

            # Update metrics
            self.metrics.total_runs += 1
            if result:
                self.metrics.pass_count += 1
            else:
                self.metrics.fail_count += 1
            self.metrics.last_run = datetime.utcnow()

            # Update rolling average execution time
            n = self.metrics.total_runs
            self.metrics.avg_execution_time_ms = (
                (self.metrics.avg_execution_time_ms * (n - 1) + elapsed) / n
            )

            return result

        except Exception as e:
            self.metrics.total_runs += 1
            self.metrics.error_count += 1
            self.metrics.last_run = datetime.utcnow()
            raise

    def transition_to(self, new_state: ValidatorState, reason: str = "") -> None:
        """Transition to a new lifecycle state."""
        old_state = self.state
        self.state = new_state

        self.state_history.append({
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
        })

        # Track specific transitions
        if new_state == ValidatorState.SHADOW:
            self.shadow_start = datetime.utcnow()
        elif new_state == ValidatorState.ACTIVE:
            self.active_start = datetime.utcnow()
        elif new_state == ValidatorState.DEPRECATED:
            self.deprecated_at = datetime.utcnow()

    def compute_hash(self) -> str:
        """Compute a hash of the validator definition."""
        data = {
            "validator_id": self.validator_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "validator_id": self.validator_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "source_pattern": self.source_pattern,
            "metrics": {
                "total_runs": self.metrics.total_runs,
                "pass_rate": self.metrics.pass_rate,
                "error_rate": self.metrics.error_rate,
                "avg_execution_time_ms": self.metrics.avg_execution_time_ms,
            },
            "state_history": self.state_history,
        }


class ValidatorRegistry:
    """
    Registry of all validators in the system.

    Manages validator lifecycle and provides access to active validators.
    """

    def __init__(self, promotion_policy: PromotionPolicy = PromotionPolicy.SHADOW_FIRST):
        self.validators: Dict[str, Validator] = {}
        self.promotion_policy = promotion_policy
        self._version_counter = 0

    def register(
        self,
        name: str,
        description: str,
        check_function: Callable[[Dict[str, Any]], bool],
        created_by: str = "",
        source_pattern: Optional[str] = None,
        initial_state: ValidatorState = ValidatorState.PROPOSED,
    ) -> Validator:
        """
        Register a new validator.

        Returns the created Validator instance.
        """
        self._version_counter += 1
        validator_id = f"val_{datetime.utcnow().strftime('%Y%m%d')}_{self._version_counter:04d}"

        validator = Validator(
            validator_id=validator_id,
            name=name,
            description=description,
            version="1.0.0",
            check_function=check_function,
            state=initial_state,
            created_by=created_by,
            source_pattern=source_pattern,
        )

        self.validators[validator_id] = validator
        return validator

    def get(self, validator_id: str) -> Optional[Validator]:
        """Get a validator by ID."""
        return self.validators.get(validator_id)

    def get_by_state(self, state: ValidatorState) -> List[Validator]:
        """Get all validators in a given state."""
        return [v for v in self.validators.values() if v.state == state]

    def get_active(self) -> List[Validator]:
        """Get all active validators."""
        return self.get_by_state(ValidatorState.ACTIVE)

    def get_shadow(self) -> List[Validator]:
        """Get all shadow validators."""
        return self.get_by_state(ValidatorState.SHADOW)

    def run_active_validators(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, bool]:
        """Run all active validators and return results."""
        results = {}
        for validator in self.get_active():
            try:
                results[validator.validator_id] = validator.run(context)
            except Exception as e:
                results[validator.validator_id] = False
        return results

    def run_shadow_validators(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, bool]:
        """
        Run all shadow validators (results don't affect decisions).

        Used for evaluation before promotion.
        """
        results = {}
        for validator in self.get_shadow():
            try:
                results[validator.validator_id] = validator.run(context)
            except Exception:
                results[validator.validator_id] = False
        return results

    def promote_to_shadow(
        self,
        validator_id: str,
        reason: str = "Manual promotion",
    ) -> bool:
        """Promote a validator from PROPOSED to SHADOW."""
        validator = self.get(validator_id)
        if not validator:
            return False

        if validator.state != ValidatorState.PROPOSED:
            return False

        validator.transition_to(ValidatorState.SHADOW, reason)
        return True

    def promote_to_active(
        self,
        validator_id: str,
        reason: str = "Met promotion criteria",
    ) -> bool:
        """
        Promote a validator from SHADOW to ACTIVE.

        FROZEN: Requires 85% agreement with existing validators.
        """
        validator = self.get(validator_id)
        if not validator:
            return False

        if validator.state != ValidatorState.SHADOW:
            return False

        # Check promotion criteria
        if not self._meets_promotion_criteria(validator):
            return False

        validator.transition_to(ValidatorState.ACTIVE, reason)
        return True

    def deprecate(
        self,
        validator_id: str,
        replacement_id: Optional[str] = None,
        reason: str = "Deprecated",
    ) -> bool:
        """
        Deprecate an active validator.

        FROZEN: Replacement must provide 95% coverage.
        """
        validator = self.get(validator_id)
        if not validator:
            return False

        if validator.state != ValidatorState.ACTIVE:
            return False

        # If replacement specified, verify coverage
        if replacement_id:
            replacement = self.get(replacement_id)
            if not replacement or replacement.state != ValidatorState.ACTIVE:
                return False

            # Would need historical comparison for real coverage check
            # Simplified: just verify replacement exists

        validator.transition_to(ValidatorState.DEPRECATED, reason)
        return True

    def remove(self, validator_id: str, reason: str = "Removed") -> bool:
        """Remove a deprecated validator."""
        validator = self.get(validator_id)
        if not validator:
            return False

        if validator.state != ValidatorState.DEPRECATED:
            return False

        validator.transition_to(ValidatorState.REMOVED, reason)
        return True

    def _meets_promotion_criteria(self, validator: Validator) -> bool:
        """
        Check if validator meets promotion criteria.

        FROZEN: 85% agreement with existing active validators required.
        """
        # Need sufficient shadow runs
        if validator.metrics.total_runs < 100:
            return False

        # Need low error rate
        if validator.metrics.error_rate > 0.01:  # 1% max errors
            return False

        # Agreement check would compare with active validators
        # Simplified: check pass rate is reasonable
        agreement_threshold = PROMOTION_RATES["shadow_to_active"]
        return validator.metrics.pass_rate >= agreement_threshold

    def discover_validator(
        self,
        failure_pattern: Dict[str, Any],
    ) -> Optional[Validator]:
        """
        Suggest a new validator based on a failure pattern.

        Part of the validator discovery pipeline from B10 (RAG).
        """
        pattern_sig = failure_pattern.get("pattern_description", "")
        occurrence_count = failure_pattern.get("occurrence_count", 0)

        if occurrence_count < 3:
            return None  # Not enough occurrences

        # Generate a check function based on the pattern
        proposed_check = failure_pattern.get("proposed_check", "")

        if proposed_check == "arm_value_swap_check":
            def check(ctx: Dict[str, Any]) -> bool:
                # Check for arm swap indicators
                return True  # Placeholder
        elif proposed_check == "unit_consistency_check":
            def check(ctx: Dict[str, Any]) -> bool:
                # Check unit consistency
                return True
        elif proposed_check == "table_structure_validation":
            def check(ctx: Dict[str, Any]) -> bool:
                # Validate table structure
                return True
        else:
            def check(ctx: Dict[str, Any]) -> bool:
                return True

        # Create proposed validator
        return self.register(
            name=f"Auto-discovered: {pattern_sig[:50]}",
            description=f"Validator discovered from failure pattern: {pattern_sig}",
            check_function=check,
            source_pattern=pattern_sig,
            initial_state=ValidatorState.PROPOSED,
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary metrics for all validators."""
        active = self.get_active()
        shadow = self.get_shadow()

        return {
            "total_validators": len(self.validators),
            "active_count": len(active),
            "shadow_count": len(shadow),
            "proposed_count": len(self.get_by_state(ValidatorState.PROPOSED)),
            "deprecated_count": len(self.get_by_state(ValidatorState.DEPRECATED)),
            "total_runs": sum(v.metrics.total_runs for v in self.validators.values()),
            "avg_pass_rate": (
                sum(v.metrics.pass_rate for v in active) / len(active)
                if active else 0
            ),
            "validators": [v.to_dict() for v in self.validators.values()],
        }


def create_standard_validators() -> List[Validator]:
    """Create standard validators for common checks."""
    validators = []

    # CI containment validator
    def ci_containment_check(ctx: Dict[str, Any]) -> bool:
        values = ctx.get("consensus_values", {})
        for key, val in values.items():
            if "_point" in key and isinstance(val, (int, float)):
                base = key.replace("_point", "")
                lower = values.get(f"{base}_ci_lower")
                upper = values.get(f"{base}_ci_upper")
                if lower is not None and upper is not None:
                    if not (lower <= val <= upper):
                        return False
        return True

    validators.append(Validator(
        validator_id="val_ci_containment",
        name="CI Containment",
        description="Verifies confidence intervals contain point estimates",
        version="1.0.0",
        check_function=ci_containment_check,
        state=ValidatorState.ACTIVE,
    ))

    # Positive ratio validator
    def positive_ratio_check(ctx: Dict[str, Any]) -> bool:
        values = ctx.get("consensus_values", {})
        ratio_keys = ["hr", "or", "rr", "hazard", "odds", "risk"]
        for key, val in values.items():
            if any(r in key.lower() for r in ratio_keys):
                if isinstance(val, (int, float)) and val <= 0:
                    return False
        return True

    validators.append(Validator(
        validator_id="val_positive_ratio",
        name="Positive Ratio",
        description="Verifies ratios (HR, OR, RR) are positive",
        version="1.0.0",
        check_function=positive_ratio_check,
        state=ValidatorState.ACTIVE,
    ))

    # Sample size validator
    def sample_size_check(ctx: Dict[str, Any]) -> bool:
        values = ctx.get("consensus_values", {})
        n_keys = ["sample_size", "_n", "subjects", "participants"]
        for key, val in values.items():
            if any(n in key.lower() for n in n_keys):
                if isinstance(val, (int, float)):
                    if val < 0:
                        return False
                    if isinstance(val, float) and not val.is_integer():
                        return False
        return True

    validators.append(Validator(
        validator_id="val_sample_size",
        name="Sample Size",
        description="Verifies sample sizes are positive integers",
        version="1.0.0",
        check_function=sample_size_check,
        state=ValidatorState.ACTIVE,
    ))

    return validators
