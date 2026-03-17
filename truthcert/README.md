# TruthCert v3.1.0-FINAL

**Meta-Analysis Verification Protocol**

A rigorous verification system for meta-analysis data extraction with decision-grade outputs.

## Overview

TruthCert implements a two-lane architecture for document processing:

- **Lane A (Exploration)**: Fast, best-effort extraction → DRAFT bundles
- **Lane B (Verification)**: Rigorous 11-gate verification → SHIPPED or REJECTED

## FROZEN Invariants

The following values are immutable and cannot be changed:

| Invariant | Value | Description |
|-----------|-------|-------------|
| Agreement Majority | 80% | Required agreement for consensus |
| Agreement Strong | 70% | Strong agreement threshold |
| Numeric Tolerance | 0.5% | Tolerance for numeric comparisons |
| Blindspot Correlation | 0.6 | Correlation threshold for blindspot detection |
| Parser Material Threshold | 5% | Material disagreement threshold |
| Minimum Witnesses | 3 | Minimum witnesses required |
| Shadow→Active | 85% | Promotion threshold |
| Deprecation Coverage | 95% | Required coverage for deprecation |

## Verification Gates (Lane B)

| Gate | Name | Description |
|------|------|-------------|
| B1 | Witnesses | Multi-witness extraction with agreement checking |
| B1.5 | Heterogeneity | Model family diversity verification |
| B2 | Blindspot | Correlation-based blindspot detection |
| B3 | Structural | Logical constraint validation |
| B4 | Anti-Mixing | Treatment arm swap detection |
| B5 | Semantic | Domain-specific validation |
| B6 | Escalation | Human review decision |
| B7 | Gold Standard | Comparison with known values |
| B8 | Adversarial | Cross-family testing |
| B9 | Terminal | Final SHIP/REJECT decision |
| B10 | RAG | Learning from past failures |
| B11 | Efficiency | Cost and token tracking |

## Quick Start

```python
from truthcert import create_truthcert, ScopeLock

# Create orchestrator
tc = create_truthcert()

# Define extraction scope
scope = tc.create_scope_lock(
    endpoint="overall survival",
    entities=["treatment", "placebo"],
    units="months",
    timepoint="12 months",
    inclusion_snippet="randomized controlled trial",
    source_hash="abc123",
)

# Explore a document (DRAFT mode)
with open("document.pdf", "rb") as f:
    content = f.read()

draft = tc.explore(content, scope)
print(f"Found {len(draft.extractions)} candidates")

# Verify for decision-grade output
result = tc.verify(content, scope)
print(f"Terminal state: {result.terminal_state}")
```

## CLI Usage

```bash
# Show version
truthcert version

# Explore a document
truthcert explore document.pdf --endpoint "overall survival" --entities treatment placebo

# Verify a document
truthcert verify document.pdf --endpoint "overall survival" --entities treatment placebo

# Query ledger
truthcert query --state shipped --limit 10

# Show statistics
truthcert stats --days 30

# Show failure patterns
truthcert patterns --min-count 3
```

## Project Structure

```
truthcert/
├── __init__.py          # Package initialization
├── orchestrator.py      # Main orchestrator
├── cli.py               # Command-line interface
├── core/
│   ├── primitives.py    # Core data structures
│   └── config.py        # Configuration
├── parsers/
│   ├── base_parser.py   # Parser base classes
│   └── parser_witness.py # Parser arbitration
├── lanes/
│   ├── exploration.py   # Lane A (DRAFT)
│   └── verification.py  # Lane B (SHIP/REJECT)
├── gates/
│   ├── witness_gates.py    # B1, B1.5, B2
│   ├── validation_gates.py # B3, B4, B5
│   ├── decision_gates.py   # B6, B7, B8, B9
│   └── learning_gates.py   # B10, B11
├── ledger/
│   ├── ledger.py        # Append-only ledger
│   └── memory.py        # RAG-based learning
├── validators/
│   ├── lifecycle.py     # Validator lifecycle
│   └── governance.py    # Promotion/deprecation
└── tests/
    ├── test_core.py
    ├── test_gates.py
    └── test_orchestrator.py
```

## Terminal States

| State | Description |
|-------|-------------|
| DRAFT | Unverified, for human review |
| SHIPPED | Verified, decision-grade quality |
| REJECTED | Failed verification, not usable |

## Key Design Principles

1. **Fail-Closed**: Any gate failure leads to REJECTED
2. **Immutability**: Scope locks and policy anchors are frozen
3. **Heterogeneity**: Multiple model families required for verification
4. **Append-Only**: Ledger entries are never modified or deleted
5. **Structure-Only RAG**: Never inject content hints from past failures

## Installation

```bash
pip install truthcert
```

Or from source:

```bash
cd truthcert
pip install -e .
```

## Running Tests

```bash
pytest truthcert/tests/ -v
```

## License

Copyright 2024. All rights reserved.
