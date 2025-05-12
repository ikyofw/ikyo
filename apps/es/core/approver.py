"""Approver management
"""
from django.db.models import Q, Exists, OuterRef
from core.log.logger import logger
from core.core.lang import Boolean2
from ..models import Office, User, Approver, Office, User, UserGroup


class SecondApprover:
    """
    Represents a second approver in the approval process.

    Attributes:
        second_approver (User): The user who acts as the second approver.
        min_approve_amount (float): The minimum amount that requires a second approval.
    """
    def __init__(self, second_approver: User, min_approve_amount: float):
        """
        Initializes a SecondApprover instance.

        Args:
            second_approver (User): The user who acts as the second approver.
            min_approve_amount (float): The minimum amount that requires a second approval.
        """
        self.second_approver : User = second_approver
        self.min_approve_amount : float = min_approve_amount

def validate_approver(office: Office, claimer: User, request_approver: User, approver: User, approve_amount: float, is_first_approve: bool) -> Boolean2:
    """
    Validates whether a user has permission to approve an expense request.

    This method checks the validity of the approver based on the approval stage (first or second),
    the office, and the approval amount. Different checks are performed depending on whether 
    it is a first or second approval.

    Args:
        office (Office): The office where the approval is being processed.
        claimer (User): Claimer.
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
        approve_amount = 5000.0
        is_first_approve = True

        result = validate_expense_approver(office, request_approver, approver, approve_amount, is_first_approve)
        if result.value:
            print("Approval is valid.")
        else:
            print(f"Approval failed: {result.data}")
    """
    if is_first_approve:
        if request_approver.id == approver.id:
            # default approver
            all_office_approvers = get_office_first_approvers(office, claimer)
            for rc in all_office_approvers:
                if rc.id == approver.id:
                    return Boolean2.TRUE()
        else:
            # check approver's assistant
            all_assistants = get_approver_assistants(office, request_approver)
            for rc in all_assistants:
                if rc.id == approver.id:
                    return Boolean2.TRUE()
    else:
        # second approve
        second_approvers = get_second_approvers(office, request_approver)
        for rc in second_approvers:
            if rc.second_approver.id == approver.id:
                if (rc.min_approve_amount is not None and approve_amount < rc.min_approve_amount ):
                    return Boolean2.FALSE("The second approval amount must be equal to or greater than %f!" % (rc.min_approve_amount))
                else:
                    return Boolean2.TRUE()
    return Boolean2.FALSE("Permission deny!")


def get_office_first_approvers(office_rc: Office, claimer: User, activate_user_only: bool = True) -> list[User]:
    """
        return list[User], sorts by User.usr_nm
    """
    approvers : list[User] = [] 
    approver_ids : list [int] = []
    # found_specified_claimer = False
    if claimer is not None:
        # 1) check the specified claimer first
        for rc in Approver.objects.filter(office=office_rc, enable=True, claimer=claimer):
            # found_specified_claimer = True
            if rc.approver is not None:
                if (not activate_user_only or rc.approver.active is True) and rc.approver.id not in approver_ids:
                    approvers.append(rc.approver)
                    approver_ids.append(rc.id)
            elif rc.approver_grp is not None:
                for ug_rc in UserGroup.objects.filter(grp = rc.approver_grp):
                    if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in approver_ids:
                        approvers.append(ug_rc.usr)
                        approver_ids.append(ug_rc.usr.id)
        # 2) check the claimer group
        for rc in Approver.objects.filter(office=office_rc, enable=True, claimer_grp__isnull=False):
            # check the claimer exists in the claimer_grp or not
            claimer_exists_in_claimer_grp = False
            for ug_rc in UserGroup.objects.filter(grp = rc.claimer_grp):
                if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id == claimer.id:
                    claimer_exists_in_claimer_grp = True
                    break
            if claimer_exists_in_claimer_grp:
                # found_specified_claimer = True
                if rc.approver is not None:
                    if (not activate_user_only or rc.approver.active is True) and rc.approver.id not in approver_ids:
                        approvers.append(rc.approver)
                        approver_ids.append(rc.id)
                elif rc.approver_grp is not None:
                    for ug_rc in UserGroup.objects.filter(grp = rc.approver_grp):
                        if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in approver_ids:
                            approvers.append(ug_rc.usr)
                            approver_ids.append(ug_rc.usr.id)
    # 3) check the generic approve
    # if not found_specified_claimer:
    for rc in Approver.objects.filter(office=office_rc, enable=True, claimer__isnull=True, claimer_grp__isnull=True):
        if rc.approver is not None:
            if (not activate_user_only or rc.approver.active is True) and rc.approver.id not in approver_ids:
                approvers.append(rc.approver)
                approver_ids.append(rc.id)
        elif rc.approver_grp is not None:
            for ug_rc in UserGroup.objects.filter(grp = rc.approver_grp):
                if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in approver_ids:
                    approvers.append(ug_rc.usr)
                    approver_ids.append(ug_rc.usr.id)
    # sorts by User.usr_nm
    approvers = sorted(approvers, key=lambda user: user.usr_nm)
    return approvers


