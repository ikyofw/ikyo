"""Expense Status
"""
from enum import Enum, unique

from core.core.lang import Boolean2

from ..core.approver import get_second_approvers
from ..models import Office, User


@unique
class Status(Enum):
    """Expense status
    """
    DRAFT = 'draft'
    SUBMITTED = "submitted"
    APPROVED = "approved"
    FIRST_APPROVED = "first approved"
    """Used for the second approval."""
    """Petty admin confirm"""
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    SETTLED = "settled"


# Status transition mapping.
STATUS_TRANSITIONS = {
    Status.DRAFT: [Status.SUBMITTED],
    Status.SUBMITTED: [Status.CANCELLED, Status.REJECTED, Status.FIRST_APPROVED, Status.APPROVED, Status.SETTLED],
    Status.FIRST_APPROVED: [Status.REJECTED, Status.APPROVED, Status.SETTLED],
    Status.APPROVED: [Status.REJECTED, Status.SETTLED],
    Status.CANCELLED: [Status.SUBMITTED],  # the end
    Status.REJECTED: [Status.SUBMITTED],  # the end
    Status.SETTLED: [Status.SUBMITTED]    # the end,  # submit: revert settled payment
}


def get_all_status(draft: bool = False) -> list[str]:
    """Get all status values as a list.

    Args:
        draft (bool, optional): Whether to include the 'DRAFT' status in the result.
            Defaults to False.

    Returns:
        list: A list of all status values (strings).
    """
    data = []
    if draft:
        data.append(Status.DRAFT.value)
    data.append(Status.SUBMITTED.value)
    data.append(Status.APPROVED.value)
    data.append(Status.FIRST_APPROVED.value)
    data.append(Status.REJECTED.value)
    data.append(Status.CANCELLED.value)
    data.append(Status.SETTLED.value)
    return data


def validate_status_transition(original_status: Status | str, new_status: Status | str) -> Boolean2:
    """Validate the status transition for an expense.

    Checks if a transition from `original_status` to `new_status` is valid 
    based on predefined STATUS_TRANSITIONS.

    Args:
        original_status (Status | str): The original status of the expense.
        new_status (Status | str): The desired new status of the expense.

    Returns:
        Boolean2: A custom Boolean class with TRUE or FALSE indicating 
                  validity of the transition.

    Raises:
        ValueError: If `original_status` or `new_status` is invalid.
    """
    original_status = Status(original_status) if isinstance(
        original_status, str) else original_status
    new_status = Status(new_status) if isinstance(
        new_status, str) else new_status
    if new_status not in STATUS_TRANSITIONS[original_status]:
        return Boolean2.FALSE(f"Invalid status transition from {original_status.name} to {new_status.name}")
    return Boolean2.TRUE()


def get_approved_status(current_status: str, office_rc: Office, amount: float, request_approver_rc: User) -> tuple:
    """
        return (has_1st_approval, need_2nd_approval, approve_status)
    """
    # basic validate
    current_status = Status(current_status) if isinstance(current_status, str) else current_status
    current_status: Status

    has_1st_approval = (current_status == Status.FIRST_APPROVED)
    need_2nd_approval = False
    if current_status != Status.APPROVED:
        # check need 2nd approval or not
        second_approvers = get_second_approvers(office_rc, request_approver_rc)
        for rc in second_approvers:
            need_2nd_approval = (rc.min_approve_amount is None or amount >= rc.min_approve_amount)
            if need_2nd_approval:
                break

    # next status
    approve_status = Status.FIRST_APPROVED if (not has_1st_approval and need_2nd_approval) else Status.APPROVED
    return has_1st_approval, need_2nd_approval, approve_status
