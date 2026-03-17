"""
Tests for TruthCert validation framework.

Tests validate the gold standard loader and validation metrics.
"""

import pytest
import tempfile
import csv
from pathlib import Path

from truthcert.validation.gold_standard import (
    GoldStandardEntry,
    GoldStandardLoader,
    create_test_document,
)
from truthcert.validation.validator import (
    ExtractionComparison,
    ValidationResult,
    ValidationReport,
    CochraneValidator,
)


class TestGoldStandardEntry:
    """Test gold standard entry."""

    def test_entry_creation(self):
        """Test creating a gold standard entry."""
        entry = GoldStandardEntry(
            review_id="CD000028_pub4",
            analysis_number=1,
            analysis_name="All-cause mortality",
            doi="10.1002/14651858.CD000028.pub4",
            source_hash="abc123",
            effect_type="logRR",
            theta=-0.08,
            sigma=0.036,
            tau=0.025,
            k=13,
        )

        assert entry.review_id == "CD000028_pub4"
        assert entry.theta == -0.08
        assert entry.k == 13

    def test_entry_is_frozen(self):
        """Test that entry is immutable."""
        entry = GoldStandardEntry(
            review_id="CD000001",
            analysis_number=1,
            analysis_name="Test",
            doi="doi",
            source_hash="hash",
            effect_type="OR",
            theta=0.5,
            sigma=0.1,
            tau=0.0,
            k=5,
        )

        with pytest.raises(AttributeError):
            entry.theta = 0.6  # Should fail - frozen

    def test_get_expected_values(self):
        """Test expected values extraction."""
        entry = GoldStandardEntry(
            review_id="CD000001",
            analysis_number=1,
            analysis_name="Test",
            doi="doi",
            source_hash="hash",
            effect_type="SMD",
            theta=0.35,
            sigma=0.12,
            tau=0.08,
            tau_squared=0.0064,
            i_squared=45.2,
            k=8,
            R=0.85,
        )

        values = entry.get_expected_values()

        assert values["effect_estimate"] == 0.35
        assert values["standard_error"] == 0.12
        assert values["tau"] == 0.08
        assert values["k"] == 8
        assert values["tau_squared"] == 0.0064
        assert values["i_squared"] == 45.2
        assert values["reliability_ratio"] == 0.85


class TestExtractionComparison:
    """Test extraction comparison."""

    def test_within_tolerance(self):
        """Test comparison within tolerance."""
        comp = ExtractionComparison(
            field_name="theta",
            expected=0.85,
            extracted=0.8502,  # 0.02% error
            tolerance_used=0.005,  # 0.5% tolerance
        )

        assert comp.within_tolerance == True
        assert comp.relative_error < 0.005

    def test_outside_tolerance(self):
        """Test comparison outside tolerance."""
        comp = ExtractionComparison(
            field_name="theta",
            expected=0.85,
            extracted=0.90,  # ~6% error
            tolerance_used=0.005,
        )

        assert comp.within_tolerance == False
        assert comp.relative_error > 0.005

    def test_missing_extraction(self):
        """Test handling of missing extraction."""
        comp = ExtractionComparison(
            field_name="tau",
            expected=0.05,
            extracted=None,
        )

        assert comp.within_tolerance == False
        assert comp.absolute_error is None


class TestValidationResult:
    """Test validation result."""

    def test_all_correct(self):
        """Test result with all correct extractions."""
        gold = GoldStandardEntry(
            review_id="CD000001",
            analysis_number=1,
            analysis_name="Test",
            doi="doi",
            source_hash="hash",
            effect_type="OR",
            theta=0.5,
            sigma=0.1,
            tau=0.0,
            k=5,
        )

        comparisons = [
            ExtractionComparison("theta", 0.5, 0.5001, tolerance_used=0.005),
            ExtractionComparison("sigma", 0.1, 0.1002, tolerance_used=0.005),
        ]

        result = ValidationResult(
            gold_standard=gold,
            terminal_state="SHIPPED",
            comparisons=comparisons,
        )

        assert result.all_correct == True
        assert result.false_positive == False
        assert result.correct_count == 2

    def test_false_positive(self):
        """Test false positive detection."""
        gold = GoldStandardEntry(
            review_id="CD000001",
            analysis_number=1,
            analysis_name="Test",
            doi="doi",
            source_hash="hash",
            effect_type="OR",
            theta=0.5,
            sigma=0.1,
            tau=0.0,
            k=5,
        )

        # One comparison fails
        comparisons = [
            ExtractionComparison("theta", 0.5, 0.5001, tolerance_used=0.005),
            ExtractionComparison("sigma", 0.1, 0.2, tolerance_used=0.005),  # Wrong
        ]

        result = ValidationResult(
            gold_standard=gold,
            terminal_state="SHIPPED",  # Shipped but wrong
            comparisons=comparisons,
        )

        assert result.false_positive == True
        assert result.all_correct == False


