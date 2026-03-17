"""
Tests for TruthCert orchestrator.

Integration tests for the main orchestration layer.
"""

import pytest
import tempfile
import os
from pathlib import Path

from truthcert.orchestrator import (
    TruthCertOrchestrator,
    TruthCertConfig,
    create_truthcert,
)
from truthcert.core.primitives import TerminalState, ScopeLock


class TestTruthCertOrchestrator:
    """Test main orchestrator functionality."""

    def test_version(self):
        """Test version is correct."""
        orchestrator = create_truthcert()
        assert orchestrator.get_version() == "3.1.0-FINAL"

    def test_config_defaults(self):
        """Test default configuration matches spec."""
        orchestrator = create_truthcert()
        config = orchestrator.get_config()

        # FROZEN thresholds
        assert config["thresholds"]["numeric_tolerance"] == 0.005
        assert config["thresholds"]["agreement_majority"] == 0.80
        assert config["thresholds"]["agreement_strong"] == 0.70
        assert config["thresholds"]["blindspot_correlation"] == 0.6
        assert config["thresholds"]["parser_material_threshold"] == 0.05

        # Witness config
        assert config["witness_config"]["min_witnesses"] == 3
        assert config["witness_config"]["require_heterogeneity"] == True

    def test_create_scope_lock(self):
        """Test scope lock creation."""
        orchestrator = create_truthcert()

        scope = orchestrator.create_scope_lock(
            endpoint="overall survival",
            entities=["drug_a", "placebo"],
            units="months",
            timepoint="12 months",
            inclusion_snippet="RCT",
            source_hash="abc123",
        )

        assert isinstance(scope, ScopeLock)
        assert scope.endpoint == "overall survival"
        assert scope.entities == ("drug_a", "placebo")

    def test_explore_simple_document(self):
        """Test exploration of a simple text document."""
        # Create temporary ledger
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            ledger_path = f.name

        orchestrator = None
        try:
            orchestrator = create_truthcert(ledger_path=ledger_path)

            # Simple test content
            content = b"""
            Study Results

            Treatment: Drug A
            Control: Placebo

            Overall Survival at 12 months:
            HR 0.85 (95% CI: 0.72-0.99)
            p = 0.03

            Sample size: n = 500
            """

            scope = orchestrator.create_scope_lock(
                endpoint="overall survival",
                entities=["Drug A", "Placebo"],
                units="months",
                timepoint="12 months",
                inclusion_snippet="",
                source_hash="test",
            )

            # Explore
            draft = orchestrator.explore(content, scope, "text/plain")

            assert draft.terminal_state == TerminalState.DRAFT
            assert draft.bundle_id.startswith("draft_")
            assert len(draft.extractions) > 0  # Should extract some values

        finally:
            if orchestrator:
                orchestrator.close()
            try:
                os.unlink(ledger_path)
            except PermissionError:
                pass  # Windows file lock, skip cleanup

    def test_verify_simple_document(self):
        """Test verification of a simple document."""
        # Create temporary ledger
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            ledger_path = f.name

        orchestrator = None
        try:
            orchestrator = create_truthcert(ledger_path=ledger_path)

            content = b"HR 0.85 (95% CI: 0.72-0.99)"

            scope = orchestrator.create_scope_lock(
                endpoint="os",
                entities=["treatment", "control"],
                units="",
                timepoint="",
                inclusion_snippet="",
                source_hash="test",
            )

            # Verify
            result = orchestrator.verify(content, scope, "text/plain")

            # Result should be SHIPPED or REJECTED (not DRAFT)
            assert result.terminal_state in [TerminalState.SHIPPED, TerminalState.REJECTED]
            assert result.bundle_id.startswith("verify_")

        finally:
            if orchestrator:
                orchestrator.close()
            try:
                os.unlink(ledger_path)
            except PermissionError:
                pass  # Windows file lock, skip cleanup

    def test_ledger_recording(self):
        """Test that verification results are recorded to ledger."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            ledger_path = f.name

        orchestrator = None
        try:
            orchestrator = create_truthcert(ledger_path=ledger_path)

            content = b"HR 0.85"
            scope = orchestrator.create_scope_lock(
                endpoint="os",
                entities=["a", "b"],
                units="",
                timepoint="",
                inclusion_snippet="",
                source_hash="test",
            )

            result = orchestrator.verify(content, scope, "text/plain")

            # Query ledger
            entry = orchestrator.get_bundle(result.bundle_id)

            assert entry is not None
            assert entry.bundle_id == result.bundle_id
            assert entry.terminal_state == result.terminal_state

        finally:
            if orchestrator:
                orchestrator.close()
            try:
                os.unlink(ledger_path)
            except PermissionError:
                pass  # Windows file lock, skip cleanup

    def test_statistics(self):
        """Test statistics retrieval."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            ledger_path = f.name

        orchestrator = None
        try:
            orchestrator = create_truthcert(ledger_path=ledger_path)
            stats = orchestrator.get_statistics()

            assert "total_bundles" in stats

        finally:
            if orchestrator:
                orchestrator.close()
            try:
                os.unlink(ledger_path)
            except PermissionError:
                pass  # Windows file lock, skip cleanup


class TestTruthCertConfig:
    """Test configuration options."""

    def test_custom_config(self):
        """Test custom configuration."""
        config = TruthCertConfig(
            min_witnesses=5,
            max_cost_usd_per_bundle=1.0,
        )

        orchestrator = TruthCertOrchestrator(config)
        retrieved_config = orchestrator.get_config()

        assert retrieved_config["witness_config"]["min_witnesses"] == 5
        assert retrieved_config["cost_budget"]["max_cost_per_bundle"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
