"""Accounting management
"""
import logging
from core.core.exception import IkValidateException
from core.models import User, Office
from ..models import Accounting

logger = logging.getLogger('ikyo')


def get_default_accounting(office: Office) -> User:
    """
    Retrieves the default accounting user for a given office.

    This method queries the `Accounting` model to find the default user (`is_default=True`) 
    associated with the specified office. If no default user is found, it returns `None`.

    Args:
        office (Office): The office for which to retrieve the default accounting user.

    Raises:
        IkValidateException: If the `office` parameter is `None`.

    Returns:
        User: The default accounting user associated with the office, or `None` if not found.

    Example:
        office = Office.objects.get(id=1)
        default_user = get_default_accounting(office)
        # default_user will be the default accounting user, or None if not set.
    """
    if office is None:
        raise IkValidateException("Parameter office is mandatory.")
    rc = Accounting.objects.filter(
        office=office).filter(is_default=True).first()
    return rc.usr if rc is not None else None


def validate_accounting(office: Office, user: User) -> bool:
    """
    Validates whether a given user is associated with the accounting of a specific office.

    This method checks if there is an entry in the `Accounting` model 
    that links the specified `user` to the given `office`.

    Args:
        office (Office): The office to validate against.
        user (User): The user to validate within the accounting records.

    Raises:
        IkValidateException: If either the `office` or `user` parameter is `None`.

    Returns:
        bool: True if the user is associated with the office in accounting records, 
              otherwise False.

    Example:
        office = Office.objects.get(id=1)
        user = User.objects.get(id=10)
        is_valid = validate_accounting(office, user)
        # is_valid will be True if the user is associated with the office.
    """
    if office is None or user is None:
        raise IkValidateException("Parameter office and user are mandatory.")
    rc = Accounting.objects.filter(office=office).filter(usr=user).first()
    return rc is not None


def get_accounting_user_ids(office_rc: Office) -> list[int]:
    """Get payers' IDs for an office

    Args:
        officeID (int): Office's ID.

    Returns:
        Office id list. Empty if not found.

    """
    rcs = Accounting.objects.filter(office=office_rc).order_by('id')
    return [rc.usr.id for rc in rcs]