"""
TruthCert Validator Governance

Manages validator promotion decisions and policy enforcement.

FROZEN GOVERNANCE RULES:
- Promotion requires approval (manual or automatic based on metrics)
- Deprecation requires replacement coverage verification
- Version tracking is mandatory
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from ..core.primitives import PromotionPolicy, PROMOTION_RATES
from .lifecycle import Validator, ValidatorState, ValidatorRegistry


class PromotionDecision(Enum):
    """Promotion decision outcomes."""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"
    NEEDS_MORE_DATA = "needs_more_data"


@dataclass
class PromotionRequest:
    """Request to promote a validator."""
    validator_id: str
    requested_by: str
    requested_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[PromotionDecision] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_reason: str = ""


@dataclass
class DeprecationRequest:
    """Request to deprecate a validator."""
    validator_id: str
    replacement_id: Optional[str]
    requested_by: str
    requested_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    coverage_evidence: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[PromotionDecision] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None


class ValidatorGovernance:
    """
    Governance system for validator lifecycle management.

    Enforces FROZEN governance rules:
    - 85% agreement for shadow→active promotion
    - 95% coverage for deprecation with replacement
    - All transitions are logged and auditable
    """

    SHADOW_TO_ACTIVE_THRESHOLD = PROMOTION_RATES["shadow_to_active"]  # FROZEN: 0.85
    DEPRECATION_COVERAGE_THRESHOLD = PROMOTION_RATES["active_to_deprecated"]  # FROZEN: 0.95

    def __init__(
        self,
        registry: ValidatorRegistry,
        promotion_policy: PromotionPolicy = PromotionPolicy.SHADOW_FIRST,
    ):
        self.registry = registry
        self.promotion_policy = promotion_policy
        self.promotion_requests: List[PromotionRequest] = []
        self.deprecation_requests: List[DeprecationRequest] = []
        self.audit_log: List[Dict[str, Any]] = []

    def request_promotion(
        self,
        validator_id: str,
        requested_by: str,
        reason: str = "",
    ) -> PromotionRequest:
        """
        Request promotion for a validator.

        For SHADOW_FIRST policy:
        - PROPOSED → SHADOW: Requires review
        - SHADOW → ACTIVE: Requires 85% agreement threshold
        """
        validator = self.registry.get(validator_id)
        if not validator:
            raise ValueError(f"Validator not found: {validator_id}")

        # Build evidence
        evidence = self._gather_promotion_evidence(validator)

        request = PromotionRequest(
            validator_id=validator_id,
            requested_by=requested_by,
            reason=reason,
            evidence=evidence,
        )

        self.promotion_requests.append(request)
        self._log_event("promotion_requested", validator_id, requested_by, evidence)

        # Auto-evaluate if policy allows
        if self.promotion_policy == PromotionPolicy.AUTO:
            self._auto_evaluate_promotion(request)

        return request

    def request_deprecation(
        self,
        validator_id: str,
        requested_by: str,
        replacement_id: Optional[str] = None,
        reason: str = "",
    ) -> DeprecationRequest:
        """
        Request deprecation for a validator.

        FROZEN: Replacement must provide 95% coverage.
        """
        validator = self.registry.get(validator_id)
        if not validator:
            raise ValueError(f"Validator not found: {validator_id}")

        coverage_evidence = {}
        if replacement_id:
            coverage_evidence = self._gather_coverage_evidence(
                validator_id, replacement_id
            )

        request = DeprecationRequest(
            validator_id=validator_id,
            replacement_id=replacement_id,
            requested_by=requested_by,
            reason=reason,
            coverage_evidence=coverage_evidence,
        )

        self.deprecation_requests.append(request)
        self._log_event("deprecation_requested", validator_id, requested_by, coverage_evidence)

        return request

    def approve_promotion(
        self,
        request: PromotionRequest,
        approved_by: str,
        reason: str = "",
    ) -> bool:
        """Approve a promotion request."""
        validator = self.registry.get(request.validator_id)
        if not validator:
            return False

        # Determine target state
        if validator.state == ValidatorState.PROPOSED:
            target_state = ValidatorState.SHADOW
        elif validator.state == ValidatorState.SHADOW:
            target_state = ValidatorState.ACTIVE

            # Verify threshold is met
            agreement = request.evidence.get("agreement_rate", 0)
            if agreement < self.SHADOW_TO_ACTIVE_THRESHOLD:
                request.decision = PromotionDecision.REJECTED
                request.decision_reason = f"Agreement {agreement:.2%} < {self.SHADOW_TO_ACTIVE_THRESHOLD:.2%}"
                return False
        else:
            return False

        # Execute promotion
        validator.transition_to(target_state, reason or f"Approved by {approved_by}")

        request.decision = PromotionDecision.APPROVED
        request.decided_by = approved_by
        request.decided_at = datetime.utcnow()
        request.decision_reason = reason

        self._log_event(
            "promotion_approved",
            request.validator_id,
            approved_by,
            {"target_state": target_state.value},
        )

        return True

    def reject_promotion(
        self,
        request: PromotionRequest,
        rejected_by: str,
        reason: str,
    ) -> None:
        """Reject a promotion request."""
        request.decision = PromotionDecision.REJECTED
        request.decided_by = rejected_by
        request.decided_at = datetime.utcnow()
        request.decision_reason = reason

        self._log_event(
            "promotion_rejected",
            request.validator_id,
            rejected_by,
            {"reason": reason},
        )

    def approve_deprecation(
        self,
        request: DeprecationRequest,
        approved_by: str,
        reason: str = "",
    ) -> bool:
        """Approve a deprecation request."""
        validator = self.registry.get(request.validator_id)
        if not validator:
            return False

        # Verify coverage if replacement specified
        if request.replacement_id:
            coverage = request.coverage_evidence.get("coverage_rate", 0)
            if coverage < self.DEPRECATION_COVERAGE_THRESHOLD:
                request.decision = PromotionDecision.REJECTED
                request.decision_reason = f"Coverage {coverage:.2%} < {self.DEPRECATION_COVERAGE_THRESHOLD:.2%}"
                return False

        # Execute deprecation
        success = self.registry.deprecate(
            request.validator_id,
            request.replacement_id,
            reason or f"Deprecated by {approved_by}",
        )

        if success:
            request.decision = PromotionDecision.APPROVED
            request.decided_by = approved_by
            request.decided_at = datetime.utcnow()

            self._log_event(
                "deprecation_approved",
                request.validator_id,
                approved_by,
                {"replacement": request.replacement_id},
            )

        return success

    def _auto_evaluate_promotion(self, request: PromotionRequest) -> None:
        """Automatically evaluate a promotion request."""
        validator = self.registry.get(request.validator_id)
        if not validator:
            return

        if validator.state == ValidatorState.PROPOSED:
            # Auto-promote to shadow if basic criteria met
            if request.evidence.get("has_description", False):
                self.approve_promotion(request, "auto", "Auto-promoted to shadow")
            else:
                request.decision = PromotionDecision.NEEDS_MORE_DATA
                request.decision_reason = "Missing description"

        elif validator.state == ValidatorState.SHADOW:
            # Check agreement threshold
            agreement = request.evidence.get("agreement_rate", 0)
            runs = request.evidence.get("total_runs", 0)

            if runs < 100:
                request.decision = PromotionDecision.NEEDS_MORE_DATA
                request.decision_reason = f"Need 100+ runs, have {runs}"
            elif agreement >= self.SHADOW_TO_ACTIVE_THRESHOLD:
                self.approve_promotion(request, "auto", "Met agreement threshold")
            else:
                request.decision = PromotionDecision.REJECTED
                request.decision_reason = f"Agreement {agreement:.2%} below threshold"

    def _gather_promotion_evidence(self, validator: Validator) -> Dict[str, Any]:
        """Gather evidence for promotion evaluation."""
        evidence = {
            "validator_id": validator.validator_id,
            "current_state": validator.state.value,
            "total_runs": validator.metrics.total_runs,
            "pass_rate": validator.metrics.pass_rate,
            "error_rate": validator.metrics.error_rate,
            "has_description": bool(validator.description),
            "version": validator.version,
        }

        # For shadow→active, compute agreement with active validators
        if validator.state == ValidatorState.SHADOW:
            agreement = self._compute_agreement_with_active(validator)
            evidence["agreement_rate"] = agreement

        return evidence

    def _gather_coverage_evidence(
        self,
        old_id: str,
        new_id: str,
    ) -> Dict[str, Any]:
        """Gather coverage evidence for deprecation."""
        old_validator = self.registry.get(old_id)
        new_validator = self.registry.get(new_id)

        if not old_validator or not new_validator:
            return {"coverage_rate": 0}

        # Simplified coverage: compare pass rates
        # Real implementation would compare on historical data
        old_pass_rate = old_validator.metrics.pass_rate
        new_pass_rate = new_validator.metrics.pass_rate

        # Coverage = how much of old's passes are covered by new
        coverage = new_pass_rate / max(old_pass_rate, 0.01)

        return {
            "old_pass_rate": old_pass_rate,
            "new_pass_rate": new_pass_rate,
            "coverage_rate": min(1.0, coverage),
            "old_runs": old_validator.metrics.total_runs,
            "new_runs": new_validator.metrics.total_runs,
        }

    def _compute_agreement_with_active(self, validator: Validator) -> float:
        """Compute agreement rate with active validators."""
        # Simplified: use pass rate as proxy for agreement
        # Real implementation would compare on same test cases
        active_validators = self.registry.get_active()

        if not active_validators:
            return 1.0  # No active validators to disagree with

        # Compare pass rates
        active_avg_pass_rate = sum(
            v.metrics.pass_rate for v in active_validators
        ) / len(active_validators)

        # Agreement = how close this validator's pass rate is to active average
        diff = abs(validator.metrics.pass_rate - active_avg_pass_rate)
        agreement = 1.0 - min(1.0, diff * 2)  # Scale difference

        return agreement

    def _log_event(
        self,
        event_type: str,
        validator_id: str,
        actor: str,
        details: Dict[str, Any],
    ) -> None:
        """Log an audit event."""
        self.audit_log.append({
            "event_type": event_type,
            "validator_id": validator_id,
            "actor": actor,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        })

    def get_pending_requests(self) -> Dict[str, List]:
        """Get all pending requests."""
        pending_promotions = [
            r for r in self.promotion_requests
            if r.decision is None or r.decision == PromotionDecision.PENDING_REVIEW
        ]

        pending_deprecations = [
            r for r in self.deprecation_requests
            if r.decision is None or r.decision == PromotionDecision.PENDING_REVIEW
        ]

        return {
            "promotions": pending_promotions,
            "deprecations": pending_deprecations,
        }

    def get_audit_trail(
        self,
        validator_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit trail, optionally filtered by validator."""
        events = self.audit_log

        if validator_id:
            events = [e for e in events if e["validator_id"] == validator_id]

        return events[-limit:]

    def generate_governance_report(self) -> Dict[str, Any]:
        """Generate a governance status report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "registry_summary": self.registry.get_metrics_summary(),
            "pending_requests": {
                "promotions": len([r for r in self.promotion_requests if r.decision is None]),
                "deprecations": len([r for r in self.deprecation_requests if r.decision is None]),
            },
            "recent_decisions": [
                {
                    "type": "promotion",
                    "validator_id": r.validator_id,
                    "decision": r.decision.value if r.decision else None,
                    "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                }
                for r in self.promotion_requests[-10:]
                if r.decision
            ],
            "promotion_policy": self.promotion_policy.value,
            "thresholds": {
                "shadow_to_active": self.SHADOW_TO_ACTIVE_THRESHOLD,
                "deprecation_coverage": self.DEPRECATION_COVERAGE_THRESHOLD,
            },
            "audit_log_size": len(self.audit_log),
        }
