"""
TruthCert Command Line Interface

Provides CLI access to TruthCert functionality.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from .orchestrator import TruthCertOrchestrator, TruthCertConfig, create_truthcert
from .core.primitives import ScopeLock, TerminalState


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TruthCert v3.1.0-FINAL - Meta-Analysis Verification System"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")
    config_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Explore command
    explore_parser = subparsers.add_parser("explore", help="Explore a document (Lane A)")
    explore_parser.add_argument("file", help="Document file to explore")
    explore_parser.add_argument("--endpoint", required=True, help="Target endpoint")
    explore_parser.add_argument("--entities", required=True, nargs="+", help="Target entities")
    explore_parser.add_argument("--units", default="", help="Units")
    explore_parser.add_argument("--timepoint", default="", help="Timepoint")
    explore_parser.add_argument("--output", "-o", help="Output file (JSON)")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a document (Lane B)")
    verify_parser.add_argument("file", help="Document file to verify")
    verify_parser.add_argument("--endpoint", required=True, help="Target endpoint")
    verify_parser.add_argument("--entities", required=True, nargs="+", help="Target entities")
    verify_parser.add_argument("--units", default="", help="Units")
    verify_parser.add_argument("--timepoint", default="", help="Timepoint")
    verify_parser.add_argument("--output", "-o", help="Output file (JSON)")
    verify_parser.add_argument("--ledger", default="truthcert_ledger.db", help="Ledger database path")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query ledger entries")
    query_parser.add_argument("--state", choices=["shipped", "rejected", "draft"], help="Filter by state")
    query_parser.add_argument("--since", help="Filter by date (YYYY-MM-DD)")
    query_parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    query_parser.add_argument("--ledger", default="truthcert_ledger.db", help="Ledger database path")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show ledger statistics")
    stats_parser.add_argument("--days", type=int, default=30, help="Days to include")
    stats_parser.add_argument("--ledger", default="truthcert_ledger.db", help="Ledger database path")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Patterns command
    patterns_parser = subparsers.add_parser("patterns", help="Show failure patterns")
    patterns_parser.add_argument("--min-count", type=int, default=3, help="Minimum occurrence count")
    patterns_parser.add_argument("--ledger", default="truthcert_ledger.db", help="Ledger database path")

    # Validators command
    validators_parser = subparsers.add_parser("validators", help="List validators")
    validators_parser.add_argument("--state", choices=["active", "shadow", "proposed", "deprecated"],
                                   help="Filter by state")

    # Governance command
    governance_parser = subparsers.add_parser("governance", help="Show governance report")
    governance_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    try:
        return run_command(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_command(args) -> int:
    """Execute the specified command."""
    if args.command == "version":
        print(f"TruthCert v{TruthCertOrchestrator.VERSION}")
        print("Meta-Analysis Verification System")
        print("FROZEN INVARIANTS ENABLED")
        return 0

    if args.command == "config":
        orchestrator = create_truthcert()
        config = orchestrator.get_config()
        if args.json:
            print(json.dumps(config, indent=2))
        else:
            print_config(config)
        return 0

    if args.command == "explore":
        return cmd_explore(args)

    if args.command == "verify":
        return cmd_verify(args)

    if args.command == "query":
        return cmd_query(args)

    if args.command == "stats":
        return cmd_stats(args)

    if args.command == "patterns":
        return cmd_patterns(args)

    if args.command == "validators":
        return cmd_validators(args)

    if args.command == "governance":
        return cmd_governance(args)

    return 1


def cmd_explore(args) -> int:
    """Execute explore command."""
    # Read document
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    content = file_path.read_bytes()

    # Create orchestrator
    orchestrator = create_truthcert()

    # Create scope lock
    import hashlib
    source_hash = hashlib.sha256(content).hexdigest()[:16]

    scope_lock = orchestrator.create_scope_lock(
        endpoint=args.endpoint,
        entities=args.entities,
        units=args.units,
        timepoint=args.timepoint,
        inclusion_snippet="",
        source_hash=source_hash,
    )

    # Explore
    draft = orchestrator.explore(content, scope_lock)

    # Output results
    result = draft.to_dict()

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, default=str))
        print(f"Results written to {args.output}")
    else:
        print(f"\n{'='*60}")
        print(f"DRAFT Bundle: {draft.bundle_id}")
        print(f"{'='*60}")
        print(f"State: {draft.terminal_state.value}")
        print(f"Parse Status: {draft.parse_status.value}")
        print(f"\nExtractions ({len(draft.extractions)}):")
        for e in draft.extractions:
            print(f"  - {e.field_name}: {e.value} (confidence: {e.confidence:.2f})")
        if draft.warnings:
            print(f"\nWarnings:")
            for w in draft.warnings:
                print(f"  - {w}")

    return 0


def cmd_verify(args) -> int:
    """Execute verify command."""
    # Read document
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    content = file_path.read_bytes()

    # Create orchestrator
    orchestrator = create_truthcert(ledger_path=args.ledger)

    # Create scope lock
    import hashlib
    source_hash = hashlib.sha256(content).hexdigest()[:16]

    scope_lock = orchestrator.create_scope_lock(
        endpoint=args.endpoint,
        entities=args.entities,
        units=args.units,
        timepoint=args.timepoint,
        inclusion_snippet="",
        source_hash=source_hash,
    )

    # Verify
    result = orchestrator.verify(content, scope_lock)

    # Output results
    output = {
        "bundle_id": result.bundle_id,
        "terminal_state": result.terminal_state.value,
        "final_extractions": result.final_extractions,
        "gate_outcomes": {
            k: {"passed": v.passed, "reason": v.failure_reason}
            for k, v in result.gate_outcomes.items()
        },
        "failure_reasons": result.failure_reasons,
        "efficiency": {
            "witnesses_used": result.efficiency.witnesses_used,
            "total_tokens": result.efficiency.total_tokens,
            "estimated_cost_usd": result.efficiency.estimated_cost_usd,
        },
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2, default=str))
        print(f"Results written to {args.output}")
    else:
        state_icon = "✓" if result.terminal_state == TerminalState.SHIPPED else "✗"
        print(f"\n{'='*60}")
        print(f"{state_icon} {result.terminal_state.value}: {result.bundle_id}")
        print(f"{'='*60}")

        if result.final_extractions:
            print(f"\nExtractions ({len(result.final_extractions)}):")
            for k, v in result.final_extractions.items():
                print(f"  - {k}: {v}")

        print(f"\nGate Results:")
        for gate_id, outcome in result.gate_outcomes.items():
            icon = "✓" if outcome.passed else "✗"
            print(f"  {icon} {gate_id}")
            if not outcome.passed and outcome.failure_reason:
                print(f"      Reason: {outcome.failure_reason}")

        if result.failure_reasons:
            print(f"\nFailure Reasons:")
            for reason in result.failure_reasons:
                print(f"  - {reason}")

    return 0 if result.terminal_state == TerminalState.SHIPPED else 1


def cmd_query(args) -> int:
    """Execute query command."""
    orchestrator = create_truthcert(ledger_path=args.ledger)

    # Parse filters
    state = None
    if args.state:
        state = TerminalState(args.state.upper())

    since = None
    if args.since:
        since = datetime.strptime(args.since, "%Y-%m-%d")

    # Query
    entries = orchestrator.query_bundles(
        terminal_state=state,
        since=since,
        limit=args.limit,
    )

    if not entries:
        print("No entries found.")
        return 0

    print(f"\nFound {len(entries)} entries:\n")
    for entry in entries:
        icon = "✓" if entry.terminal_state == TerminalState.SHIPPED else "✗"
        print(f"  {icon} {entry.bundle_id}")
        print(f"     State: {entry.terminal_state.value}")
        print(f"     Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
        if entry.failure_reasons:
            print(f"     Failures: {len(entry.failure_reasons)}")
        print()

    return 0


def cmd_stats(args) -> int:
    """Execute stats command."""
    orchestrator = create_truthcert(ledger_path=args.ledger)
    stats = orchestrator.get_statistics(args.days)

    if args.json:
        print(json.dumps(stats, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"TruthCert Statistics (Last {args.days} days)")
        print(f"{'='*60}")
        print(f"Total Bundles: {stats.get('total_bundles', 0)}")
        print(f"Shipped: {stats.get('shipped_count', 0)}")
        print(f"Rejected: {stats.get('rejected_count', 0)}")
        print(f"Ship Rate: {stats.get('ship_rate', 0):.1%}")
        print(f"Total Tokens: {stats.get('total_tokens', 0):,}")
        print(f"Total Cost: ${stats.get('total_cost_usd', 0):.2f}")
        print(f"Avg Tokens/Bundle: {stats.get('avg_tokens_per_bundle', 0):.0f}")
        print(f"Early Termination Rate: {stats.get('early_termination_rate', 0):.1%}")

    return 0


def cmd_patterns(args) -> int:
    """Execute patterns command."""
    orchestrator = create_truthcert(ledger_path=args.ledger)
    patterns = orchestrator.get_failure_patterns(args.min_count)

    if not patterns:
        print("No recurring failure patterns found.")
        return 0

    print(f"\n{'='*60}")
    print(f"Failure Patterns (min count: {args.min_count})")
    print(f"{'='*60}")

    for pattern in patterns:
        print(f"\n  Signature: {pattern['signature']}")
        print(f"  Count: {pattern['count']}")
        print(f"  First seen: {pattern['first_seen']}")
        print(f"  Last seen: {pattern['last_seen']}")
        if pattern.get('correction_hints'):
            print(f"  Hints: {pattern['correction_hints']}")

    return 0


def cmd_validators(args) -> int:
    """Execute validators command."""
    orchestrator = create_truthcert()
    summary = orchestrator._validator_registry.get_metrics_summary()

    if args.state:
        validators = [
            v for v in summary["validators"]
            if v["state"] == args.state
        ]
    else:
        validators = summary["validators"]

    print(f"\n{'='*60}")
    print(f"Validators ({len(validators)})")
    print(f"{'='*60}")
    print(f"Active: {summary['active_count']}")
    print(f"Shadow: {summary['shadow_count']}")
    print(f"Proposed: {summary['proposed_count']}")
    print(f"Deprecated: {summary['deprecated_count']}")
    print()

    for v in validators:
        print(f"  {v['name']} (v{v['version']})")
        print(f"    ID: {v['validator_id']}")
        print(f"    State: {v['state']}")
        print(f"    Runs: {v['metrics']['total_runs']}")
        print(f"    Pass Rate: {v['metrics']['pass_rate']:.1%}")
        print()

    return 0


def cmd_governance(args) -> int:
    """Execute governance command."""
    orchestrator = create_truthcert()
    report = orchestrator.get_governance_report()

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print("TruthCert Governance Report")
        print(f"{'='*60}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Promotion Policy: {report['promotion_policy']}")
        print()
        print("Thresholds (FROZEN):")
        print(f"  Shadow→Active: {report['thresholds']['shadow_to_active']:.0%}")
        print(f"  Deprecation Coverage: {report['thresholds']['deprecation_coverage']:.0%}")
        print()
        print(f"Pending Requests:")
        print(f"  Promotions: {report['pending_requests']['promotions']}")
        print(f"  Deprecations: {report['pending_requests']['deprecations']}")
        print()
        print(f"Audit Log Entries: {report['audit_log_size']}")

    return 0


def print_config(config: dict, indent: int = 0):
    """Pretty print configuration."""
    prefix = "  " * indent
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_config(value, indent + 1)
        else:
            print(f"{prefix}{key}: {value}")


if __name__ == "__main__":
    sys.exit(main())
