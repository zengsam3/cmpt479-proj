"""
MBFL algorithm implementation and test matching logic
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict
from .model import MutantInfo, SuspiciousnessScore
from .scorer import calculate_muse, calculate_metallaxis, calculate_dstar


class MBFLCalculator:
    """Implements MBFL suspiciousness calculation methods"""

    def __init__(self):
        self.methods = {
            'muse': calculate_muse,
            'metallaxis': calculate_metallaxis,
            'dstar': calculate_dstar
        }

    def calculate_suspiciousness(self,
                                 mutants: Dict[str, MutantInfo],
                                 mutant_status: Dict[str, str],
                                 coverage_map: Dict[str, Set[str]],
                                 test_id_to_name: Dict[str, str],
                                 failing_tests: Set[str],
                                 method: str = 'muse') -> List[SuspiciousnessScore]:
        """Calculate suspiciousness scores for all code locations"""

        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}. Available: {list(self.methods.keys())}")

        # Debug: Check test name matching
        print(f"\nDEBUG: Checking test name matching...")
        print(f"Failing tests: {list(failing_tests)[:2]}")

        # Find some test IDs that should match failing tests
        failing_test_ids = set()
        potential_matches = []

        for test_id, test_name in test_id_to_name.items():
            # Check for exact matches first
            if test_name in failing_tests:
                failing_test_ids.add(test_id)
                continue

            # Check for partial matches
            for failing_test in failing_tests:
                if self._is_test_match(test_name, failing_test):
                    failing_test_ids.add(test_id)
                    potential_matches.append((test_id, test_name, failing_test))
                    break

        print(f"Found {len(failing_test_ids)} test IDs for failing tests: {list(failing_test_ids)[:5]}")
        if potential_matches:
            print("Potential matches found:")
            for test_id, test_name, failing_test in potential_matches[:5]:
                print(f"  {test_id}: {test_name} -> {failing_test}")

        # If no matches found, show similar test names for debugging
        if not failing_test_ids:
            print("\nNo exact matches found. Looking for similar test names...")
            for failing_test in list(failing_tests)[:2]:
                similar = self._find_similar_tests(failing_test, test_id_to_name)
                if similar:
                    print(f"For '{failing_test}', similar tests found:")
                    for test_id, test_name, similarity in similar[:5]:
                        print(f"  {test_id}: {test_name} (similarity: {similarity})")

        # Check if any mutants are actually covered by failing tests
        mutants_covered_by_failing = 0
        for mutant_id, test_ids in coverage_map.items():
            if test_ids.intersection(failing_test_ids):
                mutants_covered_by_failing += 1

        print(f"Mutants covered by failing tests: {mutants_covered_by_failing}")

        # Group mutants by location (class, line)
        location_mutants = defaultdict(list)
        for mutant_id, mutant in mutants.items():
            key = (mutant.class_name, mutant.line_number)
            location_mutants[key].append(mutant_id)

        scores = []
        debug_count = 0
        for (class_name, line_number), mutant_ids in location_mutants.items():
            # Get a representative method name (from first mutant)
            method_name = mutants[mutant_ids[0]].method_name

            score = self.methods[method](
                mutant_ids, mutants, mutant_status, coverage_map,
                test_id_to_name, failing_tests
            )

            # Debug first few calculations
            if debug_count < 3:
                f2p, f2f, p2p, p2f = self._get_test_categories(
                    mutant_ids, mutant_status, coverage_map, test_id_to_name, failing_tests
                )
                print(f"DEBUG {class_name}:{line_number} - f2p:{f2p}, f2f:{f2f}, p2p:{p2p}, p2f:{p2f}, score:{score}")
                debug_count += 1

            scores.append(SuspiciousnessScore(
                class_name=class_name,
                method_name=method_name,
                line_number=line_number,
                score=score,
                rank=0,  # Will be set after sorting
                mutant_count=len(mutant_ids)
            ))

        # Sort by score and assign ranks
        scores.sort(key=lambda x: x.score, reverse=True)
        for i, score in enumerate(scores):
            score.rank = i + 1

        return scores

    def _is_test_match(self, test_name: str, failing_test: str) -> bool:
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
            failing_words.update(self._split_camel_case(failing_base.lower()))
            test_words.update(self._split_camel_case(test_base.lower()))

            # If they share significant words, consider it a match
            common_words = failing_words.intersection(test_words)
            if common_words and any(len(word) >= 4 for word in common_words):
                return True

        return False

    def _split_camel_case(self, text: str) -> List[str]:
        """Split camelCase text into words"""
        import re
        # Insert space before uppercase letters, then split
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        return [word.strip() for word in spaced.split() if len(word.strip()) >= 3]

    def _find_similar_tests(self, failing_test: str, test_id_to_name: Dict[str, str]) -> List[Tuple[str, str, str]]:
        """Find similar test names for debugging"""
        if '::' in failing_test:
            failing_class = failing_test.split('::')[0]
        else:
            failing_class = failing_test

        failing_simple = failing_class.split('.')[-1].replace('Test', '')

        similar = []
        for test_id, test_name in test_id_to_name.items():
            test_simple = test_name.split('.')[-1].replace('Test', '')

            # Calculate simple similarity
            if failing_simple in test_simple or test_simple in failing_simple:
                similarity = f"contains '{failing_simple}'"
                similar.append((test_id, test_name, similarity))
            elif any(word in test_simple for word in failing_simple.split() if len(word) > 2):
                similarity = "partial word match"
                similar.append((test_id, test_name, similarity))

        return similar

    def _get_test_categories(self, mutant_ids: List[str], mutant_status: Dict[str, str],
                             coverage_map: Dict[str, Set[str]], test_id_to_name: Dict[str, str],
                             failing_tests: Set[str]) -> Tuple[int, int, int, int]:
        """Calculate f2p, f2f, p2p, p2f for MUSE formula"""

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
            is_failing_test = self._is_failing_test(test_name, test_id, failing_tests)

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

    def _is_failing_test(self, test_name: str, test_id: str, failing_tests: Set[str]) -> bool:
        """Check if a test is failing with flexible matching"""
        # Direct match
        if test_name in failing_tests or test_id in failing_tests:
            return True

        # Check if any failing test matches this test (handles different formats)
        for failing_test in failing_tests:
            if self._is_test_match(test_name, failing_test):
                return True

        return False