"""Activity management
"""
from enum import Enum, unique


@unique
class ActivityType(Enum):
    """Activity type
    """
    EXPENSE = 'EXP'
    CASH_ADVANCEMENT = "CA"
