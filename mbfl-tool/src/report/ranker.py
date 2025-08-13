"""
Ranking logic for suspicious locations in MBFL analysis
"""

from typing import Dict, List
from ..core.model import SuspiciousnessScore


def rank_suspicious_locations(scores: List[SuspiciousnessScore]) -> List[SuspiciousnessScore]:
    """Sort suspiciousness scores and assign ranks"""

    # Sort by score (descending), then by mutant count (descending) as tiebreaker
    scores.sort(key=lambda x: (x.score, x.mutant_count), reverse=True)

    # Assign ranks
    for i, score in enumerate(scores):
        score.rank = i + 1

    return scores


def filter_top_k(scores: List[SuspiciousnessScore], top_k: int) -> List[SuspiciousnessScore]:
    """Return top-k suspicious locations"""
    return scores[:top_k]


def get_status_distribution(mutant_status: Dict[str, str]) -> Dict[str, int]:
    """Get distribution of mutant statuses"""
    from collections import defaultdict

    distribution = defaultdict(int)
    for status in mutant_status.values():
        distribution[status] += 1
    return dict(distribution)