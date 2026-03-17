"""
TruthCert Learning Gates (B10, B11)

B10: RAG-based learning from past failures
B11: Efficiency and cost tracking
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.primitives import GateOutcome, CostBudget, BudgetEnforcement
from ..ledger.memory import FailureMemory
from .witness_gates import BaseGate, WitnessExtraction


class RAGGate(BaseGate):
    """
    Gate B10 - RAG (Retrieval-Augmented Generation) Learning

    FROZEN INVARIANT:
    - structure_only: true - NEVER inject content hints
    - Only structural warnings are allowed
    - Prevents content leakage between extractions
    """

    def __init__(self, failure_memory: Optional[FailureMemory] = None):
        super().__init__("B10")
        self.failure_memory = failure_memory or FailureMemory()

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Apply RAG-based learning from past failures.

        CRITICAL: This gate only adds structural warnings.
        It NEVER injects content hints to preserve extraction independence.
        """
        scope_lock = getattr(context, 'scope_lock', None)
        consensus = getattr(context, 'consensus_values', {})

        if not scope_lock:
            return GateOutcome(
                gate_id=self.gate_id,
                passed=True,
                details={"rag_applied": False, "reason": "No scope lock"},
            )

        # Build document features for similarity search
        document_features = {
            "endpoint": scope_lock.endpoint,
            "entities": list(scope_lock.entities),
            "timepoint": scope_lock.timepoint,
            "n_fields_extracted": len(consensus),
        }

        # Get structural warnings (NEVER content hints)
        warnings = self.failure_memory.get_structural_warnings(document_features)

        # Add warnings to context
        if hasattr(context, 'warnings'):
            context.warnings.extend(warnings)

        # Get similar past failures for memory field
        similar_failures = self._find_similar_failures(document_features)

        # Update memory fields in context if available
        if hasattr(context, 'memory'):
            context.memory.similar_past_failures = similar_failures

        # RAG gate always passes - it's informational
        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                "rag_applied": True,
                "structural_warnings": len(warnings),
                "similar_failures_found": len(similar_failures),
                "warnings": warnings,
            },
        )

    def _find_similar_failures(
        self,
        document_features: Dict[str, Any],
    ) -> List[str]:
        """Find similar past failures for learning."""
        patterns = self.failure_memory.get_recurring_patterns(min_count=2)
        similar = []

        for pattern in patterns[:5]:  # Limit to top 5
            similar.append(pattern.signature)

        return similar

    def record_outcome(
        self,
        context: Any,
        success: bool,
        failure_reason: Optional[str] = None,
    ) -> None:
        """
        Record outcome for future learning.

        Call this after verification completes to update the memory.
        """
        if success:
            return  # Only record failures

        scope_lock = getattr(context, 'scope_lock', None)
        if not scope_lock:
            return

        # Generate failure signature
        signature = self._generate_failure_signature(context, failure_reason)

        # Record for future learning
        self.failure_memory.record_failure(
            signature=signature,
            source_context=f"endpoint:{scope_lock.endpoint}|entities:{','.join(scope_lock.entities)}",
            correction_hint="",  # Filled by human review
        )

    def _generate_failure_signature(
        self,
        context: Any,
        failure_reason: Optional[str],
    ) -> str:
        """Generate a failure signature for pattern matching."""
        parts = []

        # Include failed gate info
        gate_outcomes = getattr(context, 'gate_outcomes', {})
        for gate_id, outcome in gate_outcomes.items():
            if not outcome.passed:
                parts.append(gate_id)

        # Include structural indicators
        scope_lock = getattr(context, 'scope_lock', None)
        if scope_lock:
            parts.append(f"endpoint_{scope_lock.endpoint.replace(' ', '_')[:20]}")

        return "_".join(sorted(parts)) or "unknown_failure"


