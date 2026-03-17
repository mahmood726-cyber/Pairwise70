"""
TruthCert Configuration Management

Handles loading, validation, and management of TruthCert configurations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import hashlib


@dataclass
class ValidatorConfig:
    """Configuration for a single validator rule."""
    id: str
    rule: str
    description: str
    false_positive_rate: float = 0.0
    coverage: float = 1.0
    introduced_version: str = "1.0.0"
    approved_by: Optional[str] = None
    enabled: bool = True


@dataclass
class CorruptionConfig:
    """Configuration for adversarial corruption testing."""
    # Required corruptions (FROZEN - must detect)
    required: List[str] = field(default_factory=lambda: [
        "value_swap",
        "unit_error",
        "transcription_error",
        "arm_mismatch",
        "timepoint_shift",
        "zero_cell_injection",
    ])
    # Extended corruptions (optional)
    extended: List[str] = field(default_factory=lambda: [
        "decimal_shift",
        "sign_flip",
        "duplicate_injection",
        "missing_data_fabrication",
    ])


@dataclass
class ExternalSourceConfig:
    """Configuration for external data sources."""
    clinicaltrials_gov: bool = True
    retraction_watch: bool = True
    open_alex: bool = False
    europe_pmc: bool = False
    # Future sources
    who_ictrp: bool = False
    cochrane_central: bool = False
    prospero: bool = False


@dataclass
class TruthCertConfig:
    """
    Master configuration for TruthCert protocol.

    Manages both frozen invariants and configurable knobs.
    """

    # Version info
    version: str = "3.1.0"
    status: str = "FROZEN"

    # Validators
    validator_version: str = "validators-2026-01"
    validators: List[ValidatorConfig] = field(default_factory=list)

    # Corruption testing
    corruption_config: CorruptionConfig = field(default_factory=CorruptionConfig)

    # External sources
    external_sources: ExternalSourceConfig = field(default_factory=ExternalSourceConfig)

    # Model families for heterogeneity (FROZEN definition)
    # Different versions within same lineage do NOT count as different families
    model_families: Dict[str, List[str]] = field(default_factory=lambda: {
        "openai_gpt": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
        "anthropic_claude": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3.5-sonnet"],
        "google_gemini": ["gemini-pro", "gemini-ultra", "gemini-1.5-pro"],
        "meta_llama": ["llama-2-70b", "llama-3-70b", "llama-3.1-405b"],
        "mistral": ["mistral-large", "mistral-medium", "mixtral-8x7b"],
    })

    # Cost estimation (per 1K tokens, approximate)
    cost_per_1k_tokens: Dict[str, float] = field(default_factory=lambda: {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-4o": 0.005,
        "claude-3-opus": 0.015,
        "claude-3-sonnet": 0.003,
        "claude-3.5-sonnet": 0.003,
        "gemini-pro": 0.00025,
        "default": 0.01,
    })

    def get_model_family(self, model_name: str) -> Optional[str]:
        """Get the family for a given model name."""
        for family, models in self.model_families.items():
            if model_name in models or any(m in model_name.lower() for m in [f.lower() for f in models]):
                return family
        return None

    def count_unique_families(self, models: List[str]) -> int:
        """Count unique model families in a list of models."""
        families = set()
        for model in models:
            family = self.get_model_family(model)
            if family:
                families.add(family)
        return len(families)

    def estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for a model/token count."""
        rate = self.cost_per_1k_tokens.get(model, self.cost_per_1k_tokens["default"])
        return (tokens / 1000) * rate

    def compute_validator_set_hash(self) -> str:
        """Compute hash of the active validator ruleset."""
        validator_data = json.dumps(
            [{"id": v.id, "rule": v.rule, "enabled": v.enabled}
             for v in self.validators if v.enabled],
            sort_keys=True
        )
        return hashlib.sha256(validator_data.encode()).hexdigest()[:16]

    def get_default_validators(self) -> List[ValidatorConfig]:
        """Get the default validator set."""
        return [
            ValidatorConfig(
                id="V001",
                rule="schema_match",
                description="Output matches expected schema",
                coverage=1.0,
            ),
            ValidatorConfig(
                id="V002",
                rule="type_check",
                description="All fields have correct types",
                coverage=1.0,
            ),
            ValidatorConfig(
                id="V003",
                rule="bounds_check",
                description="Values within plausible ranges",
                coverage=0.95,
            ),
            ValidatorConfig(
                id="V004",
                rule="derived_input_match",
                description="Calculated fields match inputs",
                coverage=0.90,
            ),
            ValidatorConfig(
                id="V005",
                rule="entity_alignment",
                description="Correct arms/groups identified",
                coverage=0.95,
            ),
            ValidatorConfig(
                id="V006",
                rule="no_arm_swap",
                description="Treatment != control values",
                coverage=0.98,
            ),
            ValidatorConfig(
                id="V007",
                rule="totals_match",
                description="Sum of parts = reported total",
                coverage=0.90,
            ),
            ValidatorConfig(
                id="V008",
                rule="provenance_valid",
                description="Every value traceable to source",
                coverage=1.0,
            ),
            ValidatorConfig(
                id="V009",
                rule="no_mixing",
                description="One primary provenance chain per claim",
                coverage=0.95,
            ),
            ValidatorConfig(
                id="V010",
                rule="uncertainty_present",
                description="Uncertainty reported or derivable",
                coverage=0.85,
            ),
        ]

    @classmethod
    def load_default(cls) -> "TruthCertConfig":
        """Load default configuration."""
        config = cls()
        config.validators = config.get_default_validators()
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration."""
        return {
            "version": self.version,
            "status": self.status,
            "validator_version": self.validator_version,
            "validators": [
                {
                    "id": v.id,
                    "rule": v.rule,
                    "description": v.description,
                    "false_positive_rate": v.false_positive_rate,
                    "coverage": v.coverage,
                    "enabled": v.enabled,
                }
                for v in self.validators
            ],
            "corruption_config": {
                "required": self.corruption_config.required,
                "extended": self.corruption_config.extended,
            },
            "model_families": self.model_families,
        }

    def save(self, filepath: str) -> None:
        """Save configuration to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "TruthCertConfig":
        """Load configuration from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        config = cls()
        config.version = data.get("version", config.version)
        config.validator_version = data.get("validator_version", config.validator_version)

        if "validators" in data:
            config.validators = [
                ValidatorConfig(**v) for v in data["validators"]
            ]

        return config
