"""
Gold Standard Loader for Cochrane Meta-Analysis Data

Loads real Cochrane meta-analysis results as gold standards for TruthCert validation.
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
import hashlib


@dataclass(frozen=True)
class GoldStandardEntry:
    """
    Gold standard extraction from Cochrane meta-analysis.

    These are verified values from real Cochrane systematic reviews
    that serve as ground truth for TruthCert validation.
    """
    # Identifiers
    review_id: str
    analysis_number: int
    analysis_name: str
    doi: str
    source_hash: str

    # Core effect size
    effect_type: str  # logRR, OR, SMD, MD, GIV
    theta: float  # Point estimate
    sigma: float  # Standard error

    # Heterogeneity
    tau: float  # Between-study SD
    tau_squared: Optional[float] = None
    i_squared: Optional[float] = None

    # Study info
    k: int = 0  # Number of studies
    R: Optional[float] = None  # Reliability ratio

    # Additional metadata
    tau_estimator: str = "REML"
    r_status: str = "ok"

    def to_scope_lock_params(self) -> Dict[str, Any]:
        """Convert to ScopeLock parameters."""
        return {
            "endpoint": self.analysis_name,
            "entities": ("treatment", "control"),
            "units": self._infer_units(),
            "timepoint": "",
            "inclusion_snippet": f"Cochrane {self.review_id}",
            "source_hash": self.source_hash,
        }

    def _infer_units(self) -> str:
        """Infer units from effect type."""
        units_map = {
            "logRR": "log(risk ratio)",
            "OR": "odds ratio",
            "SMD": "standard deviation",
            "MD": "original units",
            "GIV": "generic inverse variance",
        }
        return units_map.get(self.effect_type, "")

    def get_expected_values(self) -> Dict[str, float]:
        """Get expected extraction values for validation."""
        values = {
            "effect_estimate": self.theta,
            "standard_error": self.sigma,
            "tau": self.tau,
            "k": self.k,
        }
        if self.tau_squared is not None:
            values["tau_squared"] = self.tau_squared
        if self.i_squared is not None:
            values["i_squared"] = self.i_squared
        if self.R is not None:
            values["reliability_ratio"] = self.R
        return values


class GoldStandardLoader:
    """
    Loads gold standard data from Cochrane meta-analysis results.

    Uses real data from 501 Cochrane reviews covering 4,424 analyses.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize loader with data directory.

        Args:
            data_dir: Path to Pairwise70 analysis directory
        """
        self.data_dir = Path(data_dir)
        self.results_file = self.data_dir / "ma4_results_pairwise70.csv"
        self.inventory_file = self.data_dir / "output" / "dataset_inventory.csv"
        self.heterogeneity_file = self.data_dir / "heterogeneity_output" / "tables" / "ma_summary.csv"

        self._entries: Dict[str, GoldStandardEntry] = {}
        self._heterogeneity_data: Dict[str, Dict] = {}

    def load(self) -> int:
        """
        Load all gold standard entries.

        Returns:
            Number of entries loaded
        """
        # Load heterogeneity data first
        self._load_heterogeneity()

        # Load main results
        self._load_results()

        return len(self._entries)

    def _load_heterogeneity(self) -> None:
        """Load heterogeneity statistics."""
        if not self.heterogeneity_file.exists():
            return

        with open(self.heterogeneity_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row.get('review_id', '')}_{row.get('analysis_number', '')}"
                self._heterogeneity_data[key] = {
                    "tau2_reml": self._parse_float(row.get("tau2_reml")),
                    "tau2_dl": self._parse_float(row.get("tau2_dl")),
                    "i2": self._parse_float(row.get("i2")),
                }

    def _load_results(self) -> None:
        """Load main meta-analysis results."""
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")

        with open(self.results_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = self._parse_row(row)
                if entry:
                    self._entries[entry.source_hash] = entry

    def _parse_row(self, row: Dict[str, str]) -> Optional[GoldStandardEntry]:
        """Parse a CSV row into a GoldStandardEntry."""
        try:
            review_id = row.get("review_id", "")
            analysis_number = int(row.get("analysis_number", 0))

            # Generate source hash
            source_hash = hashlib.sha256(
                f"{review_id}_{analysis_number}".encode()
            ).hexdigest()[:16]

            # Get heterogeneity data if available
            het_key = f"{review_id}_{analysis_number}"
            het_data = self._heterogeneity_data.get(het_key, {})

            return GoldStandardEntry(
                review_id=review_id,
                analysis_number=analysis_number,
                analysis_name=row.get("analysis_name", ""),
                doi=row.get("doi", ""),
                source_hash=source_hash,
                effect_type=row.get("effect_type", ""),
                theta=self._parse_float(row.get("theta", 0)),
                sigma=self._parse_float(row.get("sigma", 0)),
                tau=self._parse_float(row.get("tau", 0)),
                tau_squared=het_data.get("tau2_reml"),
                i_squared=het_data.get("i2"),
                k=int(row.get("k", 0)),
                R=self._parse_float(row.get("R")),
                tau_estimator=row.get("tau_estimator", "REML"),
                r_status=row.get("R_status", "ok"),
            )
        except (ValueError, KeyError) as e:
            return None

    @staticmethod
    def _parse_float(value: Optional[str]) -> Optional[float]:
        """Parse string to float, handling NA and empty values."""
        if value is None or value == "" or value.upper() in ("NA", "NAN", "NULL"):
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def get_entry(self, source_hash: str) -> Optional[GoldStandardEntry]:
        """Get a gold standard entry by source hash."""
        return self._entries.get(source_hash)

    def get_all_entries(self) -> List[GoldStandardEntry]:
        """Get all gold standard entries."""
        return list(self._entries.values())

    def get_entries_by_effect_type(self, effect_type: str) -> List[GoldStandardEntry]:
        """Get entries filtered by effect type."""
        return [e for e in self._entries.values() if e.effect_type == effect_type]

    def get_entries_by_review(self, review_id: str) -> List[GoldStandardEntry]:
        """Get all entries for a specific Cochrane review."""
        return [e for e in self._entries.values() if e.review_id == review_id]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about loaded data."""
        entries = list(self._entries.values())

        if not entries:
            return {"count": 0}

        effect_types = {}
        for e in entries:
            effect_types[e.effect_type] = effect_types.get(e.effect_type, 0) + 1

        reviews = set(e.review_id for e in entries)

        return {
            "count": len(entries),
            "reviews": len(reviews),
            "effect_types": effect_types,
            "k_range": (min(e.k for e in entries), max(e.k for e in entries)),
            "with_heterogeneity": sum(1 for e in entries if e.i_squared is not None),
        }


