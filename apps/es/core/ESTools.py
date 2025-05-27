from decimal import Decimal


def __toDecimal(number) -> Decimal:
    return number if type(number) == Decimal else Decimal.from_float(number)


def add(a, b) -> Decimal:
    """ a + b

    Args:
        a (float): a
        b (float): b

    Returns:
        Return (a + b): Decimal
    """
    return __toDecimal(a) + __toDecimal(b)


def sub(a, b) -> Decimal:
    """ a - b

    Args:
        a (float): a
        b (float): b

    Returns:
        Return (a - b): Decimal
    """
    return __toDecimal(a) - __toDecimal(b)


def mul(a, b) -> Decimal:
    """ a * b

    Args:
        a (float): a
        b (float): b

    Returns:
        Return (a * b): Decimal
    """
    return __toDecimal(a) * __toDecimal(b)


def div(a, b) -> Decimal:
    """ a / b

    Args:
        a (float): a
        b (float): b

    Returns:
        Return (a / b): Decimal
    """
    return __toDecimal(a) / __toDecimal(b)


def round2(a) -> Decimal:
    """ round(a, 2). E.g. 2.345 -> 2.35

    Args:
        a (float): a

    Returns:
        Return round(a, 2)
    """
    d = __toDecimal(a).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
    return Decimal(0) if d == 0 else d


def round(a: any, formater: str) -> Decimal:
    d = __toDecimal(a).quantize(Decimal(formater), rounding="ROUND_HALF_UP")
    return Decimal(0) if d == 0 else d


def isTheSame(a, b) -> bool:
    if type(a) == float:
        a = Decimal(a)
    if type(b) == float:
        b = Decimal(b)
    return abs(a - b) < 0.0000000001


def isGreater(a, b, needRound2: bool = True) -> bool:
    a = __toDecimal(a)
    b = __toDecimal(b)
    if needRound2:
        a = round2(a)
        b = round2(b)
    else:
        a = a.quantize(Decimal("0.0000000001"), rounding="ROUND_HALF_UP")
        b = b.quantize(Decimal("0.0000000001"), rounding="ROUND_HALF_UP")
    return a > b
