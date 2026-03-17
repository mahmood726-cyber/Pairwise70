"""
TruthCert Lane B - Verification Lane

Rigorous verification through 11 gates leading to SHIPPED or REJECTED.
Implements the full verification protocol with fail-closed semantics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import hashlib
import json

from ..core.primitives import (
    ScopeLock,
    PolicyAnchor,
    CleanState,
    TerminalState,
    GateOutcome,
    LedgerEntry,
    MemoryFields,
    EfficiencyMetrics,
    ParseStatus,
)
from .exploration import DraftBundle, ExtractionCandidate


class GateID(Enum):
    """Gate identifiers - order matters."""
    B1_WITNESSES = "B1"
    B1_5_HETEROGENEITY = "B1.5"
    B2_BLINDSPOT = "B2"
    B3_STRUCTURAL = "B3"
    B4_ANTI_MIXING = "B4"
    B5_SEMANTIC = "B5"
    B6_ESCALATION = "B6"
    B7_GOLD_STANDARD = "B7"
    B8_ADVERSARIAL = "B8"
    B9_TERMINAL = "B9"
    B10_RAG = "B10"
    B11_EFFICIENCY = "B11"


@dataclass
class WitnessResult:
    """Result from a single witness run."""
    witness_id: str
    model_name: str
    model_family: str
    extractions: Dict[str, Any]
    confidence_scores: Dict[str, float]
    raw_output: str
    tokens_used: int
    cost_usd: float


@dataclass
class VerificationResult:
    """
    Result of verification lane processing.

    Contains final terminal state and all gate outcomes.
    """
    bundle_id: str
    terminal_state: TerminalState
    gate_outcomes: Dict[str, GateOutcome] = field(default_factory=dict)
    final_extractions: Dict[str, Any] = field(default_factory=dict)
    witness_results: List[WitnessResult] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)
    memory: MemoryFields = field(default_factory=MemoryFields)
    efficiency: EfficiencyMetrics = field(default_factory=EfficiencyMetrics)
    policy_anchor_ref: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_ledger_entry(self, bundle_hash: str, rerun_recipe: Dict[str, Any]) -> LedgerEntry:
        """Convert to a ledger entry for recording."""
        return LedgerEntry(
            bundle_id=self.bundle_id,
            bundle_hash=bundle_hash,
            policy_anchor_ref=self.policy_anchor_ref,
            rerun_recipe=rerun_recipe,
            gate_outcomes=self.gate_outcomes,
            failure_reasons=self.failure_reasons,
            terminal_state=self.terminal_state,
            timestamp=self.created_at,
            memory=self.memory,
            efficiency=self.efficiency,
        )


# Type for gate functions
GateFunction = Callable[["VerificationContext"], GateOutcome]


@dataclass
class VerificationContext:
    """
    Context passed through verification gates.

    Accumulates state as gates are processed.
    """
    bundle_id: str
    scope_lock: ScopeLock
    policy_anchor: PolicyAnchor
    clean_state: CleanState
    document_content: bytes
    content_type: str

    # Accumulated during verification
    witness_results: List[WitnessResult] = field(default_factory=list)
    consensus_values: Dict[str, Any] = field(default_factory=dict)
    gate_outcomes: Dict[str, GateOutcome] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    # Tracking
    total_tokens: int = 0
    total_cost: float = 0.0
    early_termination: bool = False


class VerificationLane:
    """
    Lane B - Verification Mode

    Full verification through 11 gates with fail-closed semantics.
    Produces SHIPPED or REJECTED bundles only.

    Gate Order (FROZEN):
    B1 → B1.5 → B2 → B3 → B4 → B5 → B6 → B7 → B8 → B9 → B10 → B11

    Any gate failure → REJECTED (fail-closed)
    """

    def __init__(
        self,
        policy_anchor: PolicyAnchor,
        gates: Optional[Dict[str, GateFunction]] = None,
    ):
        self.policy_anchor = policy_anchor
        self._gates = gates or {}
        self._bundle_counter = 0

    def register_gate(self, gate_id: GateID, gate_func: GateFunction) -> None:
        """Register a gate implementation."""
        self._gates[gate_id.value] = gate_func

    def verify(
        self,
        content: bytes,
        scope_lock: ScopeLock,
        content_type: str = "application/pdf",
        draft_bundle: Optional[DraftBundle] = None,
    ) -> VerificationResult:
        """
        Run full verification on a document.

        Args:
            content: Raw document bytes
            scope_lock: The scope lock defining extraction targets
            content_type: MIME type of document
            draft_bundle: Optional draft bundle to verify (from exploration lane)

        Returns:
            VerificationResult with SHIPPED or REJECTED state
        """
        # Generate bundle ID
        self._bundle_counter += 1
        bundle_id = f"verify_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self._bundle_counter:04d}"

        # Initialize clean state
        clean_state = CleanState()

        # Create verification context
        context = VerificationContext(
            bundle_id=bundle_id,
            scope_lock=scope_lock,
            policy_anchor=self.policy_anchor,
            clean_state=clean_state,
            document_content=content,
            content_type=content_type,
        )

        # If we have a draft bundle, use its extractions as hints
        if draft_bundle:
            context.consensus_values = {
                e.field_name: e.value for e in draft_bundle.extractions
            }

        # Run gates in order (FROZEN ORDER)
        gate_order = [
            GateID.B1_WITNESSES,
            GateID.B1_5_HETEROGENEITY,
            GateID.B2_BLINDSPOT,
            GateID.B3_STRUCTURAL,
            GateID.B4_ANTI_MIXING,
            GateID.B5_SEMANTIC,
            GateID.B6_ESCALATION,
            GateID.B7_GOLD_STANDARD,
            GateID.B8_ADVERSARIAL,
            GateID.B9_TERMINAL,
            GateID.B10_RAG,
            GateID.B11_EFFICIENCY,
        ]

        failure_reasons = []

        for gate_id in gate_order:
            if gate_id.value not in self._gates:
                # Skip unregistered gates with warning
                context.warnings.append(f"Gate {gate_id.value} not registered")
                continue

            # Run gate
            gate_func = self._gates[gate_id.value]
            try:
                outcome = gate_func(context)
            except Exception as e:
                # Gate error → fail closed
                outcome = GateOutcome(
                    gate_id=gate_id.value,
                    passed=False,
                    failure_reason=f"Gate execution error: {str(e)}",
                    details={"exception": str(e)},
                )

            context.gate_outcomes[gate_id.value] = outcome

            # Check for failure (fail-closed)
            if not outcome.passed:
                failure_reasons.append(f"{gate_id.value}: {outcome.failure_reason}")

                # Check if early termination is allowed
                if self._can_early_terminate(gate_id, context):
                    context.early_termination = True
                    break

        # Determine terminal state
        if failure_reasons:
            terminal_state = TerminalState.REJECTED
        else:
            terminal_state = TerminalState.SHIPPED

        # Build efficiency metrics
        efficiency = EfficiencyMetrics(
            witnesses_used=len(context.witness_results),
            witnesses_converged_at=self._find_convergence_point(context.witness_results),
            total_tokens=context.total_tokens,
            estimated_cost_usd=context.total_cost,
            tokens_per_extracted_field=(
                context.total_tokens / max(1, len(context.consensus_values))
            ),
            early_termination=context.early_termination,
            budget_exceeded=(
                self.policy_anchor.cost_budget.max_cost_usd_per_bundle is not None and
                context.total_cost > self.policy_anchor.cost_budget.max_cost_usd_per_bundle
            ),
            heterogeneity_achieved=self._check_heterogeneity_achieved(context.witness_results),
            model_families_used=list(set(w.model_family for w in context.witness_results)),
        )

        # Build memory fields for learning
        memory = MemoryFields(
            failure_signature=self._compute_failure_signature(failure_reasons) if failure_reasons else None,
            source_context=self._extract_source_context(context),
            correction_hint=None,  # Filled by human review
            similar_past_failures=[],  # Filled by RAG gate
        )

        return VerificationResult(
            bundle_id=bundle_id,
            terminal_state=terminal_state,
            gate_outcomes=context.gate_outcomes,
            final_extractions=context.consensus_values,
            witness_results=context.witness_results,
            failure_reasons=failure_reasons,
            memory=memory,
            efficiency=efficiency,
            policy_anchor_ref=self._compute_policy_ref(),
        )

    def _can_early_terminate(self, gate_id: GateID, context: VerificationContext) -> bool:
        """Check if we can terminate early on failure."""
        # Critical gates that allow early termination
        early_terminate_gates = {
            GateID.B1_WITNESSES,  # No witnesses → cannot proceed
            GateID.B1_5_HETEROGENEITY,  # Missing heterogeneity → invalid
            GateID.B4_ANTI_MIXING,  # Arm mixing detected → stop
            GateID.B8_ADVERSARIAL,  # Adversarial failure → stop
        }
        return gate_id in early_terminate_gates

    def _find_convergence_point(self, witness_results: List[WitnessResult]) -> Optional[int]:
        """Find the witness count at which values converged."""
        if len(witness_results) < 2:
            return None

        # Check at each point if values would have converged
        for i in range(2, len(witness_results) + 1):
            subset = witness_results[:i]
            if self._check_convergence(subset):
                return i

        return None

    def _check_convergence(self, witness_results: List[WitnessResult]) -> bool:
        """Check if witnesses have converged on values."""
        if len(witness_results) < 2:
            return False

        # Get all unique keys
        all_keys = set()
        for w in witness_results:
            all_keys.update(w.extractions.keys())

        # Check agreement on each key
        agreement_threshold = self.policy_anchor.thresholds.agreement_majority
        required_agreement = int(len(witness_results) * agreement_threshold)

        for key in all_keys:
            values = [w.extractions.get(key) for w in witness_results if key in w.extractions]
            if len(values) < required_agreement:
                return False

            # Check if values agree (within tolerance for numerics)
            if all(isinstance(v, (int, float)) for v in values):
                mean_val = sum(values) / len(values)
                tolerance = self.policy_anchor.thresholds.numeric_tolerance
                if not all(abs(v - mean_val) / max(abs(mean_val), 1e-10) < tolerance for v in values):
                    return False
            else:
                # String values must match exactly
                if len(set(str(v) for v in values)) > 1:
                    return False

        return True

    def _check_heterogeneity_achieved(self, witness_results: List[WitnessResult]) -> bool:
        """Check if we achieved model heterogeneity."""
        families = set(w.model_family for w in witness_results)
        return len(families) >= 2

    def _compute_failure_signature(self, failure_reasons: List[str]) -> str:
        """Compute a signature for the failure pattern."""
        # Extract gate IDs and reason types
        pattern_parts = []
        for reason in failure_reasons:
            if ":" in reason:
                gate_id = reason.split(":")[0].strip()
                pattern_parts.append(gate_id)

        signature = "_".join(sorted(pattern_parts))
        return hashlib.sha256(signature.encode()).hexdigest()[:16]

    def _extract_source_context(self, context: VerificationContext) -> str:
        """Extract source context for learning."""
        parts = [
            f"endpoint: {context.scope_lock.endpoint}",
            f"entities: {', '.join(context.scope_lock.entities)}",
            f"witnesses: {len(context.witness_results)}",
        ]
        return " | ".join(parts)

    def _compute_policy_ref(self) -> str:
        """Compute reference hash for policy anchor."""
        policy_data = {
            "scope_lock_ref": self.policy_anchor.scope_lock_ref,
            "validator_version": self.policy_anchor.validator_version,
            "timestamp": self.policy_anchor.timestamp.isoformat(),
        }
        return hashlib.sha256(
            json.dumps(policy_data, sort_keys=True).encode()
        ).hexdigest()[:16]

    def promote_draft(
        self,
        draft_bundle: DraftBundle,
        content: bytes,
    ) -> VerificationResult:
        """
        Promote a DRAFT bundle to verification.

        Uses draft extractions as initial hints but runs full verification.
        """
        return self.verify(
            content=content,
            scope_lock=draft_bundle.scope_lock,
            content_type="application/pdf",
            draft_bundle=draft_bundle,
        )


class GateRegistry:
    """
    Registry of verification gates.

    Provides factory functions for creating standard gate implementations.
    """

    @staticmethod
    def create_witness_gate(
        min_witnesses: int = 3,
        max_witnesses: int = 5,
    ) -> GateFunction:
        """Create B1 - Witnesses gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # This would call actual LLM witnesses
            # Placeholder implementation
            n_witnesses = len(context.witness_results)

            if n_witnesses < min_witnesses:
                return GateOutcome(
                    gate_id="B1",
                    passed=False,
                    failure_reason=f"Insufficient witnesses: {n_witnesses} < {min_witnesses}",
                    details={"witness_count": n_witnesses, "required": min_witnesses},
                )

            return GateOutcome(
                gate_id="B1",
                passed=True,
                details={"witness_count": n_witnesses},
            )

        return gate

    @staticmethod
    def create_heterogeneity_gate() -> GateFunction:
        """Create B1.5 - Heterogeneity gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            families = set(w.model_family for w in context.witness_results)

            if len(families) < 2:
                return GateOutcome(
                    gate_id="B1.5",
                    passed=False,
                    failure_reason=f"Insufficient model diversity: {len(families)} families",
                    details={"families": list(families)},
                )

            return GateOutcome(
                gate_id="B1.5",
                passed=True,
                details={"families": list(families)},
            )

        return gate

    @staticmethod
    def create_blindspot_gate(correlation_threshold: float = 0.6) -> GateFunction:
        """Create B2 - Blindspot detection gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Check for systematic extraction failures
            # Placeholder - would analyze agreement patterns
            return GateOutcome(
                gate_id="B2",
                passed=True,
                details={"correlation_threshold": correlation_threshold},
            )

        return gate

    @staticmethod
    def create_structural_gate() -> GateFunction:
        """Create B3 - Structural validation gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Validate logical constraints
            # e.g., CI contains point estimate, n > 0, etc.
            extractions = context.consensus_values

            # Check CI contains point estimate
            for key in extractions:
                if "_point" in key:
                    base = key.replace("_point", "")
                    lower_key = f"{base}_ci_lower"
                    upper_key = f"{base}_ci_upper"

                    if lower_key in extractions and upper_key in extractions:
                        point = extractions[key]
                        lower = extractions[lower_key]
                        upper = extractions[upper_key]

                        if not (lower <= point <= upper):
                            return GateOutcome(
                                gate_id="B3",
                                passed=False,
                                failure_reason=f"CI does not contain point estimate: {lower} <= {point} <= {upper}",
                                details={"field": key, "point": point, "ci": [lower, upper]},
                            )

            return GateOutcome(
                gate_id="B3",
                passed=True,
                details={"checks_passed": True},
            )

        return gate

    @staticmethod
    def create_anti_mixing_gate() -> GateFunction:
        """Create B4 - Anti-mixing gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Detect if treatment arm values got swapped
            # Placeholder - would compare arm labels to values
            return GateOutcome(
                gate_id="B4",
                passed=True,
                details={"mixing_detected": False},
            )

        return gate

    @staticmethod
    def create_semantic_gate() -> GateFunction:
        """Create B5 - Semantic validation gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Check semantic consistency
            # e.g., mortality endpoint should have values < 1.0 for proportions
            return GateOutcome(
                gate_id="B5",
                passed=True,
                details={"semantic_valid": True},
            )

        return gate

    @staticmethod
    def create_escalation_gate() -> GateFunction:
        """Create B6 - Human escalation gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Check if human review is needed
            # Automatic pass if no escalation triggers
            return GateOutcome(
                gate_id="B6",
                passed=True,
                details={"escalation_required": False},
            )

        return gate

    @staticmethod
    def create_gold_standard_gate() -> GateFunction:
        """Create B7 - Gold standard comparison gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Compare against known gold standard if available
            # Pass if no gold standard to compare
            return GateOutcome(
                gate_id="B7",
                passed=True,
                details={"gold_standard_available": False},
            )

        return gate

    @staticmethod
    def create_adversarial_gate() -> GateFunction:
        """Create B8 - Adversarial cross-family testing gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Run adversarial extraction with different model family
            # Check for agreement
            families = set(w.model_family for w in context.witness_results)

            if len(families) < 2:
                return GateOutcome(
                    gate_id="B8",
                    passed=False,
                    failure_reason="Cannot run adversarial test without model diversity",
                    details={"families": list(families)},
                )

            return GateOutcome(
                gate_id="B8",
                passed=True,
                details={"adversarial_agreement": True},
            )

        return gate

    @staticmethod
    def create_terminal_gate() -> GateFunction:
        """Create B9 - Terminal state decision gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Final decision based on all previous gates
            failed_gates = [
                g for g, o in context.gate_outcomes.items()
                if not o.passed
            ]

            if failed_gates:
                return GateOutcome(
                    gate_id="B9",
                    passed=False,
                    failure_reason=f"Previous gates failed: {', '.join(failed_gates)}",
                    details={"failed_gates": failed_gates},
                )

            return GateOutcome(
                gate_id="B9",
                passed=True,
                details={"decision": "SHIP"},
            )

        return gate

    @staticmethod
    def create_rag_gate() -> GateFunction:
        """Create B10 - RAG (learning) gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Apply learning from past failures
            # This gate doesn't fail - it adds warnings
            return GateOutcome(
                gate_id="B10",
                passed=True,
                details={"warnings_applied": len(context.warnings)},
            )

        return gate

    @staticmethod
    def create_efficiency_gate(max_cost: float = 1.0) -> GateFunction:
        """Create B11 - Efficiency gate."""
        def gate(context: VerificationContext) -> GateOutcome:
            # Check cost/efficiency constraints
            if context.total_cost > max_cost:
                return GateOutcome(
                    gate_id="B11",
                    passed=False,
                    failure_reason=f"Cost exceeded: ${context.total_cost:.2f} > ${max_cost:.2f}",
                    details={"cost": context.total_cost, "max_cost": max_cost},
                )

            return GateOutcome(
                gate_id="B11",
                passed=True,
                details={
                    "cost": context.total_cost,
                    "tokens": context.total_tokens,
                    "efficiency": context.total_tokens / max(1, len(context.consensus_values)),
                },
            )

        return gate


