'''
Description: Inbox Manager
version: 
Author: YL
Date: 2024-04-26 11:53:36
'''
import logging
import traceback

import core.user.userManager as UserManager
from core.core.exception import IkException, IkValidateException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import IkInbox, IkInboxPrm

logger = logging.getLogger('ikyo')

ACTION_COMMAND = "__CMD"
PARAMETER_FROM_MENU = "fromMenu"
MENU_INBOX = "Inbox"


def getInboxStatus() -> list:
    data = [{
        "value": IkInbox.STATUS_NEW,
        "display": IkInbox.STATUS_NEW
    }, {
        "value": IkInbox.STATUS_READ,
        "display": IkInbox.STATUS_READ
    }]
    return data


def getInboxModules() -> list:
    data = list(IkInbox.objects.all().values_list("module", flat=True).distinct())
    return data


def markRead(operatorID, inboxIds) -> Boolean2:
    if not isinstance(inboxIds, list):
        inboxIds = [int(inboxIds)]
    return updateStatus(operatorID=operatorID, inboxIds=inboxIds, status=IkInbox.STATUS_READ)


def markUnread(operatorID, inboxIds) -> Boolean2:
    if not isinstance(inboxIds, list):
        inboxIds = [int(inboxIds)]
    return updateStatus(operatorID=operatorID, inboxIds=inboxIds, status=IkInbox.STATUS_NEW)


def markDeleted(operatorID, inboxIds) -> Boolean2:
    if not isinstance(inboxIds, list):
        inboxIds = [int(inboxIds)]
    return updateStatus(operatorID=operatorID, inboxIds=inboxIds, status=IkInbox.STATUS_DELETED)


def updateStatus(operatorID, inboxIds, status) -> Boolean2:
    '''
        operatorID (int): Current User ID
        inboxIds (list): inbox id list
        status (str): inbox status

        Update inbox messages
        Return True if success.
    '''
    operator = UserManager.getUserName(userID=operatorID)
    if operator is None:
        raise IkValidateException('Operator [%s] does not exist.' % operatorID)
    inboxDBRcs = []
    for inboxID in inboxIds:
        inboxRc = IkInbox.objects.filter(id=inboxID).first()
        if inboxRc is None:
            raise IkValidateException('Message [%s] does not exist.' % inboxID)
        elif inboxRc.owner_id != operatorID:
            logger.error("[%s] going to change inbox message [%s]'s status from [%s] to [%s]. Permission Deny: Message owner is [%s]." %
                         (operator, inboxRc.sts, status, inboxRc.owner_id))
            raise IkValidateException('Permission deny.')
        if inboxRc.sts == status:
            return Boolean2(True)  # no need to change
        # if status == IkInbox.STATUS_DELETED:  # delete database
        #     inboxRc.ik_set_status_delete()
        # else:  # update
        inboxRc.sts = status
        inboxRc.ik_set_status_modified()
        inboxDBRcs.append(inboxRc)
    # save to database
    ptrn = IkTransaction(userID=operatorID)
    ptrn.add(inboxDBRcs)
    b = ptrn.save()
    if not b.value:
        raise IkValidateException(b.dataStr)
    return Boolean2(True)


def getLinkParameters(inboxID) -> dict:
    prmRcs = IkInboxPrm.objects.filter(inbox__id=inboxID).order_by("id")
    map = {}
    for prm in prmRcs:
        map.update({prm.k: prm.v})
    return map
