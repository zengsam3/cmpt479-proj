"""
Parser for kill.csv file from Defects4J mutation analysis
"""

from pathlib import Path
from typing import Dict


def parse_kill_csv(mutation_dir: Path) -> Dict[str, str]:
    """Parse kill.csv to get mutant status"""
    kill_file = mutation_dir / "kill.csv"

    if not kill_file.exists():
        raise FileNotFoundError(f"kill.csv not found in {mutation_dir}")

    mutant_status = {}

    with open(kill_file, 'r') as f:
        lines = f.readlines()

        # Skip header line (MutantNo [FAIL | TIME | EXC | LIVE | UNCOV] or similar)
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Skip header line
            if line.startswith('MutantNo') or '[FAIL' in line or (
                    line_num == 1 and any(x in line for x in ['FAIL', 'TIME', 'EXC', 'LIVE', 'UNCOV'])):
                continue

            # Try comma-separated first: "1,FAIL"
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    mutant_id = parts[0].strip()
                    status = parts[1].strip()
                    mutant_status[mutant_id] = status
                    continue

            # Then try space-separated: "1 FAIL"
            parts = line.split()
            if len(parts) >= 2:
                mutant_id = parts[0]
                status = parts[1]
                mutant_status[mutant_id] = status
            else:
                print(f"Warning: Could not parse line {line_num} in kill.csv: '{line}'")

    print(f"Parsed {len(mutant_status)} mutant statuses from kill.csv")
    if mutant_status:
        # Show sample of statuses for debugging
        sample_statuses = list(mutant_status.values())[:5]
        print(f"Sample statuses: {sample_statuses}")

        # Show status distribution
        status_counts = {}
        for status in mutant_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"Status distribution: {status_counts}")

    return mutant_status