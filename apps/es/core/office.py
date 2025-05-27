"""Office management
"""
from django.db.models import Exists, OuterRef, Q

from core.core.exception import IkException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.log.logger import logger
from core.models import Office, User, UserGroup, UserOffice

from ..models import (Accounting, Approver, PettyCashExpenseAdmin, UserRole,
                      UserWorkOffice)


def get_user_offices(user: User, contains_acl_offices: bool = False) -> list[Office]:
    """
    Retrieves a list of offices associated with a given user.

    This method uses a subquery to find all offices where the user has an entry in the `UserOffice` table. 
    The results are filtered and ordered by the `code` field.

    Args:
        user (User): The user whose associated offices are to be retrieved.
        contains_acl_offices (bool, optional): If True, only offices with an entry in the `UserOffice` table and other accessable offices (Approver, Accounting, PettyCashExpenseAdmin, UserRole, etc)
                                                are included in the result. Defaults to True.

    Returns:
        list[Office]: A list of `Office` objects associated with the user, ordered by their `code`.

    Example:
        user = User.objects.get(id=10)
        offices = get_user_offices(user)
        for office in offices:
            print(office.name)
    """
    subquery = UserOffice.objects.filter(
        office_id=OuterRef('id'),
        usr=user
    )
    if not contains_acl_offices:
        return Office.objects.annotate(
            exists_user_office=Exists(subquery)).filter(exists_user_office=True).order_by('code')

    office_ids = list(Office.objects.annotate(
        exists_user_office=Exists(subquery)).filter(exists_user_office=True).values_list('id', flat=True))
    user_grp_ids = UserGroup.objects.filter(usr=user).values_list('grp_id', flat=True)
    # 1. Approver
    additional_office_ids = Approver.objects.filter(
        Q(approver=user)
        | Q(approver_grp_id__in=user_grp_ids)
        | Q(approver_assistant=user)
        | Q(approver_assistant_grp_id__in=user_grp_ids)
        | Q(approver2=user)
        | Q(approver2_grp_id__in=user_grp_ids),
        enable=True
    ).exclude(office_id__in=office_ids).values_list('office_id', flat=True).distinct()
    office_ids.extend(list(additional_office_ids))

    # 2. Accounting
    additional_office_ids = Accounting.objects.filter(usr=user).exclude(office_id__in=office_ids).values_list('office_id', flat=True).distinct()
    office_ids.extend(list(additional_office_ids))

    # 3. PettyCashExpenseAdmin
    additional_office_ids = PettyCashExpenseAdmin.objects.filter(enable=True, admin=user).exclude(office_id__in=office_ids).values_list('office_id', flat=True).distinct()
    office_ids.extend(list(additional_office_ids))

    # 4. UserRole
    additional_office_ids = UserRole.objects.filter(Q(usr=user) | Q(usr_grp_id__in=user_grp_ids), enable=True).exclude(
        office_id__in=office_ids).values_list('office_id', flat=True).distinct()
    office_ids.extend(list(additional_office_ids))

    # sort by office code
    return Office.objects.filter(id__in=office_ids).order_by('code')


def update_user_work_office(office: Office, user: User) -> Boolean2:
    """
    Updates or creates the work office for a given user.

    If the user already has a work office assigned and it matches the provided office,
    no changes are made. Otherwise, the work office is updated or a new association
    is created. The changes are committed using the `IkTransaction` mechanism.

    Args:
        office (Office): The office to be assigned to the user.
        user (User): The user whose work office is being updated.

    Returns:
        Boolean2: A Boolean2 object representing the success of the operation.
                  - Boolean2.TRUE() if no changes were required.
                  - A result from the `IkTransaction.save()` method otherwise.

    Example:
        office = Office.objects.get(id=1)
        user = User.objects.get(id=10)
        result = update_user_work_office(office, user)
        if result.value:
            print("User work office updated successfully")
        else:
            print("Failed to update user work office:", result.data)
    """
    uwoRc = UserWorkOffice.objects.filter(usr=user).first()
    isNew = False
    if uwoRc is not None:
        if uwoRc.office.id == office.id:
            # no change
            return Boolean2.TRUE()
        uwoRc.office = office
    else:
        isNew = True
        uwoRc = UserWorkOffice(usr=user, office=office)
    trn = IkTransaction()
    if isNew:
        trn.add(uwoRc)
    else:
        trn.modify(uwoRc)
    return trn.save()


def get_user_work_office(user: User) -> Office:
    """
    Retrieves the work office for a given user.

    The method follows a two-step process:
      1. Checks if there is an entry in `UserWorkOffice` for the user.
      2. If not found, it queries `UserOffice` to get the default office or 
         the first available office based on sequence and ID.

    If a valid office is found in step 2 but not in step 1, it updates the 
    `UserWorkOffice` table using the `update_user_work_office` method.

    Args:
        user (User): The user whose work office is to be retrieved.

    Returns:
        Office: The user's associated work office, or None if no office is found.

    Raises:
        Exception: Logs an error if the `update_user_work_office` operation fails.

    Example:
        user = User.objects.get(id=10)
        office = get_user_work_office(user)
        if office:
            print(f"User work office: {office.name}")
        else:
            print("No work office found for the user")
    """
    # setp 1
    rc = UserWorkOffice.objects.filter(usr=user).first()
    if rc is not None:
        return rc.office
    # setp 2
    rc = UserOffice.objects.filter(usr=user, is_default=True).first()
    if rc is None:
        rc = UserOffice.objects.filter(usr=user).order_by('seq', 'id').first()
    if rc is None:
        raise IkException("Please set the work office first.")
    else:
        b = update_user_work_office(rc.office, user)
        if not b.value:
            logger.error(b.data)
        return rc.office


def validate_user_office(office: Office, user: User) -> bool:
    """
    Validates whether a given user is associated with a specific office.

    This method checks the `UserOffice` model to determine if there is a valid
    association between the provided `user` and `office`.

    Args:
        office (Office): The office to validate against.
        user (User): The user to validate.

    Returns:
        bool: True if the user is associated with the office, otherwise False.

    Example:
        office = Office.objects.get(id=1)
        user = User.objects.get(id=10)
        is_valid = validate_user_office(office, user)
        if is_valid:
            print("The user is associated with the office.")
        else:
            print("No association found between the user and office.")
    """
    return UserOffice.objects.filter(usr=user, office=office).first() is not None


def get_office_by_id(office_id: int) -> Office:
    """Get office orecord.

        Args:
        office_id (int): User id.

    Returns:
        Office record if found, None otherwise.
    """
    return Office.objects.filter(id=office_id).first()
