#!/usr/bin/env python
"""
TruthCert Validation Runner

Validates TruthCert against 4,424 Cochrane meta-analyses.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from truthcert.validation.gold_standard import GoldStandardLoader
from truthcert.validation.validator import CochraneValidator, run_quick_validation


def main():
    parser = argparse.ArgumentParser(
        description="Validate TruthCert against Cochrane meta-analysis data"
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent.parent / "analysis",
        help="Path to Pairwise70 analysis directory",
    )

    parser.add_argument(
        "--max-entries",
        type=int,
        default=None,
        help="Maximum entries to test (default: all)",
    )

    parser.add_argument(
        "--effect-types",
        nargs="+",
        default=None,
        help="Filter by effect types (e.g., logRR OR SMD)",
    )

    parser.add_argument(
        "--min-k",
        type=int,
        default=2,
        help="Minimum number of studies (default: 2)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for validation report",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation with 50 samples",
    )

    parser.add_argument(
        "--compare-effects",
        action="store_true",
        help="Compare validation metrics across effect types",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TruthCert Validation Suite")
    print("=" * 60)
    print(f"Data directory: {args.data_dir}")
    print()

    if args.quick:
        # Quick validation
        print("Running quick validation (50 samples)...")
        results = run_quick_validation(str(args.data_dir), n_samples=50)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nReport saved to: {args.output}")

        return

    # Full validation
    validator = CochraneValidator(args.data_dir)

    print("Loading gold standards...")
    stats = validator.load_gold_standards()

    print(f"\nGold Standard Summary:")
    print(f"  Total entries: {stats['count']}")
    print(f"  Cochrane reviews: {stats['reviews']}")
    print(f"  Effect types: {stats['effect_types']}")
    print(f"  Studies per MA: {stats['k_range'][0]} - {stats['k_range'][1]}")
    print(f"  With heterogeneity data: {stats['with_heterogeneity']}")
    print()

    if args.compare_effects:
        print("Comparing validation across effect types...")
        comparison = validator.compare_effect_types()

        print("\nEffect Type Comparison:")
        print("-" * 60)
        print(f"{'Type':<10} {'Count':<8} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<8}")
        print("-" * 60)

        for effect_type, metrics in comparison.items():
            print(
                f"{effect_type:<10} {metrics['count']:<8} "
                f"{metrics['accuracy']:.1%}       {metrics['precision']:.1%}        "
                f"{metrics['recall']:.1%}       {metrics['f1_score']:.3f}"
            )

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(comparison, f, indent=2)
            print(f"\nComparison saved to: {args.output}")

        return

    # Full validation suite
    print(f"Running validation suite...")
    if args.max_entries:
        print(f"  Max entries: {args.max_entries}")
    if args.effect_types:
        print(f"  Effect types: {args.effect_types}")
    print(f"  Min studies (k): {args.min_k}")
    print()

    report = validator.run_validation_suite(
        max_entries=args.max_entries,
        effect_types=args.effect_types,
        min_k=args.min_k,
    )

    # Print results
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print()

    print(f"Total tested: {report.total_tested}")
    print(f"  SHIPPED: {report.total_shipped}")
    print(f"  REJECTED: {report.total_rejected}")
    print(f"  DRAFT: {report.total_draft}")
    print()

    print("Confusion Matrix:")
    print(f"  True Positives:  {report.true_positives}")
    print(f"  True Negatives:  {report.true_negatives}")
    print(f"  False Positives: {report.false_positives}")
    print(f"  False Negatives: {report.false_negatives}")
    print()

    print("Metrics:")
    print(f"  Accuracy:  {report.accuracy:.1%}")
    print(f"  Precision: {report.precision:.1%}")
    print(f"  Recall:    {report.recall:.1%}")
    print(f"  F1 Score:  {report.f1_score:.3f}")
    print()

    print("Error Statistics:")
    print(f"  Mean Absolute Error: {report.mean_absolute_error:.6f}")
    print(f"  Mean Relative Error: {report.mean_relative_error:.4%}")
    print(f"  Max Error:           {report.max_error:.6f}")
    print()

    print("Cost Summary:")
    print(f"  Total Tokens:      {report.total_tokens:,}")
    print(f"  Total Cost:        ${report.total_cost_usd:.2f}")
    print(f"  Cost/Extraction:   ${report.cost_per_extraction:.4f}")
    print()

    # Save report
    output_path = args.output or Path(
        f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report.save(output_path)
    print(f"Report saved to: {output_path}")

    # Print verbose details if requested
    if args.verbose and report.false_positives > 0:
        print("\n" + "=" * 60)
        print("FALSE POSITIVE DETAILS")
        print("=" * 60)

        for result in report.results:
            if result.false_positive:
                print(f"\nReview: {result.gold_standard.review_id}")
                print(f"Analysis: {result.gold_standard.analysis_name}")
                for comp in result.comparisons:
                    if not comp.within_tolerance:
                        print(
                            f"  {comp.field_name}: expected {comp.expected:.4f}, "
                            f"got {comp.extracted:.4f if comp.extracted else 'None'} "
                            f"(error: {comp.relative_error:.2%})"
                        )


if __name__ == "__main__":
    main()
