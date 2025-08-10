"""
Suspiciousness score calculation functions for different MBFL methods
"""

from typing import Dict, List, Set, Tuple
from .model import MutantInfo


def _get_test_categories(mutant_ids: List[str], mutant_status: Dict[str, str],
                         coverage_map: Dict[str, Set[str]], test_id_to_name: Dict[str, str],
                         failing_tests: Set[str]) -> Tuple[int, int, int, int]:
    """Calculate f2p, f2f, p2p, p2f for MBFL formulas"""

    f2p = f2f = p2p = p2f = 0

    # Get all tests that cover any mutant at this location
    covering_test_ids = set()
    for mutant_id in mutant_ids:
        covering_test_ids.update(coverage_map.get(mutant_id, set()))

    # Debug: Check if we have any covering tests
    if not covering_test_ids:
        return f2p, f2f, p2p, p2f

    for test_id in covering_test_ids:
        # If testMap exists, use it to get test name; otherwise use test_id directly
        test_name = test_id_to_name.get(test_id, test_id)

        # Check if this test is failing with flexible matching
        is_failing_test = _is_failing_test(test_name, test_id, failing_tests)

        # Check if any mutant at this location is killed by this test
        mutant_killed = False
        for mutant_id in mutant_ids:
            if (test_id in coverage_map.get(mutant_id, set()) and
                    mutant_status.get(mutant_id) == 'FAIL'):
                mutant_killed = True
                break

        # Categorize based on test result and mutant kill status
        if is_failing_test and mutant_killed:
            f2p += 1
        elif is_failing_test and not mutant_killed:
            f2f += 1
        elif not is_failing_test and not mutant_killed:
            p2p += 1
        elif not is_failing_test and mutant_killed:
            p2f += 1

    return f2p, f2f, p2p, p2f


def _is_failing_test(test_name: str, test_id: str, failing_tests: Set[str]) -> bool:
    """Check if a test is failing with flexible matching"""
    # Direct match
    if test_name in failing_tests or test_id in failing_tests:
        return True

    # Check if any failing test matches this test (handles different formats)
    for failing_test in failing_tests:
        if _is_test_match(test_name, failing_test):
            return True

    return False


def _is_test_match(test_name: str, failing_test: str) -> bool:
    """Check if test_name matches failing_test with various strategies"""
    # Extract class name from failing test (remove ::method part)
    if '::' in failing_test:
        failing_class = failing_test.split('::')[0]
    else:
        failing_class = failing_test

    # Strategy 1: Exact class match
    if test_name == failing_class:
        return True

    # Strategy 2: Test name ends with the failing class (handles packages)
    if test_name.endswith(failing_class.split('.')[-1]):
        return True

    # Strategy 3: Class name similarity
    failing_simple = failing_class.split('.')[-1]  # Get just the class name
    test_simple = test_name.split('.')[-1]

    # Remove common suffixes for comparison
    failing_base = failing_simple.replace('Test', '').replace('Tests', '')
    test_base = test_simple.replace('Test', '').replace('Tests', '')

    # Check for common base (e.g., Fraction matches ContinuedFraction, BigFraction, etc.)
    if len(failing_base) >= 4:  # Minimum meaningful length
        if (failing_base in test_base or test_base in failing_base):
            return True

    # Strategy 4: Check if they share the same package and have related names
    failing_package = '.'.join(failing_class.split('.')[:-1])
    test_package = '.'.join(test_name.split('.')[:-1])

    if failing_package == test_package:
        # Same package - check for word overlap
        failing_words = set(failing_base.lower().split())
        test_words = set(test_base.lower().split())

        # Add word splitting by camelCase
        failing_words.update(_split_camel_case(failing_base.lower()))
        test_words.update(_split_camel_case(test_base.lower()))

        # If they share significant words, consider it a match
        common_words = failing_words.intersection(test_words)
        if common_words and any(len(word) >= 4 for word in common_words):
            return True

    return False


def _split_camel_case(text: str) -> List[str]:
    """Split camelCase text into words"""
    import re
    # Insert space before uppercase letters, then split
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return [word.strip() for word in spaced.split() if len(word.strip()) >= 3]


def calculate_muse(mutant_ids: List[str], mutants: Dict[str, MutantInfo],
                   mutant_status: Dict[str, str], coverage_map: Dict[str, Set[str]],
                   test_id_to_name: Dict[str, str], failing_tests: Set[str]) -> float:
    """MUSE suspiciousness calculation"""

    f2p, f2f, p2p, p2f = _get_test_categories(
        mutant_ids, mutant_status, coverage_map, test_id_to_name, failing_tests
    )

    # MUSE formula: f2p / (f2f + p2f + 1)
    denominator = f2f + p2f + 1
    return f2p / denominator if denominator > 0 else 0.0


def calculate_metallaxis(mutant_ids: List[str], mutants: Dict[str, MutantInfo],
                         mutant_status: Dict[str, str], coverage_map: Dict[str, Set[str]],
                         test_id_to_name: Dict[str, str], failing_tests: Set[str]) -> float:
    """Metallaxis suspiciousness calculation"""

    f2p, f2f, p2p, p2f = _get_test_categories(
        mutant_ids, mutant_status, coverage_map, test_id_to_name, failing_tests
    )

    # Metallaxis formula: f2p / (f2p + f2f)
    denominator = f2p + f2f
    return f2p / denominator if denominator > 0 else 0.0


def calculate_dstar(mutant_ids: List[str], mutants: Dict[str, MutantInfo],
                    mutant_status: Dict[str, str], coverage_map: Dict[str, Set[str]],
                    test_id_to_name: Dict[str, str], failing_tests: Set[str]) -> float:
    """DStar suspiciousness calculation"""

    f2p, f2f, p2p, p2f = _get_test_categories(
        mutant_ids, mutant_status, coverage_map, test_id_to_name, failing_tests
    )

    # DStar formula: f2p^2 / (f2f + p2f)
    denominator = f2f + p2f
    return (f2p ** 2) / denominator if denominator > 0 else 0.0