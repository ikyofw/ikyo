"""Petty expense management
"""
from decimal import Decimal

from core.core.lang import Boolean2

from ..models import Office, PettyCashExpenseAdmin, User


def get_petty_admin_setting(office: Office) -> PettyCashExpenseAdmin:
    """
    """
    return PettyCashExpenseAdmin.objects.filter(office=office, enable=True).first()


def get_petty_admin(office: Office) -> User:
    """
    """
    petty_admin_rc = get_petty_admin_setting(office)
    return petty_admin_rc.admin if petty_admin_rc is not None else None


def validate_petty_admin(office: Office, user: User, pay_amount: float) -> Boolean2:
    """
    Validates whether a user has permission to approve an expense request.

    This method checks the validity of the approver based on the approval stage (first or second),
    the office, and the approval amount. Different checks are performed depending on whether 
    it is a first or second approval.

    Args:
        office (Office): The office where the approval is being processed.
        request_approver (User): The primary approver associated with the expense request.
        approver (User): The user attempting to approve the expense.
        approve_amount (float): The amount being approved during the second approval stage.
        is_first_approve (bool): A flag indicating whether this is the first approval stage.

    Returns:
        Boolean2: A Boolean2 object indicating the result of the validation:
            - `Boolean2.TRUE()` if the approver is valid.
            - `Boolean2.FALSE()` with an error message if validation fails.

    Raises:
        None.

    Example:
        office = Office.objects.get(id=1)
        request_approver = User.objects.get(id=10)
        approver = User.objects.get(id=20)
        approve_amount = 500.0
        is_first_approve = True

        result = validate_expense_approver(office, request_approver, approver, approve_amount, is_first_approve)
        if result.value:
            print("Approval is valid.")
        else:
            print(f"Approval failed: {result.data}")
    """
    rc = PettyCashExpenseAdmin.objects.filter(
        office=office, admin=user).first()
    if rc is not None:
        if rc.enable is True and pay_amount > rc.max_amt:
            return Boolean2.FALSE("Petty expense pay amount cannot greater than %f." % (rc.max_amt))
        return Boolean2.TRUE()
    return Boolean2.FALSE("Permission deny.")


def is_support_petty_expense(office_rc: Office, pay_amount: Decimal) -> bool:
    """check is the specified office is support petty cash expense or not

    Args:
        office_rc (int): Office's ID
        pay_amount (float or Decimal): claim amount.

    Returns:
        True if support putty cash expense.
    """
    petty_setting_rc = PettyCashExpenseAdmin.objects.filter(office=office_rc, enable=True).first()
    if petty_setting_rc is None:
        return False
    return pay_amount > 0 and pay_amount <= petty_setting_rc.max_amt
