'''
Description: User Management Manager
version: 
Author: XH.ikyo
Date: 2023-09-18 14:27:13
'''
import hashlib
import re

from django.db.models import F, Q, Subquery, Value
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.contrib.auth.hashers import make_password

from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import *
from core.utils.langUtils import isNotNullBlank, isNullBlank
from iktools import IkConfig


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
        usrRcs = usrRcs.filter(active=True)
    elif not isEnable and isDisable:
        usrRcs = usrRcs.filter(~Q(active=True))

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
    officeFg: list[UserOffice] = requestData.get('officeFg')

    if isNullBlank(currentUsrID) and createNew:
        usrDtlFg.ik_is_status_new()
        usrDtlFg.assignPrimaryID()
    currentUsrID = usrDtlFg.id

    username = usrDtlFg.usr_nm.strip()
    # check the user name is exists or not
    if isNullBlank(username):
        return Boolean2(False, 'Username is mandatory!')
    usrCheckerRcs = User.objects.filter(usr_nm__iexact=username)
    if len(usrCheckerRcs) > 1:
        return Boolean2(False, 'Duplicate user name [%s], please change (e.g. add suffix)' % username)

    if createNew and len(usrCheckerRcs) == 1:
        return Boolean2(False, 'Duplicate user name [%s], please change (e.g. add suffix)' % username)
    if usrDtlFg.ik_is_status_modified():
        currentUsrRc = User.objects.filter(id=currentUsrID).first()
        if isNullBlank(currentUsrRc):
            return Boolean2(False, 'This account has been deleted. Please check.')
        if len(usrCheckerRcs) == 1 and usrCheckerRcs.first().id != currentUsrID:
            return Boolean2(False, 'Duplicate user name [%s], please change (e.g. add suffix)' % username)

    # email
    email = usrDtlFg.email
    if isNotNullBlank(email) and not __isValidEmail(email):
        return Boolean2(False, "Email is incorrect!")

    # password
    newPsw = usrDtlFg.psw if isNotNullBlank(usrDtlFg.psw) else None
    if isNullBlank(newPsw) and createNew:
        return Boolean2(False, 'Password is mandatory!')
    if isNotNullBlank(newPsw):
        if len(newPsw) < 6:
            return Boolean2(False, 'The password\'s length should be equal to or greater than 6 characters!')
        password_encryption_method = IkConfig.getSystem('password_encryption_method').lower()
        if password_encryption_method == 'md5':
            newPsw = hashlib.md5(newPsw.encode("utf8")).hexdigest()
        elif password_encryption_method == 'pbkdf2':
            newPsw = make_password(newPsw)
        else:
            return Boolean2(False, "Unsupported password encryption method: [%s], please choose in [MD5/PBKDF2]" % password_encryption_method)

    if not usrDtlFg.active:
        usrDtlFg.active = False

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

    # user office
    officeRcs = []
    hasDefault = False
    allToBeDel = True
    for o in officeFg:
        if o.ik_is_status_delete():
            officeRcs.append(o)
            continue
        allToBeDel = False
        if hasDefault and o.is_default:
            return Boolean2(False, "User can only have one default office, please check.")
        if o.is_default:
            hasDefault = True

        if o.ik_is_status_new():
            o.usr_id = usrDtlFg.id
        officeRcs.append(o)
    if (isNotNullBlank(officeFg) and len(officeFg) > 0) and not allToBeDel and not hasDefault:
        return Boolean2(False, "Please set a default office.")
    # sort
    officeRcs.sort(key=lambda o: o.seq)
    seq = 0
    for o in officeRcs:
        if o.ik_is_status_delete():
            continue
        seq += 1
        if seq != o.seq:
            o.seq = seq
        if not o.ik_is_status_new():
            o.ik_set_status_modified()

    if createNew:
        usrDtlFg.psw = newPsw
    elif usrDtlFg.ik_is_status_modified():
        if isNotNullBlank(newPsw):
            usrDtlFg.psw = newPsw
        else:
            usrDtlFg.psw = oldPsw

    pytrn = IkTransaction(userID=saveUsrID)
    pytrn.add(usrDtlFg)
    pytrn.add(grpFg)
    pytrn.add(officeRcs)
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
