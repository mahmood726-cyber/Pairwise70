"""
TruthCert v3.1.0-FINAL - Meta-Analysis Verification Protocol

A rigorous verification system for meta-analysis data extraction with:
- Two-lane architecture (Exploration vs Verification)
- 11 verification gates for decision-grade outputs
- Append-only ledger with learning capabilities
- Multi-witness extraction with heterogeneity requirements

FROZEN INVARIANTS:
- Scope Lock: Immutable extraction targets
- Policy Anchor: Versioned configuration
- Parser Arbitration: 5% material threshold
- Terminal States: DRAFT, SHIPPED, REJECTED only
- Agreement: 80% majority, 70% strong
- Blindspot: r > 0.6 correlation threshold
- Promotion: 85% shadow→active, 95% deprecation coverage
"""

__version__ = "3.1.0"
__status__ = "FROZEN"

from .core.primitives import (
    ScopeLock,
    PolicyAnchor,
    CleanState,
    TerminalState,
    LedgerEntry,
    GateOutcome,
    MemoryFields,
    EfficiencyMetrics,
)
from .orchestrator import TruthCertOrchestrator, TruthCertConfig, create_truthcert
from .lanes.exploration import ExplorationLane, DraftBundle
from .lanes.verification import VerificationLane, VerificationResult
from .ledger.ledger import Ledger
from .validators.lifecycle import Validator, ValidatorRegistry

__all__ = [
    # Core primitives
    "ScopeLock",
    "PolicyAnchor",
    "CleanState",
    "TerminalState",
    "LedgerEntry",
    "GateOutcome",
    "MemoryFields",
    "EfficiencyMetrics",
    # Orchestrator
    "TruthCertOrchestrator",
    "TruthCertConfig",
    "create_truthcert",
    # Lanes
    "ExplorationLane",
    "DraftBundle",
    "VerificationLane",
    "VerificationResult",
    # Ledger
    "Ledger",
    # Validators
    "Validator",
    "ValidatorRegistry",
]