class EfficiencyGate(BaseGate):
    """
    Gate B11 - Efficiency and Cost Tracking

    Tracks and enforces:
    - Token usage per bundle
    - Cost per extraction
    - Early termination opportunities
    - Budget constraints
    """

    def __init__(
        self,
        cost_budget: Optional[CostBudget] = None,
        enforcement: BudgetEnforcement = BudgetEnforcement.WARN,
    ):
        super().__init__("B11")
        self.cost_budget = cost_budget or CostBudget()
        self.enforcement = enforcement

    def evaluate(self, context: Any) -> GateOutcome:
        """
        Check efficiency constraints and track costs.
        """
        witnesses: List[WitnessExtraction] = getattr(context, 'witness_results', [])
        consensus = getattr(context, 'consensus_values', {})

        # Calculate metrics
        total_tokens = sum(w.tokens_used for w in witnesses)
        total_cost = sum(w.cost_usd for w in witnesses)
        n_fields = max(1, len(consensus))
        tokens_per_field = total_tokens / n_fields

        # Store in context
        if hasattr(context, 'total_tokens'):
            context.total_tokens = total_tokens
        if hasattr(context, 'total_cost'):
            context.total_cost = total_cost

        # Build efficiency report
        efficiency_report = {
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "tokens_per_field": tokens_per_field,
            "witness_count": len(witnesses),
            "fields_extracted": n_fields,
        }

        # Check budget constraints
        budget_exceeded = False
        budget_warnings = []

        if total_cost > self.cost_budget.max_cost_per_bundle:
            budget_exceeded = True
            budget_warnings.append(
                f"Cost exceeded: ${total_cost:.4f} > ${self.cost_budget.max_cost_per_bundle:.4f}"
            )

        if total_tokens > self.cost_budget.max_tokens_per_bundle:
            budget_exceeded = True
            budget_warnings.append(
                f"Tokens exceeded: {total_tokens} > {self.cost_budget.max_tokens_per_bundle}"
            )

        # Check early termination opportunity
        early_termination = self._check_early_termination(witnesses)
        if early_termination:
            efficiency_report["early_termination_possible"] = True
            efficiency_report["optimal_witness_count"] = early_termination

        # Determine pass/fail based on enforcement policy
        if budget_exceeded:
            if self.enforcement == BudgetEnforcement.HARD:
                return GateOutcome(
                    gate_id=self.gate_id,
                    passed=False,
                    failure_reason="Budget exceeded (hard enforcement)",
                    details={
                        **efficiency_report,
                        "budget_exceeded": True,
                        "warnings": budget_warnings,
                        "enforcement": self.enforcement.value,
                    },
                )
            elif self.enforcement == BudgetEnforcement.WARN:
                # Add warning but pass
                if hasattr(context, 'warnings'):
                    context.warnings.extend(budget_warnings)

        return GateOutcome(
            gate_id=self.gate_id,
            passed=True,
            details={
                **efficiency_report,
                "budget_exceeded": budget_exceeded,
                "warnings": budget_warnings if budget_exceeded else [],
                "enforcement": self.enforcement.value,
            },
        )

    def _check_early_termination(
        self,
        witnesses: List[WitnessExtraction],
    ) -> Optional[int]:
        """
        Check if we could have terminated earlier with same result.

        Returns optimal witness count if early termination was possible.
        """
        if len(witnesses) < 3:
            return None

        # Simulate incremental consensus
        for n in range(3, len(witnesses)):
            subset = witnesses[:n]

            # Check if consensus stabilized
            if self._consensus_stable(subset, witnesses):
                return n

        return None

    def _consensus_stable(
        self,
        subset: List[WitnessExtraction],
        full: List[WitnessExtraction],
    ) -> bool:
        """Check if subset consensus matches full consensus."""
        # Build subset consensus
        subset_consensus = self._build_consensus(subset)

        # Build full consensus
        full_consensus = self._build_consensus(full)

        # Compare
        if set(subset_consensus.keys()) != set(full_consensus.keys()):
            return False

        for key in subset_consensus:
            s_val = subset_consensus[key]
            f_val = full_consensus[key]

            if isinstance(s_val, (int, float)) and isinstance(f_val, (int, float)):
                if f_val != 0 and abs(s_val - f_val) / abs(f_val) > 0.01:
                    return False
            elif str(s_val) != str(f_val):
                return False

        return True

    def _build_consensus(
        self,
        witnesses: List[WitnessExtraction],
    ) -> Dict[str, Any]:
        """Build consensus from witness extractions."""
        from collections import Counter
        import numpy as np

        consensus = {}

        all_fields = set()
        for w in witnesses:
            all_fields.update(w.extractions.keys())

        for field in all_fields:
            values = [
                w.extractions[field]
                for w in witnesses
                if field in w.extractions
            ]

            if not values:
                continue

            # Majority for categorical, mean for numeric
            if all(isinstance(v, (int, float)) for v in values):
                consensus[field] = np.mean(values)
            else:
                consensus[field] = Counter(str(v) for v in values).most_common(1)[0][0]

        return consensus

    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a given model and token counts."""
        # Pricing per 1K tokens (approximate)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        }

        # Default pricing
        default = {"input": 0.01, "output": 0.03}

        # Find matching model
        model_lower = model_name.lower()
        model_pricing = default

        for name, price in pricing.items():
            if name in model_lower:
                model_pricing = price
                break

        cost = (
            (input_tokens / 1000) * model_pricing["input"] +
            (output_tokens / 1000) * model_pricing["output"]
        )

        return cost


class CostTracker:
    """
    Tracks cumulative costs across bundles.
    """

    def __init__(self, daily_budget: float = 100.0):
        self.daily_budget = daily_budget
        self.daily_costs: Dict[str, float] = {}  # date -> cost
        self.bundle_costs: List[Dict[str, Any]] = []

    def record(
        self,
        bundle_id: str,
        cost: float,
        tokens: int,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a bundle's cost."""
        ts = timestamp or datetime.utcnow()
        date_key = ts.strftime("%Y-%m-%d")

        self.daily_costs[date_key] = self.daily_costs.get(date_key, 0) + cost

        self.bundle_costs.append({
            "bundle_id": bundle_id,
            "cost": cost,
            "tokens": tokens,
            "timestamp": ts.isoformat(),
        })

    def get_daily_remaining(self, date: Optional[str] = None) -> float:
        """Get remaining budget for a day."""
        date_key = date or datetime.utcnow().strftime("%Y-%m-%d")
        spent = self.daily_costs.get(date_key, 0)
        return max(0, self.daily_budget - spent)

    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for recent days."""
        from datetime import timedelta

        today = datetime.utcnow().date()
        summary = {
            "daily_budget": self.daily_budget,
            "days": {},
            "total_cost": 0,
            "total_bundles": 0,
        }

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            cost = self.daily_costs.get(date, 0)
            summary["days"][date] = cost
            summary["total_cost"] += cost

        summary["total_bundles"] = len(self.bundle_costs)
        summary["avg_cost_per_bundle"] = (
            summary["total_cost"] / max(1, summary["total_bundles"])
        )

        return summary
