"""
TruthCert v3.1.0 Core Primitives

Immutable data structures defining the protocol's fundamental building blocks.
These are FROZEN and cannot change without a major version bump.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import hashlib
import json


# =============================================================================
# ENUMERATIONS (FROZEN)
# =============================================================================

class TerminalState(Enum):
    """Only three terminal states exist. No limbo."""
    DRAFT = "DRAFT"           # Exploration output, not authoritative
    SHIPPED = "SHIPPED"       # Verified, decision-grade (immutable)
    REJECTED = "REJECTED"     # Failed verification (immutable)


class OutputType(Enum):
    """Exploration output types with promotion eligibility."""
    CANDIDATE_FACT = "CANDIDATE_FACT"       # Extracted data point
    CODE_DRAFT = "CODE_DRAFT"               # Generated code
    INTERPRETATION = "INTERPRETATION"       # Analytical conclusion
    HYPOTHESIS = "HYPOTHESIS"               # Speculative claim
    FACT = "FACT"                           # Verified fact
    DERIVED = "DERIVED"                     # Verified derived value


class ParseStatus(Enum):
    """Parser stability states."""
    STABLE = "stable"
    REPAIRED = "repaired"
    KILL = "kill"


class HeterogeneityLevel(Enum):
    """Model heterogeneity requirement levels."""
    REQUIRED = "required"     # Must use >=2 different model families
    PREFERRED = "preferred"   # Attempt >=2, continue if not achieved


class BudgetEnforcement(Enum):
    """Cost budget enforcement modes."""
    OFF = "off"       # Log only, never terminate
    WARN = "warn"     # Log budget_exceeded=true, continue
    HARD = "hard"     # Terminate/reject if exceeded


class WitnessMode(Enum):
    """Witness configuration modes."""
    FIXED = "fixed"       # Fixed count (default)
    SMART = "smart"       # Accuracy-optimized with early termination
    TIERED = "tiered"     # Complexity-matched


class PromotionPolicy(Enum):
    """How outputs promote from DRAFT to verification."""
    BALANCED = "balanced"
    SAFETY = "safety"
    PRODUCTIVITY = "productivity"
    SHADOW_FIRST = "shadow_first"  # Default: all validators start in shadow


class UncertaintyStatus(Enum):
    """Uncertainty availability status."""
    REPORTED = "reported"         # Source states uncertainty
    DERIVABLE = "derivable"       # Can calculate from data
    NOT_DERIVABLE = "not_derivable"  # Cannot determine


class RetractionStatus(Enum):
    """Publication retraction status."""
    NONE = "none"
    WATCH = "watch"
    RETRACTED = "retracted"


# =============================================================================
# CORE PRIMITIVES (FROZEN)
# =============================================================================

@dataclass(frozen=True)
class ScopeLock:
    """
    Immutable definition of the target extraction scope.
    Scope drift => REJECT. No exceptions.
    """
    endpoint: str               # Primary outcome measure
    entities: tuple             # Arms/groups being compared (tuple for immutability)
    units: str                  # Measurement units
    timepoint: str              # Assessment timepoint
    inclusion_snippet: str      # Key eligibility text
    source_hash: str            # SHA-256 of source document

    def __post_init__(self):
        """Validate scope lock on creation."""
        if not self.endpoint:
            raise ValueError("Endpoint is required")
        if not self.entities or len(self.entities) < 2:
            raise ValueError("At least 2 entities required for comparison")
        if not self.source_hash:
            raise ValueError("Source hash is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "entities": list(self.entities),
            "units": self.units,
            "timepoint": self.timepoint,
            "inclusion_snippet": self.inclusion_snippet,
            "source_hash": self.source_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopeLock":
        return cls(
            endpoint=data["endpoint"],
            entities=tuple(data["entities"]),
            units=data["units"],
            timepoint=data["timepoint"],
            inclusion_snippet=data["inclusion_snippet"],
            source_hash=data["source_hash"],
        )


@dataclass(frozen=True)
class Thresholds:
    """Verification thresholds (FROZEN defaults from spec)."""
    numeric_tolerance: float = 0.005          # 0.5% tolerance for numeric comparisons
    agreement_majority: float = 0.80          # 80% required agreement for consensus
    agreement_strong: float = 0.70            # 70% strong agreement threshold
    blindspot_correlation: float = 0.6        # Correlation threshold for blindspot
    parser_material_threshold: float = 0.05   # 5% material disagreement threshold


@dataclass(frozen=True)
class WitnessConfig:
    """Witness configuration for verification runs."""
    min_witnesses: int = 3                    # FROZEN: Minimum always >= 3
    max_witnesses: int = 5                    # Max for smart/tiered modes
    require_heterogeneity: bool = True        # FROZEN: Multiple model families required
    mode: WitnessMode = WitnessMode.FIXED
    convergence_threshold: float = 0.92       # Agreement ratio for early stop

    def __post_init__(self):
        if self.min_witnesses < 3:
            raise ValueError("Minimum witnesses must be >= 3 (FROZEN)")
        if self.max_witnesses < self.min_witnesses:
            raise ValueError("Max witnesses must be >= min witnesses")


@dataclass(frozen=True)
class CostBudget:
    """Cost control configuration."""
    enforcement: BudgetEnforcement = BudgetEnforcement.OFF
    max_tokens_per_bundle: Optional[int] = None
    max_cost_usd_per_bundle: Optional[float] = None
    alert_threshold_pct: float = 0.80


@dataclass(frozen=True)
class FeatureFlags:
    """Optional feature toggles."""
    external_refs_enabled: bool = False       # ClinicalTrials.gov, etc.
    rag_enabled: bool = False                 # Retrieval-augmented extraction
    gold_standard_enabled: bool = False       # Human spot-check


@dataclass(frozen=True)
class PolicyAnchor:
    """
    Immutable run seed binding that fully specifies every run.
    Blocks context bleed; every run is fully specified by its Policy Anchor.
    """
    scope_lock_ref: str                       # Reference to Scope Lock hash
    validator_version: str                    # e.g., "validators-2026-01"
    timestamp: datetime
    thresholds: Thresholds = field(default_factory=Thresholds)
    witness_config: WitnessConfig = field(default_factory=WitnessConfig)
    cost_budget: CostBudget = field(default_factory=CostBudget)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    promotion_policy: PromotionPolicy = PromotionPolicy.BALANCED
    validator_set_hash: Optional[str] = None  # Hash of active validator ruleset

    def compute_hash(self) -> str:
        """Compute deterministic hash of this policy anchor."""
        data = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope_lock_ref": self.scope_lock_ref,
            "validator_version": self.validator_version,
            "timestamp": self.timestamp.isoformat(),
            "thresholds": {
                "numeric_tolerance": self.thresholds.numeric_tolerance,
                "agreement_majority": self.thresholds.agreement_majority,
                "agreement_strong": self.thresholds.agreement_strong,
                "blindspot_correlation": self.thresholds.blindspot_correlation,
                "parser_material_threshold": self.thresholds.parser_material_threshold,
            },
            "witness_config": {
                "min_witnesses": self.witness_config.min_witnesses,
                "max_witnesses": self.witness_config.max_witnesses,
                "require_heterogeneity": self.witness_config.require_heterogeneity,
                "mode": self.witness_config.mode.value,
                "convergence_threshold": self.witness_config.convergence_threshold,
            },
            "cost_budget": {
                "enforcement": self.cost_budget.enforcement.value,
                "max_tokens_per_bundle": self.cost_budget.max_tokens_per_bundle,
                "max_cost_usd_per_bundle": self.cost_budget.max_cost_usd_per_bundle,
                "alert_threshold_pct": self.cost_budget.alert_threshold_pct,
            },
            "features": {
                "external_refs_enabled": self.features.external_refs_enabled,
                "rag_enabled": self.features.rag_enabled,
                "gold_standard_enabled": self.features.gold_standard_enabled,
            },
            "promotion_policy": self.promotion_policy.value,
            "validator_set_hash": self.validator_set_hash,
        }


@dataclass
class CleanState:
    """
    Every run begins with fresh state.
    No cached extractions, replayable inputs captured and hashed.
    """
    extracted_values: Dict[str, Any] = field(default_factory=dict)
    witness_outputs: List[Dict[str, Any]] = field(default_factory=list)
    consensus: Optional[Dict[str, Any]] = None
    terminal_state: TerminalState = TerminalState.DRAFT

    @classmethod
    def create_fresh(cls) -> "CleanState":
        """Create a fresh clean state."""
        return cls()


@dataclass
class RiskFlags:
    """Risk indicators for draft outputs."""
    mixing_suspicion: bool = False            # Multiple sources blended
    missing_provenance: bool = False          # Can't trace to source
    uncertainty_unknown: bool = False         # No confidence available
    failed_tests: List[str] = field(default_factory=list)  # Code test failures
    external_mismatch: bool = False           # Differs from registry


@dataclass
class EfficiencyMetrics:
    """Efficiency tracking for runs."""
    witnesses_used: int = 0
    witnesses_converged_at: Optional[int] = None
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    tokens_per_extracted_field: float = 0.0
    latency_ms: int = 0
    early_termination: bool = False
    early_termination_reason: Optional[str] = None
    budget_enforcement: BudgetEnforcement = BudgetEnforcement.OFF
    budget_limit_tokens: Optional[int] = None
    budget_limit_usd: Optional[float] = None
    budget_exceeded: bool = False
    heterogeneity_required: bool = True
    heterogeneity_achieved: bool = False
    model_families_used: List[str] = field(default_factory=list)


@dataclass
class MemoryFields:
    """Memory fields for learning from failures."""
    failure_signature: Optional[str] = None   # Clusterable failure pattern
    source_context: Optional[str] = None      # Document characteristics
    correction_hint: Optional[str] = None     # What would have fixed it
    embedding: Optional[List[float]] = None   # For similarity search (768-dim)
    similar_past_failures: List[str] = field(default_factory=list)


@dataclass
class ExternalRefs:
    """External reference validation results."""
    registry_id: Optional[str] = None         # e.g., NCT number
    registry_sample_size: Optional[int] = None
    registry_endpoint: Optional[str] = None
    retraction_status: RetractionStatus = RetractionStatus.NONE
    discrepancies: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GateOutcome:
    """Result of a single verification gate."""
    gate_id: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None


@dataclass
class LedgerEntry:
    """
    Append-only log entry. Every run writes to the ledger regardless of outcome.
    """
    # Core Fields (Required)
    bundle_id: str
    bundle_hash: str
    policy_anchor_ref: str
    rerun_recipe: Dict[str, Any]              # Everything needed to reproduce
    gate_outcomes: Dict[str, GateOutcome]     # Pass/fail for each gate
    failure_reasons: List[str]                # Empty if SHIPPED
    terminal_state: TerminalState
    timestamp: datetime

    # Memory Fields (Required for Learning)
    memory: MemoryFields = field(default_factory=MemoryFields)

    # Efficiency Fields (Required)
    efficiency: EfficiencyMetrics = field(default_factory=EfficiencyMetrics)

    # External Reference Fields (When Enabled)
    external_refs: Optional[ExternalRefs] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ledger entry for storage."""
        return {
            "bundle_id": self.bundle_id,
            "bundle_hash": self.bundle_hash,
            "policy_anchor_ref": self.policy_anchor_ref,
            "rerun_recipe": self.rerun_recipe,
            "gate_outcomes": {
                k: {
                    "gate_id": v.gate_id,
                    "passed": v.passed,
                    "details": v.details,
                    "failure_reason": v.failure_reason,
                }
                for k, v in self.gate_outcomes.items()
            },
            "failure_reasons": self.failure_reasons,
            "terminal_state": self.terminal_state.value,
            "timestamp": self.timestamp.isoformat(),
            "memory": {
                "failure_signature": self.memory.failure_signature,
                "source_context": self.memory.source_context,
                "correction_hint": self.memory.correction_hint,
                "embedding": self.memory.embedding,
                "similar_past_failures": self.memory.similar_past_failures,
            },
            "efficiency": {
                "witnesses_used": self.efficiency.witnesses_used,
                "witnesses_converged_at": self.efficiency.witnesses_converged_at,
                "total_tokens": self.efficiency.total_tokens,
                "estimated_cost_usd": self.efficiency.estimated_cost_usd,
                "tokens_per_extracted_field": self.efficiency.tokens_per_extracted_field,
                "early_termination": self.efficiency.early_termination,
                "budget_exceeded": self.efficiency.budget_exceeded,
                "heterogeneity_achieved": self.efficiency.heterogeneity_achieved,
                "model_families_used": self.efficiency.model_families_used,
            },
            "external_refs": self.external_refs.__dict__ if self.external_refs else None,
        }


