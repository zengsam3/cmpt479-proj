"""
Parser for coverage-related files from Defects4J mutation analysis
"""

from pathlib import Path
from typing import Dict, Set
from collections import defaultdict


def parse_cov_map(mutation_dir: Path) -> Dict[str, Set[str]]:
    """Parse covMap.csv to get test-mutant coverage"""
    covmap_file = mutation_dir / "covMap.csv"

    if not covmap_file.exists():
        raise FileNotFoundError(f"covMap.csv not found in {mutation_dir}")

    coverage_map = defaultdict(set)

    with open(covmap_file, 'r') as f:
        lines = f.readlines()

        # Skip header line (TestNo MutantNo or TestNo,MutantNo)
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Skip header line
            if line.startswith('TestNo') or (line_num == 1 and 'MutantNo' in line):
                continue

            # Parse comma-separated format: "197,751"
            parts = line.split(',')
            if len(parts) >= 2:
                test_id = parts[0].strip()
                mutant_id = parts[1].strip()
                coverage_map[mutant_id].add(test_id)
            else:
                print(f"Warning: Could not parse line {line_num} in covMap.csv: '{line}'")

    print(f"Parsed coverage for {len(coverage_map)} mutants from covMap.csv")
    if coverage_map:
        # Show sample for debugging
        sample_mutant = list(coverage_map.keys())[0]
        sample_tests = list(coverage_map[sample_mutant])[:3]
        print(f"Sample: Mutant {sample_mutant} covered by tests {sample_tests}")

    return dict(coverage_map)


def parse_test_map(mutation_dir: Path) -> Dict[str, str]:
    """Parse testMap.csv to map test IDs to test names"""
    testmap_file = mutation_dir / "testMap.csv"

    test_id_to_name = {}

    if not testmap_file.exists():
        print("Warning: testMap.csv not found - will use test IDs directly")
        return test_id_to_name

    with open(testmap_file, 'r') as f:
        lines = f.readlines()

        # Skip header line (TestNo TestName or TestNo,TestName,...)
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Skip header line
            if line.startswith('TestNo') or (line_num == 1 and ('TestName' in line or 'TestNo' in line)):
                continue

            # Parse comma-separated format: "378,org.apache.commons.math3.analysis.integration.gauss.LegendreHighPrecisionTest,7052"
            parts = line.split(',')
            if len(parts) >= 2:
                test_id = parts[0].strip()
                test_name = parts[1].strip()  # Take the test name (second column)
                test_id_to_name[test_id] = test_name
                # Note: Ignoring third column (7052) if present
            else:
                print(f"Warning: Could not parse line {line_num} in testMap.csv: '{line}'")

    print(f"Parsed {len(test_id_to_name)} test mappings from testMap.csv")
    if test_id_to_name:
        # Show sample for debugging
        sample_items = list(test_id_to_name.items())[:3]
        print(f"Sample mappings: {sample_items}")

    return test_id_to_name