def get_approver_assistants(office_rc: Office, approver_rc: User, activate_user_only: bool = True) -> list[User]:
    assistant_approvers : list[User] = [] 
    assistant_approver_ids : list [int] = []
    # 1 validate the approver
    for approver_define_rc in Approver.objects.filter(office=office_rc, enable=True, approver=approver_rc):
        if approver_define_rc.approver_assistant is not None:
            if (not activate_user_only or approver_define_rc.approver_assistant.active is True) \
                and approver_define_rc.approver_assistant.id not in assistant_approver_ids:
                assistant_approvers.append(approver_define_rc.approver_assistant)
                assistant_approver_ids.append(approver_define_rc.approver_assistant.id)
        if approver_define_rc.approver_assistant_grp is not None:
            for ug_rc in UserGroup.objects.filter(grp = approver_define_rc.approver_assistant_grp):
                if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in assistant_approver_ids:
                    assistant_approvers.append(ug_rc.usr)
                    assistant_approver_ids.append(ug_rc.usr.id)
    # 2 validate the approver group
    for approver_define_rc in Approver.objects.filter(office=office_rc, enable=True, approver_grp__isnull=False):
        # check the user_rc exists in approver_grp or not
        is_user_exists_in_approver_grp = False
        for ug_rc in UserGroup.objects.filter(grp = approver_define_rc.approver_grp):
            if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id == approver_rc.id:
                is_user_exists_in_approver_grp = True
                break
        if is_user_exists_in_approver_grp:
            # add assistants
            if approver_define_rc.approver_assistant is not None:
                if (not activate_user_only or approver_define_rc.approver_assistant.active is True) \
                    and approver_define_rc.approver_assistant.id not in assistant_approver_ids:
                    assistant_approvers.append(approver_define_rc.approver_assistant)
                    assistant_approver_ids.append(approver_define_rc.approver_assistant.id)
            if approver_define_rc.approver_assistant_grp is not None:
                for ug_rc in UserGroup.objects.filter(grp = approver_define_rc.approver_assistant_grp):
                    if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in assistant_approver_ids:
                        assistant_approvers.append(ug_rc.usr)
                        assistant_approver_ids.append(ug_rc.usr.id)
    # sorts by User.usr_nm
    assistant_approvers = sorted(assistant_approvers, key=lambda user: user.usr_nm)
    return assistant_approvers


