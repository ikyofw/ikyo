"""Access control. E.g. approvable, rejectable
"""
from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from django.db.models.manager import Manager

from core.log.logger import logger
from core.models import Office, User, UserGroup

from ..models import (Accounting, CashAdvancement, Expense, Payee,
                      PettyCashExpenseAdmin, UserCashAdvancementPermission,
                      UserExpensePermission, UserRole)
from . import approver as ApproverManager
from .setting import is_accounting_rejectable
from .status import Status, get_approved_status, validate_status_transition


def is_office_admin(user_rc: User, office_rc: Office) -> bool:
    return __is_es_admin(user_rc, office_rc)


def is_cancelable(status: str, claimer_id: int, operator_id: int) -> bool:
    """Check the operator can cancel a expense or not by status.

    Only allow expense's owner can cancel a submitted expense.

    Args:
        status (str: Status): Expense's current status
        claimer_id (int): Expense claimer's ID
        operatorID (int): Operator's ID

    Returns:
        True if cancellable, False otherwise.

    """
    validate_status_result = validate_status_transition(status, Status.CANCELLED)
    if not validate_status_result.value:
        return False
    return claimer_id == operator_id


def is_approverable(operator_rc: User, current_status: str, payee_rc: Payee, amount: float, request_approver_rc: User) -> bool:
    """Check the operator can cancel a expense or not.

    Only allow expense's owner can cancel a submitted expense.

    Args:
        operator_rc (User): Operator.
        current_status (str: Status): Expense's current status.
        payee_rc (Payee): Payee.
        request_approver_rc (User): Request approver.
        amount (float): Payment amount.
        first_approver (User): The first approver.

    Returns:
        True if approveable, False otherwise.

    """
    log_header = 'is_approverable'
    # basic validate
    current_status = Status(current_status) if isinstance(current_status, str) else current_status
    current_status: Status
    office_rc = payee_rc.office

    has_1st_approval, need_2nd_approval, approve_status = get_approved_status(current_status, office_rc, amount, request_approver_rc)

    # validate next status
    validate_status_result = validate_status_transition(current_status, approve_status)
    if not validate_status_result.value:
        logger.debug("%s %s cannot change the status from %s to %s." % (log_header, operator_rc.usr_nm, current_status.value, approve_status.value))
        return False

    # validate approver
    if has_1st_approval:
        # the 2nd approval
        for send_approver_rc in ApproverManager.get_second_approvers(office_rc, request_approver_rc):
            if operator_rc.id == send_approver_rc.second_approver.id:
                return True
        return False
    else:
        # the first approval or final approval
        if operator_rc.id == request_approver_rc.id:
            # allow requester approver to approve
            return True
        else:
            for assistant_approver_rc in ApproverManager.get_approver_assistants(office_rc, request_approver_rc):
                if assistant_approver_rc.id == operator_rc.id:
                    return True
            return False


def is_rejectable(operator_rc: User, current_status: str, payee_rc: Payee, amount: float, request_approver_rc: User,
                  is_petty_expense: bool = False, has_petty_expense_confirm: bool = False) -> bool:
    if is_approverable(operator_rc, current_status, payee_rc, amount, request_approver_rc):
        return True
    if is_accounting_rejectable():
        return is_settlable(operator_rc, current_status, payee_rc, amount, request_approver_rc, is_petty_expense, has_petty_expense_confirm)
    return False


def is_settlable(operator_rc: User, current_status: str, payee_rc: Payee, amount: float, request_approver_rc: User,
                 is_petty_expense: bool = False, has_petty_expense_confirm: bool = False) -> bool:
    office_rc = payee_rc.office
    log_header = 'is_settlable operator=%s office=%s' % (operator_rc.usr_nm, office_rc.code)

    has_1st_approval, need_2nd_approval, approve_status = get_approved_status(current_status, office_rc, amount, request_approver_rc)
    if has_1st_approval:
        # the 2nd approval
        second_approver = []
        for second_approver_rc in ApproverManager.get_second_approvers(office_rc, request_approver_rc):
            second_approver.append(second_approver_rc.second_approver.id)
        if operator_rc.id not in second_approver:
            return False
    elif need_2nd_approval:
        logger.debug("%s permission deny: need 2nd approval before settle." % (log_header))
        return False

    # basic validate
    current_status = Status(current_status) if isinstance(current_status, str) else current_status
    current_status: Status

    # validate the accounting setting
    accounting_setting_rc = Accounting.objects.filter(office=office_rc, usr=operator_rc).first()
    if accounting_setting_rc is None:
        logger.debug("%s permission deny: accounting record doesn't exist." % (log_header))
        return False

    # validate next status
    validate_status_result = validate_status_transition(current_status, Status.SETTLED)
    if not validate_status_result.value:
        logger.debug("%s cannot change the status from %s to %s" % (log_header, current_status.value, Status.SETTLED.value))
        return False

    # validate the petty expense
    if is_petty_expense is True and has_petty_expense_confirm is False:
        logger.debug("%s petty expense should be confirmed first." % (log_header))
        return False

    # if the status is submitted and the operator is approver and account, then user can pay directly
    if current_status == Status.SUBMITTED:
        if not is_approverable(operator_rc, current_status, payee_rc, amount, request_approver_rc):
            logger.debug("%s cannot change the status from %s to %s directly" % (log_header, current_status.value, Status.SETTLED.value))
            return False
    return True


