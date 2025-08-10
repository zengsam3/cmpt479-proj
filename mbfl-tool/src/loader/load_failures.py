"""
Parser for failing_tests file from Defects4J mutation analysis
"""

from pathlib import Path
from typing import Set


def parse_failing_tests(mutation_dir: Path) -> Set[str]:
    """Parse failing_tests file to get list of failing tests"""
    failing_file = mutation_dir / "failing_tests"

    failing_tests = set()

    if not failing_file.exists():
        print(f"Warning: failing_tests file not found in {mutation_dir}")
        return failing_tests

    with open(failing_file, 'r') as f:
        current_test = None
        for line in f:
            line = line.strip()
            if line.startswith('--- '):
                # Extract test name from format: --- org.apache.commons.math3.fraction.BigFractionTest::testDigitLimitConstructor
                test_name = line[4:]  # Remove '--- '
                failing_tests.add(test_name)
                current_test = test_name

    return failing_tests