from datetime import datetime as datetime_

from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import Group, GroupMenu, UserGroup
from core.utils.langUtils import isNotNullBlank, isNullBlank


def save(saveUsrID, currentGroupID, createNew, requestData, validate) -> Boolean2:
    now = datetime_.now()
    grpDtlFg: Group = requestData.get('grpDtlFg')
    usrFg: list[UserGroup] = requestData.get('usrFg')
    leavedUsrFg: list[UserGroup] = requestData.get('leavedUsrFg')
    scrFg: list[IkyGroupMenu] = requestData.get('scrFg')

    groupName = grpDtlFg.grp_nm.strip()
    if isNullBlank(groupName):
        return Boolean2(False, "Group Name is mandatory.")
    grpDtlFg.grp_nm = groupName

    if isNullBlank(currentGroupID) and isNullBlank(createNew):
        return Boolean2(False, "Save error, the id of the group to be modified was not found.")
    elif isNotNullBlank(currentGroupID):
        savedGroupRcs = Group.objects.filter(grp_nm__iexact=groupName).exclude(id=currentGroupID).first()
    else:
        savedGroupRcs = Group.objects.filter(grp_nm__iexact=groupName).first()
    if isNotNullBlank(savedGroupRcs):
        return Boolean2(False, "Group Name is unique, please check.")

    if isNotNullBlank(createNew):
        grpDtlFg.assignPrimaryID()

    groupID = grpDtlFg.id

    validate(usrFg, 'usrFg', 'usr_id', now, groupID)
    validate(scrFg, 'scrFg', 'menu_id', now, groupID)

    pytrn = IkTransaction(userID=saveUsrID)
    pytrn.add(grpDtlFg)
    pytrn.add(usrFg)
    pytrn.add(scrFg)
    b = pytrn.save()
    if not b.value:
        return Boolean2(False, b.dataStr)
    return Boolean2(True, groupID)
