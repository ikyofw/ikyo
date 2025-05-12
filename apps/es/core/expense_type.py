from enum import Enum, unique

# todo
@unique
class ExpenseType(Enum):
    """ExpenseType type
    """
    EXPENSE = "expense"
    """ expense """

    CASH_ADVANCEMENT = "cash advancement"
    """cash advancement"""
