from enum import Enum, unique


@unique
class ExpenseType(Enum):
    """ExpenseType type
    """
    EXPENSE = "expense"
    """ expense """

    CASH_ADVANCEMENT = "cash advancement"
    """cash advancement"""
