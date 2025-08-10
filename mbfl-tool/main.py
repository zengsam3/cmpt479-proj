#!/usr/bin/env python3
"""
Mutation-Based Fault Localization (MBFL) Tool
Implements MUSE-style fault localization using Defects4J mutation analysis data
"""

import argparse
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict

from src.core import MBFLCalculator
from src.loader import (
    parse_mutants_log, parse_kill_csv, parse_cov_map,
    parse_test_map, parse_failing_tests
)
from src.report import (
    rank_suspicious_locations, print_summary, export_results,
    SourceCodeAnalyzer, build_results_dict
)


class MBFLTool:
    """Main MBFL fault localization tool"""

    def __init__(self, mutation_dir: Path, source_dir: Optional[Path] = None):
        self.mutation_dir = mutation_dir
        self.calculator = MBFLCalculator()
        self.source_analyzer = SourceCodeAnalyzer(source_dir) if source_dir else None

    def run_analysis(self, method: str = 'muse', top_k: int = 10) -> Dict:
        """Run complete MBFL analysis"""

        print("Parsing mutation data...")

        # Load all data using loader functions
        mutants = parse_mutants_log(self.mutation_dir)
        mutant_status = parse_kill_csv(self.mutation_dir)
        coverage_map = parse_cov_map(self.mutation_dir)
        test_id_to_name = parse_test_map(self.mutation_dir)
        failing_tests = parse_failing_tests(self.mutation_dir)

        print(f"Found {len(mutants)} mutants")
        print(f"Found {len(failing_tests)} failing tests")
        print(f"Coverage data for {len(coverage_map)} mutants")
        print(f"Test ID mapping for {len(test_id_to_name)} tests")

        # Debug information
        if failing_tests:
            print(f"Failing test names: {list(failing_tests)[:3]}...")

        # Check for potential issues
        if not mutant_status:
            print("WARNING: No mutant status data found - all scores will be 0")
        if not failing_tests:
            print("WARNING: No failing tests found - MBFL requires failing tests")

        print(f"Calculating suspiciousness using {method}...")

        # Calculate suspiciousness scores
        scores = self.calculator.calculate_suspiciousness(
            mutants, mutant_status, coverage_map, test_id_to_name,
            failing_tests, method
        )

        # Rank the scores
        ranked_scores = rank_suspicious_locations(scores)

        # Get status distribution for summary
        status_distribution = self._get_status_distribution(mutant_status)

        # Build results dictionary
        results = build_results_dict(
            ranked_scores, method, len(mutants), len(failing_tests),
            status_distribution, self.source_analyzer, top_k
        )

        return results

    def _get_status_distribution(self, mutant_status: Dict[str, str]) -> Dict[str, int]:
        """Get distribution of mutant statuses"""
        distribution = defaultdict(int)
        for status in mutant_status.values():
            distribution[status] += 1
        return dict(distribution)


def main():
    parser = argparse.ArgumentParser(
        description="MBFL Fault Localization Tool for Defects4J",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python main.py --mutation-dir ./mutation_output --method muse --top-k 5
  python main.py --mutation-dir ./mutation_output --source-dir ./src/main/java --method metallaxis
        """
    )

    parser.add_argument("--mutation-dir", type=Path, required=True,
                        help="Directory containing Defects4J mutation analysis output")
    parser.add_argument("--source-dir", type=Path,
                        help="Source code directory (optional, for code context)")
    parser.add_argument("--method", choices=['muse', 'metallaxis', 'dstar'],
                        default='muse', help="MBFL method to use (default: muse)")
    parser.add_argument("--top-k", type=int, default=10,
                        help="Number of top suspicious locations to report (default: 10)")
    parser.add_argument("--output", type=Path,
                        help="Output JSON file for results (optional)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress detailed output")

    args = parser.parse_args()

    try:
        # Initialize tool
        tool = MBFLTool(args.mutation_dir, args.source_dir)

        # Run analysis
        results = tool.run_analysis(method=args.method, top_k=args.top_k)

        # Export results if requested
        if args.output:
            export_results(results, args.output)

        # Print summary unless quiet mode
        if not args.quiet:
            print_summary(results)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure all required files are present in the mutation directory:")
        print("  - mutants.log")
        print("  - kill.csv")
        print("  - covMap.csv")
        print("  - failing_tests")
        print("  - testMap.csv (optional)")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())