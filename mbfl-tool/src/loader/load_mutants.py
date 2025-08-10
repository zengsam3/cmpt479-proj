"""
Parser for mutants.log file from Defects4J mutation analysis
"""

from pathlib import Path
from typing import Dict
from ..core.model import MutantInfo


def parse_mutants_log(mutation_dir: Path) -> Dict[str, MutantInfo]:
    """Parse mutants.log file to extract mutant metadata"""
    mutants = {}
    mutants_file = mutation_dir / "mutants.log"

    if not mutants_file.exists():
        raise FileNotFoundError(f"mutants.log not found in {mutation_dir}")

    with open(mutants_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse format: 1:LVR:POS:0:org.apache.commons.math3.fraction.BigFraction:45:1817:2 |==> 0
            parts = line.split(' |==> ')
            if len(parts) != 2:
                continue

            left_part = parts[0]
            to_value = parts[1]

            components = left_part.split(':')
            if len(components) >= 7:
                mutant_id = components[0]
                operator = components[1]
                class_name = components[4]
                line_number = int(components[5])
                from_value = components[3] if len(components) > 3 else ""

                # Extract method name from class context - simplified approach
                method_name = "unknown"  # We'll try to infer this from source if available

                mutants[mutant_id] = MutantInfo(
                    mutant_id=mutant_id,
                    operator=operator,
                    class_name=class_name,
                    method_name=method_name,
                    line_number=line_number,
                    from_value=from_value,
                    to_value=to_value
                )
    return mutants