class TestValidationReport:
    """Test validation report."""

    def test_metrics_calculation(self):
        """Test aggregate metrics calculation."""
        report = ValidationReport()

        # Create mock results
        gold = GoldStandardEntry(
            review_id="CD000001",
            analysis_number=1,
            analysis_name="Test",
            doi="doi",
            source_hash="hash",
            effect_type="OR",
            theta=0.5,
            sigma=0.1,
            tau=0.0,
            k=5,
        )

        # 8 TP, 2 FP, 1 FN, 1 TN = 12 total
        for i in range(8):
            # True positives - correct and shipped
            report.results.append(ValidationResult(
                gold_standard=gold,
                terminal_state="SHIPPED",
                comparisons=[ExtractionComparison("theta", 0.5, 0.5, tolerance_used=0.005)],
            ))

        for i in range(2):
            # False positives - wrong but shipped
            report.results.append(ValidationResult(
                gold_standard=gold,
                terminal_state="SHIPPED",
                comparisons=[ExtractionComparison("theta", 0.5, 0.7, tolerance_used=0.005)],
            ))

        # False negative - correct but rejected
        report.results.append(ValidationResult(
            gold_standard=gold,
            terminal_state="REJECTED",
            comparisons=[ExtractionComparison("theta", 0.5, 0.5, tolerance_used=0.005)],
        ))

        # True negative - wrong and rejected
        report.results.append(ValidationResult(
            gold_standard=gold,
            terminal_state="REJECTED",
            comparisons=[ExtractionComparison("theta", 0.5, 0.9, tolerance_used=0.005)],
        ))

        report.calculate_metrics()

        assert report.total_tested == 12
        assert report.true_positives == 8
        assert report.false_positives == 2
        assert report.false_negatives == 1
        assert report.true_negatives == 1

        # Accuracy = (TP + TN) / Total = (8 + 1) / 12 = 0.75
        assert abs(report.accuracy - 0.75) < 0.01

        # Precision = TP / (TP + FP) = 8 / 10 = 0.8
        assert abs(report.precision - 0.8) < 0.01

        # Recall = TP / (TP + FN) = 8 / 9 ≈ 0.889
        assert abs(report.recall - 0.889) < 0.01


class TestCreateTestDocument:
    """Test document generation."""

    def test_document_contains_values(self):
        """Test that generated document contains expected values."""
        entry = GoldStandardEntry(
            review_id="CD000028_pub4",
            analysis_number=1,
            analysis_name="All-cause mortality",
            doi="10.1002/14651858.CD000028.pub4",
            source_hash="abc123",
            effect_type="logRR",
            theta=-0.0802,
            sigma=0.036,
            tau=0.0255,
            i_squared=25.3,
            k=13,
        )

        doc = create_test_document(entry)

        # Should contain key values
        assert "CD000028_pub4" in doc
        assert "All-cause mortality" in doc
        assert "-0.0802" in doc
        assert "0.036" in doc
        assert "k = 13" in doc
        assert "I² = 25.3%" in doc


class TestGoldStandardLoader:
    """Test gold standard loader."""

    def test_loader_with_mock_data(self):
        """Test loader with mock CSV data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create mock results file
            results_file = tmppath / "ma4_results_pairwise70.csv"
            with open(results_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "review_id", "analysis_number", "analysis_name", "doi",
                    "k", "effect_type", "theta", "sigma", "tau", "R",
                    "tau_estimator", "R_status"
                ])
                writer.writerow([
                    "CD000028_pub4", "1", "All-cause mortality",
                    "10.1002/14651858.CD000028.pub4", "13", "logRR",
                    "-0.0802", "0.036", "0.0255", "0.76", "REML", "ok"
                ])
                writer.writerow([
                    "CD000123", "2", "Progression-free survival",
                    "10.1002/14651858.CD000123", "8", "SMD",
                    "0.35", "0.12", "0.08", "0.82", "REML", "ok"
                ])

            loader = GoldStandardLoader(tmppath)
            count = loader.load()

            assert count == 2

            entries = loader.get_all_entries()
            assert len(entries) == 2

            # Check first entry
            entry = [e for e in entries if e.review_id == "CD000028_pub4"][0]
            assert entry.effect_type == "logRR"
            assert abs(entry.theta - (-0.0802)) < 0.0001
            assert entry.k == 13

    def test_filter_by_effect_type(self):
        """Test filtering entries by effect type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            results_file = tmppath / "ma4_results_pairwise70.csv"
            with open(results_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "review_id", "analysis_number", "analysis_name", "doi",
                    "k", "effect_type", "theta", "sigma", "tau", "R",
                    "tau_estimator", "R_status"
                ])
                # Add various effect types
                for i, effect_type in enumerate(["logRR", "OR", "SMD", "logRR"]):
                    writer.writerow([
                        f"CD00000{i}", str(i), f"Analysis {i}",
                        f"doi{i}", "5", effect_type,
                        "0.5", "0.1", "0.05", "0.8", "REML", "ok"
                    ])

            loader = GoldStandardLoader(tmppath)
            loader.load()

            logrr = loader.get_entries_by_effect_type("logRR")
            assert len(logrr) == 2

            smd = loader.get_entries_by_effect_type("SMD")
            assert len(smd) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
