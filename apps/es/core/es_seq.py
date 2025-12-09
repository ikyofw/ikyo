"""ES sequence management

"""
import logging
from enum import Enum, unique
from threading import Lock

from django.db.models import Q

import core.user.user_manager as UserManager
from core.core.exception import IkException, IkValidateException
from core.db.transaction import IkTransaction

from .. import models as esModels

logger = logging.getLogger('ikyo')


@unique
class SequenceType(Enum):
    """Sequence types
    """

    SEQ_TYPE_EXPENSE_SN = "expense sn"
    SEQ_TYPE_CASH_ADVANCEMENT_SN = "cash sn"
    SEQ_TYPE_EXPENSE_FILE = "expense file"
    SEQ_TYPE_PAYMENT_RECORD_FILE = "payment record file"
    SEQ_TYPE_EXCHANGE_RECEIPT_FILE = "exchange receipt file"
    SEQ_TYPE_EXPENSE_DRAFT_SN = "expense draft sn"
    SEQ_TYPE_SUPPORTING_DOCUMENT = "supporting document"
    SEQ_TYPE_PO_SN = "po sn"
    SEQ_TYPE_PO_FILE = "po file"


# MAX to 8
__MAX_SEQ = 100000000
__MAX_DRAFT_SEQ = __MAX_SEQ / 10000
__seqLock = Lock()


def getNextSeq(sequenceType: SequenceType, officeID: int, maxReset: bool = False, maxValue: int = None) -> int:
    """Get next sequence by sequence type and office ID

    Args:
        sequenceType (SequenceType): Sequence type.
        officeID (int): Office's ID.
        maxReset (bool): reset value

    Returns:
        Next sequence ID if found, None otherwise.

    Raises:
        IkException: If update the sequence failed.

    """
    __seqLock.acquire()
    try:
        seq = 1
        rc = esModels.Sequence.objects.filter(tp=sequenceType.value).filter(office_id=officeID).first()
        if rc is None:
            rc = esModels.Sequence(tp=sequenceType.value, office_id=officeID, seq=seq)
        else:
            seq = rc.seq + 1
            if maxReset is True and seq >= maxValue:
                seq = 1
            rc.seq = seq
            rc.ik_set_status_modified()
        trn = IkTransaction(userID=UserManager.SYSTEM_USER_ID)
        trn.add(rc)
        b = trn.save()
        if not b.value:
            raise IkException(b.dataStr)
        return seq
    finally:
        __seqLock.release()


def getCurrentSeq(sequenceType: SequenceType, officeID: int) -> int:
    """Get the current sequence.

    Args:
        sequenceType (SequenceType): Sequence type.
        officeSN (int): Office's ID.

    Returns:
        Current sequence if found, None otherwise.
    """
    rc = esModels.Sequence.objects.filter(tp=sequenceType.value, office_id=officeID).first()
    return None if rc is None else rc.seq


def getNextSN(sequenceType: SequenceType, officeID: int) -> str:
    """Get next SN.

    Args:
        sequenceType (SequenceType): Sequence type.
        officeID (str): Office's ID.

    Returns:
        Next SN.

    Raises:
        IkException: If data error or system error.

    """
    if officeID is None:
        raise IkException('Parameter office is mandatory.')
    officeRc = esModels.Office.objects.filter(id=officeID).first()
    if officeRc is None:
        raise IkException('Office [%s] does not exist.' % officeID)
    seq = getNextSeq(sequenceType, officeRc.id)
    if seq >= __MAX_SEQ:
        logging.error('Sequence is too large, system cannot support. The last sequence is %s for [%s] for office [%s].' % (seq, sequenceType, officeRc.code))
        raise IkException("Sequence is too large, system cannot support!")
    seqStr = str(seq).zfill(len(str(__MAX_SEQ - 1)))
    sn = '%s%s' % (officeRc.code, seqStr)
    return sn


def SN2Number(sn: str) -> int:
    """Convert sn to a number. 

    Example:
        HK00002026 -> 2026

    Args:
        sn (str): Expense/Cash Advancement SN.

    Returns:
        SN number (int).
    """
    s = ''
    # remove office code
    for i in range(len(sn)):
        x = sn[i]
        if x >= '0' and x <= '9':
            s = sn[i:]
            break
    for i in range(len(s)):
        x = sn[i]
        if x >= '0':
            s = s[i:]
            break
    return int(s)