# =============================================================================
# PROMOTION DEFAULTS (FROZEN)
# =============================================================================

PROMOTION_RATES = {
    # FROZEN validator lifecycle thresholds
    "shadow_to_active": 0.85,       # 85% agreement with existing validators
    "active_to_deprecated": 0.95,   # 95% coverage by replacement required

    # Output type promotion rates by policy
    PromotionPolicy.BALANCED: {
        OutputType.CANDIDATE_FACT: 1.00,
        OutputType.FACT: 1.00,
        OutputType.DERIVED: 1.00,
        OutputType.CODE_DRAFT: 0.80,
        OutputType.INTERPRETATION: 0.60,
        OutputType.HYPOTHESIS: 0.40,
    },
    PromotionPolicy.SAFETY: {
        OutputType.CANDIDATE_FACT: 1.00,
        OutputType.FACT: 1.00,
        OutputType.DERIVED: 1.00,
        OutputType.CODE_DRAFT: 1.00,
        OutputType.INTERPRETATION: 0.80,
        OutputType.HYPOTHESIS: 0.60,
    },
    PromotionPolicy.PRODUCTIVITY: {
        OutputType.CANDIDATE_FACT: 1.00,
        OutputType.FACT: 1.00,
        OutputType.DERIVED: 1.00,
        OutputType.CODE_DRAFT: 0.60,
        OutputType.INTERPRETATION: 0.40,
        OutputType.HYPOTHESIS: 0.20,
    },
}
