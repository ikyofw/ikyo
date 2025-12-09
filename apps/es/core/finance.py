"""Currency
"""
from decimal import Decimal

from .es_tools import round, round2


def round_currency(number: any) -> Decimal:
    """Round currency (0.01)

    Args:
        number (float or Decimal): Input number.

    Returns:
        Round(number, 2)
    """
    # TODO: use roundCurrency to replace round2
    return round2(number)


def round_rate(rate: any) -> Decimal:
    return round(rate, "0.0000001")