# Use this method to replace getRollbackSeq
def rollbackSeq(sequenceType: SequenceType, officeObject: any, rollbackSeq: int, transaction: IkTransaction = None, exact: bool = True) -> int:
    """Get the current sequence and rollback the sequence (-1)

    Args:
        sequenceType (SequenceType): Sequence type.
        officeObject (int|str): Office's ID or office's code.
        transaction (IkTransaction, optional): Update transaction.
        exact (bool): Raise exception if rollback failed when exact is True. Otherwise return the current sequence.

    Returns:
        The sequence after rollback. If no sequence record found, then return 0.
        If 

    Raises:
        IkException: If data error or system error.

    Todo:
        * need to test this method in a transaction
        * add lock work with getNextSeq(..) when parameter transaction is not None
    """
    officeID = None
    if officeObject is None:
        raise IkValidateException("Parameter office is mandatory.")
    elif type(officeObject) == str:
        officeRc = esModels.Office.objects.filter(code=officeObject).first()
        if officeRc is None:
            raise IkValidateException('Office [%s] is not found.' % officeObject)
        officeID = officeRc.id
    elif type(officeObject) == int:
        officeID = officeObject
    elif isinstance(officeObject, esModels.Office):
        officeID = officeObject.id
    else:
        raise IkValidateException("Parameter office should be office's ID or office's code. Please check: %s" % officeObject)
    if type(rollbackSeq) != int:
        raise IkValidateException('Rollback sequence should be an integer value: %s' % rollbackSeq)
    __seqLock.acquire()
    try:
        rc = esModels.Sequence.objects.filter(Q(tp=sequenceType.value) & Q(office_id=officeID)).first()
        seq = 0
        if rc is not None:
            seq = rc.seq
            if seq != rollbackSeq:
                if exact:
                    raise IkValidateException('Concurrent error. Please try again.')
                return seq
            elif seq == 0:
                logger.error("Rollback DB sequence [%s] is 0." % rc.tp)
            else:
                rc.seq = seq - 1
                trn = IkTransaction(userID=UserManager.SYSTEM_USER_ID) if transaction is None else transaction
                trn.modify(rc)
                if transaction is None:
                    b = trn.save()
                    if not b.value:
                        logging.error('Rollback sequence failed. The last sequence is %s for [%s] for office [%s].' % (seq, sequenceType.value, officeObject))
                        raise IkException('Update sequence failed: %s' % b.dataStr)
                return rc.seq
        return seq
    finally:
        __seqLock.release()


def getDraftSN(office: int | esModels.Office) -> str:
    """Get next draft SN.

    Args:
        office (int or esModels.Office)
    Returns:
        Next SN.

    Raises:
        IkException: If data error or system error.

    """
    if type(office) == int:
        officeRc = esModels.Office.objects.filter(id=office).first()
    else:
        officeRc = office
    if officeRc is None:
        raise IkException('Office [%s] does not exist.' % office)
    seq = getNextSeq(SequenceType.SEQ_TYPE_EXPENSE_DRAFT_SN, officeRc.id, True, __MAX_DRAFT_SEQ)
    if seq >= __MAX_DRAFT_SEQ:
        logging.error('Sequence is too large, system cannot support. The last sequence is %s for [%s] for office [%s].' % (
            seq, SequenceType.SEQ_TYPE_EXPENSE_DRAFT_SN, officeRc.code))
        raise IkException("Sequence is too large, system cannot support!")
    officeCode = officeRc.code
    seqStr = str(seq).zfill(len(str(__MAX_DRAFT_SEQ - 1)))
    sn = '%s%s%s' % ('-', officeCode, seqStr)  # office code's length is 2.
    return sn


def getSupportingDocumentFileSN(seq: int) -> str:
    seqStr = str(seq).zfill(len(str(__MAX_SEQ - 1)))
    sn = 'S%s' % (seqStr)
    return sn


def getCashAdvancementReceiptFileSN(seq: int) -> str:
    seqStr = str(seq).zfill(len(str(__MAX_SEQ - 1)))
    sn = 'FX%s' % (seqStr)
    return sn