def get_second_approvers(office_rc: Office, approver_rc: User, activate_user_only: bool = True) -> list[SecondApprover]:
    second_approvers : list[SecondApprover] = [] 
    second_approver_ids : list [int] = []
    # 1 validate the approver
    for approver_define_rc in Approver.objects.filter(office=office_rc, enable=True, approver=approver_rc):
        if approver_define_rc.approver2 is not None:
            if (not activate_user_only or approver_define_rc.approver2.active is True) \
                and approver_define_rc.approver2.id not in second_approver_ids:
                second_approvers.append(SecondApprover(approver_define_rc.approver2, approver_define_rc.approver2_min_amount))
                second_approver_ids.append(approver_define_rc.approver2.id)
        if approver_define_rc.approver2_grp is not None:
            for ug_rc in UserGroup.objects.filter(grp = approver_define_rc.approver2_grp):
                if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in second_approver_ids:
                    second_approvers.append(SecondApprover(ug_rc.usr, approver_define_rc.approver2_min_amount))
                    second_approver_ids.append(ug_rc.usr.id)
    # 2 validate the approver group
    for approver_define_rc in Approver.objects.filter(office=office_rc, enable=True, approver_grp__isnull=False):
        # check the user_rc exists in approver_grp or not
        is_user_exists_in_approver_grp = False
        for ug_rc in UserGroup.objects.filter(grp = approver_define_rc.approver_grp):
            if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id == approver_rc.id:
                is_user_exists_in_approver_grp = True
                break
        if is_user_exists_in_approver_grp:
            # add 2nd approver
            if approver_define_rc.approver2 is not None:
                if (not activate_user_only or approver_define_rc.approver2.active is True) \
                    and approver_define_rc.approver2.id not in second_approver_ids:
                    second_approvers.append(SecondApprover(approver_define_rc.approver2, approver_define_rc.approver2_min_amount))
                    second_approver_ids.append(approver_define_rc.approver2.id)
            if approver_define_rc.approver2_grp is not None:
                for ug_rc in UserGroup.objects.filter(grp = approver_define_rc.approver2_grp):
                    if (not activate_user_only or ug_rc.usr.active is True) and ug_rc.usr.id not in second_approver_ids:
                        second_approvers.append(SecondApprover(ug_rc.usr, approver_define_rc.approver2_min_amount))
                        second_approver_ids.append(ug_rc.usr.id)
    # sorts by User.usr_nm
    second_approvers = sorted(second_approvers, key=lambda second_approver: second_approver.second_approver.usr_nm)
    return second_approvers


def get_accessible_approvers(office_rc: Office, user_rc: User, activate_user_only: bool = True) -> list[User]:
    approvers : list[User] = [] 
    approver_ids = [int]
    # approver assistant and 2nd approver
    assistant_ug_subquery = UserGroup.objects.filter(grp=OuterRef('approver_assistant_grp'), usr=user_rc)
    approver2_ug_subquery = UserGroup.objects.filter(grp=OuterRef('approver2_grp'), usr=user_rc)

    approver_setting_rcs = Approver.objects.filter(office=office_rc, enable=True)
    approver_setting_rcs = approver_setting_rcs.filter(Q(Q(approver_assistant=user_rc) | (Q(approver_assistant_grp__isnull=False) & Exists(assistant_ug_subquery)))
                                                       | Q(Q(approver2=user_rc) | (Q(approver2_grp__isnull=False) & Exists(approver2_ug_subquery))))
    for setting_rc in approver_setting_rcs:
        if setting_rc.approver is not None and setting_rc.approver.id not in approver_ids:
            approvers.append(setting_rc.approver)
            approver_ids.append(setting_rc.approver.id)
        if setting_rc.approver_grp is not None:
            for ug_rc in UserGroup.objects.filter(grp=setting_rc.approver_grp):
                if ug_rc.usr is not None and ug_rc.usr.id not in approver_ids:
                    approvers.append(ug_rc.usr)
                    approver_ids.append(ug_rc.usr.id)
    # sorts by User.usr_nm
    second_approvers = sorted(approvers, key=lambda approver: approver.usr_nm)
    return second_approvers


def is_need_second_approval(office_rc: Office, approver_rc: User, claim_amount: float) -> bool:
    second_approvers = get_second_approvers(office_rc, approver_rc)
    for rc in second_approvers:
        if rc.min_approve_amount is None or claim_amount >= rc.min_approve_amount:
            return True
    return False