def create_test_document(entry: GoldStandardEntry) -> str:
    """
    Create a synthetic test document from a gold standard entry.

    This generates text that mimics how meta-analysis results might
    appear in a publication, for testing extraction accuracy.
    """
    effect_names = {
        "logRR": "log risk ratio",
        "OR": "odds ratio",
        "SMD": "standardised mean difference",
        "MD": "mean difference",
        "GIV": "effect size",
    }

    effect_name = effect_names.get(entry.effect_type, "effect estimate")

    # Calculate CI (approximate 95% CI)
    ci_lower = entry.theta - 1.96 * entry.sigma
    ci_upper = entry.theta + 1.96 * entry.sigma

    document = f"""
Meta-Analysis Results

Review: {entry.review_id}
DOI: {entry.doi}

Analysis: {entry.analysis_name}

Results:
The pooled {effect_name} was {entry.theta:.4f} (95% CI: {ci_lower:.4f} to {ci_upper:.4f}).
Standard error: {entry.sigma:.4f}

Heterogeneity:
Number of studies: k = {entry.k}
Between-study variance: τ = {entry.tau:.4f}
"""

    if entry.tau_squared is not None:
        document += f"τ² = {entry.tau_squared:.6f}\n"

    if entry.i_squared is not None:
        document += f"I² = {entry.i_squared:.1f}%\n"

    if entry.R is not None:
        document += f"Reliability ratio R = {entry.R:.4f}\n"

    return document
