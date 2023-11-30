'''
Description: User Management Manager
version: 
Author: XH.ikyo
Date: 2023-09-18 14:27:13
'''
import re
import hashlib
from django.db.models import Q, F, Value, Subquery
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from datetime import datetime as datetime_

from core.utils.langUtils import isNullBlank, isNotNullBlank
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction

from core.models import *


def getUsrList(schItems: dict) -> QuerySet:
    if isNullBlank(schItems):
        isEnable = True
        isDisable = False
        schKey = ''
    else:
        isEnable = schItems['schEnb'].lower() == 'true'
        isDisable = schItems['schDsb'].lower() == 'true'
        schKey = schItems['schKey'].strip()

    usrRcs = User.objects.all()
    if isEnable and not isDisable:
        usrRcs = usrRcs.filter(enable='Y')
    elif not isEnable and isDisable:
        usrRcs = usrRcs.filter(Q(enable__isnull=True) | ~Q(enable='Y'))

    if isNotNullBlank(schKey):
        schFilter = Q(usr_nm__icontains=schKey) | Q(rmk__icontains=schKey)
        groupNms = UserGroup.objects.filter(usr_id=F('usr')).values('usr_id').annotate(groups=Concat('grp__grp_nm', Value(', '))).values('groups')

        usrRcs = usrRcs.annotate(groups=Subquery(groupNms.filter(usr_id=F('id')).values('groups')[:1]))
        schFilter |= Q(groups__icontains=schKey)

        usrRcs = usrRcs.filter(schFilter)
    usrRcs = usrRcs.order_by('usr_nm')

    return usrRcs


def save(saveUsrID: int, currentUsrID, createNew, requestData, oldPsw) -> Boolean2:
    usrDtlFg: User = requestData.get('usrDtlFg')
    grpFg: list[UserGroup] = requestData.get('grpFg')

    if isNullBlank(currentUsrID) and createNew:
        usrDtlFg.ik_is_status_new()
        usrDtlFg.assignPrimaryID()
    currentUsrID = usrDtlFg.id

    username = usrDtlFg.usr_nm.strip()
    # check the user name is exists or not
    if isNullBlank(username):
        return Boolean2(False, 'Username is mandatory!')
    usrCheckerRc = User.objects.filter(usr_nm__iexact=username).first()
    if createNew and isNotNullBlank(usrCheckerRc):
        return Boolean2(False, 'This account is exists. Please check.')
    elif usrDtlFg.ik_is_status_modified() and isNullBlank(usrCheckerRc):
        return Boolean2(False, 'This account has been deleted. Please check.')
    elif usrDtlFg.ik_is_status_modified() and usrDtlFg.id != usrCheckerRc.id:
        return Boolean2(False, 'This account is exists. Please check.')

    # email
    email = usrDtlFg.email
    if isNotNullBlank(email) and not __isValidEmail(email):
        return Boolean2(False, "Email is incorrect!")

    # password
    newPsw = usrDtlFg.psw
    # if isNullBlank(newPsw) or len(newPsw) < 6:
    #     return Boolean2(False, 'The password\'s length should be equal to or greater than 6 characters!')

    if usrDtlFg.enable != 'Y':
        usrDtlFg.enable = 'N'

    # user groups
    grpRcs, groupIDs = [], []
    for i in grpFg:
        groupID = i.grp_id
        if isNullBlank(groupID):
            if i.ik_is_status_new():
                i.ik_set_status_retrieve()
            if i.ik_is_status_modified():
                i.ik_set_status_delete()
        elif not i.ik_is_status_delete():
            if groupID in groupIDs:
                if i.ik_is_status_new():
                    i.ik_set_status_retrieve()
                if i.ik_is_status_modified():
                    i.ik_set_status_delete()
            else:
                groupIDs.append(groupID)
    for j in grpFg:
        if j.ik_is_status_new():
            j.usr_id = usrDtlFg.id
        if not j.ik_is_status_retrieve():
            grpRcs.append(j)

    if createNew:
        usrDtlFg.psw = __getPswMD5(newPsw)
    elif usrDtlFg.ik_is_status_modified():
        if isNotNullBlank(newPsw):
            usrDtlFg.psw = __getPswMD5(newPsw)
        else:
            usrDtlFg.psw = __getPswMD5(oldPsw)

    pytrn = IkTransaction(userID=saveUsrID)
    pytrn.add(usrDtlFg)
    pytrn.add(grpFg)
    b = pytrn.save()
    if not b.value:
        return Boolean2(False, b.dataStr)
    return Boolean2(True, currentUsrID)


def __isValidEmail(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def __getPswMD5(psw):
    md5 = hashlib.md5()
    md5.update(psw.encode('utf-8'))
    return md5.hexdigest()