def can_revert_settled_payment(operator_rc: User, current_status: str, office_rc: Office) -> bool:
    # basic validate
    current_status = Status(current_status) if isinstance(current_status, str) else current_status
    current_status: Status

    if current_status != Status.SETTLED:
        return False

    # validate next status
    validate_status_result = validate_status_transition(current_status, Status.SUBMITTED)
    if not validate_status_result.value:
        return False
    return __is_es_admin(operator_rc, office_rc)


def is_approved_petty_expense_confirmable(operator_rc: User, current_status: str, office_rc: Office, claim_amount: float) -> bool:
    """Check the operator can submit a petty cash expense or not

    Only allow expense's owner to cancel a submitted expense.

    Args:
        status (str: Status): Expense's status.
        payeeID (int): Payee's ID.
        operatorID (int): Operator's ID.

    Returns:
        True if submittable, False otherwise.

    """
    current_status = Status(current_status) if isinstance(current_status, str) else current_status
    current_status: Status

    if current_status != Status.APPROVED:
        return False

    petty_setting_rc = PettyCashExpenseAdmin.objects.filter(office=office_rc, admin=operator_rc, enable=True).first()
    if petty_setting_rc is None:
        return False
    return claim_amount <= petty_setting_rc.max_amt


def is_es_admin(user_rc: User, office_rc: Office = None) -> bool:
    return __is_es_admin(user_rc, office_rc)


def __is_es_admin(user_rc: User, office_rc: Office = None) -> bool:
    """
    Check if the given user is an office admin.

    Args:
        user_rc (User): The user record to check.
        office_rc (Office, optional): The office record to validate against. Defaults to None.

    Returns:
        bool: True if the user is an office admin, otherwise False.

    Raises:
        IkException: If user_rc is None.
    """
    if user_rc is None:
        raise IkException("Parameter [user_rc] is mandatory!")
    # Validate if the user is an admin for the specified office
    if office_rc is not None:
        oa_rc = UserRole.objects.filter(Q(Q(usr_id=user_rc.id) | Exists(UserGroup.objects.filter(grp_id=OuterRef('usr_grp_id'))))
                                        & Q(office=office_rc)
                                        & Q(role=UserRole.ROLE_ADMIN)
                                        & Q(enable=True)
                                        & Q(target_usr__isnull=True)
                                        & Q(target_usr_grp__isnull=True)).first()
        if oa_rc is not None:
            return True
    # Validate if the user is a global ES admin
    oa_rc = UserRole.objects.filter(Q(Q(usr_id=user_rc.id) | Exists(UserGroup.objects.filter(grp_id=OuterRef('usr_grp_id'))))
                                    & Q(office__isnull=True)
                                    & Q(role=UserRole.ROLE_ADMIN)
                                    & Q(enable=True)
                                    & Q(target_usr__isnull=True)
                                    & Q(target_usr_grp__isnull=True)).first()
    return oa_rc is not None


def add_query_filter(model_objects: QuerySet, query_user_rc: User, query_parameters: dict = None) -> QuerySet:
    """
    Add filter conditions to the Expense and Cash Advancement query. This is very important for ACL check!

    Args:
        model_objects (Manager/QuerySet): Django model objects queryset
        query_user_rc (User): The user object for the current query
        query_parameters (dict): The query parameters. It can be None.

    Returns:
        The filtered queryset.

    Raise:
        Exception if the model_objects is not a QuerySet or an instance of Expense model's objects or CashAdvancement model's objects.

    Example:
        queryset = Expense.objects.all()
        queryset = add_query_filter(queryset, query_user_rc, query_parameters)
        queryset = queryset.filter(...).order_by(...)

    """
    if isinstance(model_objects, Manager):
        model_objects = model_objects.all()
    if not isinstance(model_objects, QuerySet):
        raise Exception("model_objects is not a QuerySet")
    # Check if the model_objects is an instance of Expense model's objects
    if model_objects.model != Expense and model_objects.model != CashAdvancement:
        raise Exception("model_objects is not an instance of Expense model's objects or CashAdvancement model's objects")
    if query_user_rc is None:
        raise Exception("query_user_rc is mandatory.")
    if query_parameters is None:
        query_parameters = {}

    query_user_id = query_user_rc.id

    if model_objects.model == Expense:
        return model_objects.filter(id__in=UserExpensePermission.objects.filter(usr_id=query_user_id).values('expense_id')
                                    ).annotate(
                                        acl=Subquery(
                                            UserExpensePermission.objects.filter(
                                                usr_id=query_user_id,
                                                expense_id=OuterRef('id')
                                            ).values('acl')[:1]
                                        )
        )
    elif model_objects.model == CashAdvancement:
        return model_objects.filter(id__in=UserCashAdvancementPermission.objects.filter(usr_id=query_user_id).values('ca_id')
                                    ).annotate(
                                        acl=Subquery(
                                            UserCashAdvancementPermission.objects.filter(
                                                usr_id=query_user_id,
                                                ca_id=OuterRef('id')
                                            ).values('acl')[:1]
                                        )
        )
    else:
        raise Exception("model_objects is not an instance of Expense model's objects or CashAdvancement model's objects")
