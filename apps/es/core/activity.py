"""Activity management
"""
from enum import Enum, unique
from core.log.logger import logger


@unique
class ActivityType(Enum):
    """Activity type
    """
    EXPENSE = 'EXP'
    CASH_ADVANCEMENT = "CA"