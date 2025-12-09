import logging
from datetime import datetime

import core.user.user_manager as UserManager
from core.core.exception import IkValidateException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import IkInbox, IkInboxPrm
from core.utils.lang_utils import isNullBlank

logger = logging.getLogger('ikyo')

ACTION_COMMAND = "__CMD"
PARAMETER_FROM_MENU = "fromMenu"
MENU_INBOX = "Inbox"


def mark_read(operator_id: int, inbox_ids: int | list) -> Boolean2:
    if not isinstance(inbox_ids, list):
        inbox_ids = [int(inbox_ids)]
    return update_status(operator_id=operator_id, inbox_ids=inbox_ids, status=IkInbox.STATUS_READ)


def mark_unread(operator_id: int, inbox_ids: int | list) -> Boolean2:
    if not isinstance(inbox_ids, list):
        inbox_ids = [int(inbox_ids)]
    return update_status(operator_id=operator_id, inbox_ids=inbox_ids, status=IkInbox.STATUS_NEW)


def mark_completed(operator_id: int, inbox_ids: int | list) -> Boolean2:
    if not isinstance(inbox_ids, list):
        inbox_ids = [int(inbox_ids)]
    return update_status(operator_id=operator_id, inbox_ids=inbox_ids, status=IkInbox.STATUS_COMPLETED)


def mark_deleted(operator_id: int, inbox_ids: int | list) -> Boolean2:
    if not isinstance(inbox_ids, list):
        inbox_ids = [int(inbox_ids)]
    return update_status(operator_id=operator_id, inbox_ids=inbox_ids, status=IkInbox.STATUS_DELETED)


def update_status(operator_id: int, inbox_ids: list, status: str) -> Boolean2:
    '''
        operator_id (int): Current User ID
        inbox_ids (list): inbox id list
        status (str): inbox status

        Update inbox messages
        Return True if success.
    '''
    operator = UserManager.getUserName(userID=operator_id)
    if operator is None:
        raise IkValidateException('Operator [%s] does not exist.' % operator_id)
    inbox_rcs = []
    for inbox_id in inbox_ids:
        inbox_rc = IkInbox.objects.filter(id=inbox_id).first()
        if inbox_rc is None:
            raise IkValidateException('Message [%s] does not exist.' % inbox_id)
        elif inbox_rc.owner_id != operator_id:
            logger.error("[%s] going to change inbox message [%s]'s status from [%s] to [%s]. Permission Deny: Message owner is [%s]." %
                         (operator, inbox_rc.sts, status, inbox_rc.owner_id))
            raise IkValidateException('Permission deny.')
        if inbox_rc.sts == status:
            continue  # no need to change
        if status == IkInbox.STATUS_DELETED:  # delete database
            inbox_rc.ik_set_status_delete()
        else:  # update
            inbox_rc.sts = status
            inbox_rc.ik_set_status_modified()
        inbox_rcs.append(inbox_rc)
    # save to database
    ptrn = IkTransaction(userID=operator_id)
    ptrn.add(inbox_rcs)
    return ptrn.save()


def get_link_params(inbox_id: int) -> dict:
    link_prm_rcs = IkInboxPrm.objects.filter(inbox__id=inbox_id).order_by("id")
    map = {}
    for prm in link_prm_rcs:
        map.update({prm.k: prm.v})
    return map


def send(sender_id: int, receiver_ids: int | list, module: str, summary: str, link_params: dict = None) -> list:
    '''
        receiverIDs: user id list
        return inbox ID list if success, else return None.
    '''
    # validation
    if sender_id is None:
        raise IkValidateException('Parameter [senderID] is mandatory!')
    sender = UserManager.getUserName(userID=sender_id)
    if sender is None:
        raise IkValidateException('Sender [%s] does not exist.' % sender_id)
    if isNullBlank(receiver_ids):
        raise IkValidateException('Parameter [receiverIDs] is mandatory!')
    elif type(receiver_ids) == int:
        receiver_ids = [receiver_ids]
    if type(receiver_ids) != list:
        raise IkValidateException('Parameter [receiverIDs] should be an int or an int list!')
    elif len(receiver_ids) == 0:
        raise IkValidateException('Parameter [receiverIDs] cannot be empty!')
    for receiver_id in receiver_ids:
        receiver = UserManager.getUserName(userID=receiver_id)
        if receiver is None:
            raise IkValidateException(False, 'Receiver [%s] does not exist.' % receiver_id)
    if isNullBlank(module):
        raise IkValidateException(False, 'Parameter [Module] is mandatory.')
    if isNullBlank(summary):
        raise IkValidateException(False, 'Parameter [Summary] is mandatory.')
    if not isNullBlank(link_params) and type(link_params) != dict:
        raise IkValidateException('Parameter [linkParameters] should be None or a dict.')
    # prepare model records
    inbox_rcs = []
    inbox_prm_rcs = []
    for receiver_id in receiver_ids:
        inbox_rc = IkInbox(owner_id=receiver_id,
                           sender_id=sender_id,
                           send_dt=datetime.now(),
                           sts=IkInbox.STATUS_NEW,
                           summary=summary,
                           module=module)
        inbox_rcs.append(inbox_rc)
        if link_params is not None and len(link_params) > 0:
            for name, value in link_params.items():
                inbox_prm_rcs.append(IkInboxPrm(inbox=inbox_rc, k=name, v=(None if isNullBlank(value) else value)))
    # save to database
    ptrn = IkTransaction(userID=sender_id)
    ptrn.add(inbox_rcs)
    ptrn.add(inbox_prm_rcs)
    b = ptrn.save()
    if not b.value:
        raise IkValidateException(b.dataStr)
    return [inboxRc.id for inboxRc in inbox_rcs]