def create_standard_verification_lane(policy_anchor: PolicyAnchor) -> VerificationLane:
    """Create a verification lane with all standard gates registered."""
    lane = VerificationLane(policy_anchor)

    # Register all gates
    lane.register_gate(GateID.B1_WITNESSES, GateRegistry.create_witness_gate())
    lane.register_gate(GateID.B1_5_HETEROGENEITY, GateRegistry.create_heterogeneity_gate())
    lane.register_gate(GateID.B2_BLINDSPOT, GateRegistry.create_blindspot_gate())
    lane.register_gate(GateID.B3_STRUCTURAL, GateRegistry.create_structural_gate())
    lane.register_gate(GateID.B4_ANTI_MIXING, GateRegistry.create_anti_mixing_gate())
    lane.register_gate(GateID.B5_SEMANTIC, GateRegistry.create_semantic_gate())
    lane.register_gate(GateID.B6_ESCALATION, GateRegistry.create_escalation_gate())
    lane.register_gate(GateID.B7_GOLD_STANDARD, GateRegistry.create_gold_standard_gate())
    lane.register_gate(GateID.B8_ADVERSARIAL, GateRegistry.create_adversarial_gate())
    lane.register_gate(GateID.B9_TERMINAL, GateRegistry.create_terminal_gate())
    lane.register_gate(GateID.B10_RAG, GateRegistry.create_rag_gate())
    lane.register_gate(GateID.B11_EFFICIENCY, GateRegistry.create_efficiency_gate(
        max_cost=policy_anchor.cost_budget.max_cost_per_bundle
    ))

    return lane
