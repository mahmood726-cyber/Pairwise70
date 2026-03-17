"""
TruthCert Orchestrator

Main entry point for the TruthCert verification system.
Coordinates all components: parsing, lanes, gates, ledger, and validators.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import hashlib
import json

from .core.primitives import (
    ScopeLock,
    PolicyAnchor,
    CleanState,
    TerminalState,
    GateOutcome,
    LedgerEntry,
    MemoryFields,
    EfficiencyMetrics,
    Thresholds,
    WitnessConfig,
    CostBudget,
    FeatureFlags,
    PromotionPolicy,
    BudgetEnforcement,
)
from .parsers.base_parser import BaseParser, SimpleTextParser, ParsedDocument
from .parsers.parser_witness import ParserWitness, ParserArbitrator
from .lanes.exploration import ExplorationLane, DraftBundle
from .lanes.verification import VerificationLane, VerificationResult, WitnessResult
from .ledger.ledger import Ledger, LedgerStorage
from .ledger.memory import FailureMemory
from .validators.lifecycle import ValidatorRegistry, create_standard_validators
from .validators.governance import ValidatorGovernance


@dataclass
class TruthCertConfig:
    """Configuration for TruthCert orchestrator."""
    # Database path
    ledger_db_path: str = "truthcert_ledger.db"

    # Thresholds (FROZEN values)
    numeric_tolerance: float = 0.005
    agreement_majority: float = 0.80
    agreement_strong: float = 0.70
    blindspot_correlation: float = 0.6
    parser_material_threshold: float = 0.05

    # Witness configuration
    min_witnesses: int = 3
    max_witnesses: int = 5
    require_heterogeneity: bool = True

    # Cost budget
    max_cost_usd_per_bundle: float = 0.50
    max_tokens_per_bundle: int = 50000
    budget_enforcement: BudgetEnforcement = BudgetEnforcement.WARN

    # Feature flags
    rag_enabled: bool = True
    external_refs_enabled: bool = False
    gold_standard_enabled: bool = False

    # Promotion policy
    promotion_policy: PromotionPolicy = PromotionPolicy.SHADOW_FIRST


class TruthCertOrchestrator:
    """
    Main orchestrator for TruthCert verification system.

    Provides high-level API for:
    - Document exploration (Lane A → DRAFT)
    - Document verification (Lane B → SHIPPED/REJECTED)
    - Ledger management
    - Validator governance
    """

    VERSION = "3.1.0-FINAL"

    def __init__(self, config: Optional[TruthCertConfig] = None):
        self.config = config or TruthCertConfig()
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all TruthCert components."""
        # Create thresholds
        thresholds = Thresholds(
            numeric_tolerance=self.config.numeric_tolerance,
            agreement_majority=self.config.agreement_majority,
            agreement_strong=self.config.agreement_strong,
            blindspot_correlation=self.config.blindspot_correlation,
            parser_material_threshold=self.config.parser_material_threshold,
        )

        # Create witness config
        witness_config = WitnessConfig(
            min_witnesses=self.config.min_witnesses,
            max_witnesses=self.config.max_witnesses,
            require_heterogeneity=self.config.require_heterogeneity,
        )

        # Create cost budget
        cost_budget = CostBudget(
            max_cost_usd_per_bundle=self.config.max_cost_usd_per_bundle,
            max_tokens_per_bundle=self.config.max_tokens_per_bundle,
            enforcement=self.config.budget_enforcement,
        )

        # Create feature flags
        features = FeatureFlags(
            rag_enabled=self.config.rag_enabled,
            external_refs_enabled=self.config.external_refs_enabled,
            gold_standard_enabled=self.config.gold_standard_enabled,
        )

        # Create default policy anchor
        self._default_policy_anchor = PolicyAnchor(
            scope_lock_ref="default",
            validator_version=self.VERSION,
            timestamp=datetime.utcnow(),
            thresholds=thresholds,
            witness_config=witness_config,
            cost_budget=cost_budget,
            features=features,
            promotion_policy=self.config.promotion_policy,
        )

        # Initialize parsers
        self._primary_parser = SimpleTextParser()
        self._alternate_parser = SimpleTextParser()
        self._parser_witness = ParserWitness()
        self._parser_arbitrator = ParserArbitrator(
            self._primary_parser,
            self._alternate_parser,
            self._parser_witness,
        )

        # Initialize ledger
        self._ledger_storage = LedgerStorage(self.config.ledger_db_path)
        self._ledger = Ledger(self._ledger_storage)

        # Initialize memory
        self._failure_memory = FailureMemory()

        # Initialize lanes
        self._exploration_lane = ExplorationLane(self._primary_parser)
        self._verification_lane = VerificationLane(self._default_policy_anchor)

        # Initialize validators
        self._validator_registry = ValidatorRegistry(self.config.promotion_policy)
        for validator in create_standard_validators():
            self._validator_registry.validators[validator.validator_id] = validator

        # Initialize governance
        self._governance = ValidatorGovernance(
            self._validator_registry,
            self.config.promotion_policy,
        )

        # Witness functions (to be registered)
        self._witness_functions: List[Callable] = []

    def register_witness(
        self,
        witness_func: Callable[[bytes, ScopeLock], WitnessResult],
        model_name: str,
        model_family: str,
    ) -> None:
        """
        Register a witness function for extraction.

        Witness functions should take document content and scope lock,
        and return extraction results.
        """
        self._witness_functions.append({
            "func": witness_func,
            "model_name": model_name,
            "model_family": model_family,
        })

    def explore(
        self,
        content: bytes,
        scope_lock: ScopeLock,
        content_type: str = "application/pdf",
    ) -> DraftBundle:
        """
        Explore a document (Lane A).

        Returns a DRAFT bundle with best-effort extractions.
        Does not go through verification gates.
        """
        return self._exploration_lane.explore(
            content=content,
            scope_lock=scope_lock,
            content_type=content_type,
        )

    def verify(
        self,
        content: bytes,
        scope_lock: ScopeLock,
        content_type: str = "application/pdf",
        witnesses: Optional[List[WitnessResult]] = None,
    ) -> VerificationResult:
        """
        Verify a document (Lane B).

        Returns SHIPPED or REJECTED based on verification gates.
        Records result to ledger.
        """
        # If witnesses provided, use them; otherwise run registered witnesses
        if witnesses is None and self._witness_functions:
            witnesses = self._run_witnesses(content, scope_lock)

        # Run verification
        result = self._verification_lane.verify(
            content=content,
            scope_lock=scope_lock,
            content_type=content_type,
        )

        # Add witness results to context if available
        if witnesses:
            result.witness_results = witnesses

        # Record to ledger
        bundle_hash = self._compute_bundle_hash(content, scope_lock)
        rerun_recipe = self._build_rerun_recipe(scope_lock, content_type)

        self._ledger.record(
            bundle_id=result.bundle_id,
            bundle_hash=bundle_hash,
            policy_anchor_ref=result.policy_anchor_ref,
            rerun_recipe=rerun_recipe,
            gate_outcomes=result.gate_outcomes,
            terminal_state=result.terminal_state,
            failure_reasons=result.failure_reasons,
            memory=result.memory,
            efficiency=result.efficiency,
        )

        return result

    def promote_draft(
        self,
        draft_bundle: DraftBundle,
        content: bytes,
    ) -> VerificationResult:
        """
        Promote a DRAFT bundle to verification.

        Takes a draft bundle from exploration and runs full verification.
        """
        return self.verify(
            content=content,
            scope_lock=draft_bundle.scope_lock,
        )

    def _run_witnesses(
        self,
        content: bytes,
        scope_lock: ScopeLock,
    ) -> List[WitnessResult]:
        """Run all registered witness functions."""
        results = []
        for i, witness in enumerate(self._witness_functions):
            try:
                result = witness["func"](content, scope_lock)
                results.append(result)
            except Exception as e:
                # Log error but continue
                pass
        return results

    def _compute_bundle_hash(self, content: bytes, scope_lock: ScopeLock) -> str:
        """Compute hash for bundle."""
        data = {
            "content_hash": hashlib.sha256(content).hexdigest(),
            "scope_lock": {
                "endpoint": scope_lock.endpoint,
                "entities": list(scope_lock.entities),
                "timepoint": scope_lock.timepoint,
            },
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:32]

    def _build_rerun_recipe(
        self,
        scope_lock: ScopeLock,
        content_type: str,
    ) -> Dict[str, Any]:
        """Build recipe for rerunning verification."""
        return {
            "scope_lock": {
                "endpoint": scope_lock.endpoint,
                "entities": list(scope_lock.entities),
                "units": scope_lock.units,
                "timepoint": scope_lock.timepoint,
                "inclusion_snippet": scope_lock.inclusion_snippet,
                "source_hash": scope_lock.source_hash,
            },
            "content_type": content_type,
            "policy_version": self.VERSION,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Ledger access methods

    def get_bundle(self, bundle_id: str) -> Optional[LedgerEntry]:
        """Get a bundle from the ledger."""
        return self._ledger.get(bundle_id)

    def query_bundles(
        self,
        terminal_state: Optional[TerminalState] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[LedgerEntry]:
        """Query bundles from the ledger."""
        return self._ledger.query(
            terminal_state=terminal_state,
            since=since,
            limit=limit,
        )

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get ledger statistics."""
        return self._ledger.get_stats(days)

    def get_failure_patterns(self, min_count: int = 3) -> List[Dict[str, Any]]:
        """Get recurring failure patterns."""
        return self._ledger.get_failure_patterns(min_count)

    # Validator management methods

    def register_validator(
        self,
        name: str,
        description: str,
        check_function: Callable[[Dict[str, Any]], bool],
        created_by: str = "",
    ):
        """Register a new validator."""
        return self._validator_registry.register(
            name=name,
            description=description,
            check_function=check_function,
            created_by=created_by,
        )

    def get_governance_report(self) -> Dict[str, Any]:
        """Get governance status report."""
        return self._governance.generate_governance_report()

    # Utility methods

    def create_scope_lock(
        self,
        endpoint: str,
        entities: List[str],
        units: str,
        timepoint: str,
        inclusion_snippet: str,
        source_hash: str,
    ) -> ScopeLock:
        """Create a scope lock for extraction."""
        return ScopeLock(
            endpoint=endpoint,
            entities=tuple(entities),
            units=units,
            timepoint=timepoint,
            inclusion_snippet=inclusion_snippet,
            source_hash=source_hash,
        )

    def get_version(self) -> str:
        """Get TruthCert version."""
        return self.VERSION

    def close(self) -> None:
        """Close resources (database connections, etc.)."""
        if hasattr(self, '_ledger') and self._ledger:
            self._ledger.close()

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "version": self.VERSION,
            "ledger_db_path": self.config.ledger_db_path,
            "thresholds": {
                "numeric_tolerance": self.config.numeric_tolerance,
                "agreement_majority": self.config.agreement_majority,
                "agreement_strong": self.config.agreement_strong,
                "blindspot_correlation": self.config.blindspot_correlation,
                "parser_material_threshold": self.config.parser_material_threshold,
            },
            "witness_config": {
                "min_witnesses": self.config.min_witnesses,
                "max_witnesses": self.config.max_witnesses,
                "require_heterogeneity": self.config.require_heterogeneity,
            },
            "cost_budget": {
                "max_cost_per_bundle": self.config.max_cost_usd_per_bundle,
                "max_tokens_per_bundle": self.config.max_tokens_per_bundle,
                "enforcement": self.config.budget_enforcement.value,
            },
            "features": {
                "rag_enabled": self.config.rag_enabled,
                "external_refs_enabled": self.config.external_refs_enabled,
                "gold_standard_enabled": self.config.gold_standard_enabled,
            },
            "promotion_policy": self.config.promotion_policy.value,
        }


def create_truthcert(
    ledger_path: str = "truthcert_ledger.db",
    **kwargs,
) -> TruthCertOrchestrator:
    """Create a TruthCert orchestrator with optional configuration."""
    config = TruthCertConfig(ledger_db_path=ledger_path, **kwargs)
    return TruthCertOrchestrator(config)
