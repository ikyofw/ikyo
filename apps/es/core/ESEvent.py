"""ES event manager.
"""
from datetime import datetime
from enum import Enum, unique
from es.models import Event
from core.models import User


@unique
class EventCategory(Enum):
    """Event cateogry list.
    """

    EXPENSE = "expense"
    EXPENSE_PAY = "expense-pay"
    CASH_ADVANCEMENT = "cash"
    CASH_ADVANCEMENT_PAY = "cash-pay"
    CASH_EXCHANGE = "cash-exchange"  # TODO:
    CATEGORY_PETTY_CASH_EXPENSE_SUBMIT = "petty-cash-expense-submit"


def __create_event_rc(event_date: datetime, operator: User, sn: str, category: EventCategory, original_status: str, new_status: str, description: str = None) -> Event:
    """Add expense event

        file (:obj:`pathlib.Path`): File's full path.

    Args:
        event_date (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Expense SN or Cash Advancement SN.
        category (:obj:`EventCategory`): Event category.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
            description (str): Event description.

    Returns:
        Return event record.
    """
    rc = Event(cat=category.value,
               expense_sn=sn,
               usr=operator,
               orig_sts=original_status.value if isinstance(original_status, EventCategory) else original_status,
               new_sts=new_status.value if isinstance(new_status, EventCategory) else new_status,
               dsc=description)
    rc.cre_dt = event_date
    return rc


def add_expense_event(event_date: datetime, operator: User, sn: str, original_status: str, new_status: str, description: str = None) -> Event:
    """Add expense event

    Args:
        event_date (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Expense SN.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
        description (str): Event description.

    Returns:
        Return event record.
    """
    return __create_event_rc(event_date, operator, sn, EventCategory.EXPENSE, original_status, new_status, description)


def add_expense_pay_event(event_date: datetime, operator: User, sn: str, original_status: str, new_status: str, description: str = None) -> Event:
    """Add expense payment event

    Args:
        event_date (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Expense SN.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
            description (str): Event description.

    Returns:
        Return event record.
    """
    return __create_event_rc(event_date, operator, sn, EventCategory.EXPENSE_PAY, original_status, new_status, description)


def add_cash_advancement_event(event_date: datetime, operator: User, sn: str, original_status: str, new_status: str, description: str = None) -> Event:
    """Add cash advancement event

    Args:
        event_date (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Cash advancement SN.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
            description (str): Event description.

    Returns:
        Return event record.
    """
    return __create_event_rc(event_date, operator, sn, EventCategory.CASH_ADVANCEMENT, original_status, new_status, description)


def add_cash_advancement_pay_event(event_date: datetime, operator: User, sn: str, original_status: str, new_status: str, description: str = None) -> Event:
    """Add cash advancement payment event

    Args:
        eventDate (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Cash advancement SN.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
            description (str): Event description.

    Returns:
        Return event record.
    """
    return __create_event_rc(event_date, operator, sn, EventCategory.CASH_ADVANCEMENT_PAY, original_status, new_status, description)


def add_submit_petty_cash_expense_event(event_date: datetime, operator: User, sn: str, original_status: str, new_status: str, description: str = None) -> Event:
    """Add cash advancement payment event

    Args:
        event_date (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Cash advancement SN.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
        description (str): Event description.

    Returns:
        Return event record.
    """
    return __create_event_rc(event_date, operator, sn, EventCategory.CATEGORY_PETTY_CASH_EXPENSE_SUBMIT, original_status, new_status, description)


def add_cash_exchange_event(event_date: datetime, operator: User, sn: str, original_status: str, new_status: str, description: str = None) -> Event:
    """Add cash advancement exchange event

    Args:
        event_date (:obj:`datetime.datetime`): Action date.
        operator (:obj:`core.models.User`): Operator.
        sn (str): Cash advancement SN.
        original_status (str): Expense original status.
        new_status (str): Expense new status.
        description (str): Event description.

    Returns:
        Return event record.
    """
    return __create_event_rc(event_date, operator, sn, EventCategory.CASH_EXCHANGE, original_status, new_status, description)
