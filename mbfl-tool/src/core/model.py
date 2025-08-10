"""
Data models for MBFL fault localization
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MutantInfo:
    """Represents a mutant with its metadata"""
    mutant_id: str
    operator: str
    class_name: str
    method_name: str
    line_number: int
    from_value: str
    to_value: str


@dataclass
class TestResult:
    """Represents test execution result"""
    test_name: str
    status: str  # PASS, FAIL
    error_msg: Optional[str] = None


@dataclass
class SuspiciousnessScore:
    """Represents suspiciousness score for a code location"""
    class_name: str
    method_name: str
    line_number: int
    score: float
    rank: int
    mutant_count: int