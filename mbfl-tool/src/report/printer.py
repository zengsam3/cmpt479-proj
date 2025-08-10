"""
Output formatting and export functionality for MBFL results
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from ..core.model import SuspiciousnessScore
from .source_viewer import SourceCodeAnalyzer


def build_results_dict(scores: List[SuspiciousnessScore],
                       method: str,
                       total_mutants: int,
                       total_failing_tests: int,
                       mutant_status_distribution: Dict[str, int],
                       source_analyzer: Optional[SourceCodeAnalyzer] = None,
                       top_k: int = 10) -> Dict:
    """Build results dictionary for export or display"""

    # Get top-k suspicious locations with code context
    top_locations = []
    for score in scores[:top_k]:
        location_data = {
            "rank": score.rank,
            "class": score.class_name,
            "method": score.method_name,
            "line": score.line_number,
            "suspiciousness": score.score,
            "mutant_count": score.mutant_count
        }

        if source_analyzer:
            context = source_analyzer.get_code_context(
                score.class_name, score.line_number
            )
            location_data["code_context"] = context

        top_locations.append(location_data)

    return {
        "method": method,
        "total_locations": len(scores),
        "top_suspicious_locations": top_locations,
        "summary": {
            "total_mutants": total_mutants,
            "total_failing_tests": total_failing_tests,
            "mutant_status_distribution": mutant_status_distribution
        }
    }


def export_results(results: Dict, output_file: Path):
    """Export results to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results exported to {output_file}")


def print_summary(results: Dict):
    """Print analysis summary"""
    print(f"\n=== MBFL Analysis Results ({results['method'].upper()}) ===")
    print(f"Total suspicious locations: {results['total_locations']}")
    print(f"Total mutants: {results['summary']['total_mutants']}")
    print(f"Failing tests: {results['summary']['total_failing_tests']}")

    status_dist = results['summary']['mutant_status_distribution']
    print(f"Mutant status distribution: {status_dist}")

    print(f"\nTop {len(results['top_suspicious_locations'])} Suspicious Locations:")
    print("-" * 80)

    for loc in results["top_suspicious_locations"]:
        print(f"#{loc['rank']:2d}: {loc['class'].split('.')[-1]}:{loc['line']} "
              f"(score: {loc['suspiciousness']:.4f}, mutants: {loc['mutant_count']})")

        if 'code_context' in loc and 'code_lines' in loc['code_context']:
            for line_info in loc['code_context']['code_lines']:
                marker = ">>> " if line_info['is_suspicious'] else "    "
                print(f"{marker}{line_info['line_number']:4d}: {line_info['code']}")
            print()