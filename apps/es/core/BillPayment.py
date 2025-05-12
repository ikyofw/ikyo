"""ES sequence management

"""
import logging
import os
import shutil
import traceback
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from threading import Lock

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import connection
from django.db.models import Exists, OuterRef, Q

#import adminsupport.manager.ib000Manager as InboxManager
import core.core.fs as ikfs
import core.user.userManager as UserManager
import core.utils.db as dbUtils
import es.core.ESEvent as EventManager
import es.core.ESFile as ESFileManager
import es.core.ESSeq as SnManager
import es.core.ESTools as ESTools
import es.core.PO as POManager
#import wci.core.user.userManager as WciUserManager
from core.core.exception import IkException, IkValidateException
from core.core.lang import Boolean2
# from core.core.mailer import MailManager
from core.db.transaction import IkTransaction
from core.sys.systemSetting import SystemSetting
from core.utils.langUtils import isNotNullBlank, isNullBlank
from es.models import *
from .status import Status
#from wci.core.ui.menuManager import WciMenuManager
#from wci.models import WciOffice
#from wci.openfire.openfireManager import OpenfireManager
from ..core.finance import round_currency
from ..core.const import *

__EXPENSE_LOCK = Lock()

logger = logging.getLogger('ikyo')

def createBillPayment(claimerID: int, payeeID: int, expenseRmk: str, claimerRmk: str, expenseFile: Path, eChequeFile: Path, expenseDtlRcs: list[ExpenseDetail]):
    '''
        used for ES006, ES007

        return (fileID, fileSeq)
    '''
    if type(claimerID) != int:
        raise IkValidateException("Parameter [claimerID] should be an integer.")
    claimerRc = UserManager.getUser(claimerID)
    if claimerRc is None:
        raise IkValidateException('Operator [%s] does not exist.' % claimerID)
    if type(payeeID) != int:
        raise IkValidateException("Parameter [payeeID] should be an integer.")
    payeeRc = Payee.objects.filter(id=payeeID).first()
    if payeeRc is None:
        raise IkValidateException('Payee [%s] does not exist.' % payeeID)
    if expenseFile is None:
        raise IkValidateException("Parameter [expenseFile] is mandatory.")
    expenseFile = Path(expenseFile)
    if not expenseFile.is_file():
        raise IkValidateException('Expense file [%s] does not exist.' % expenseFile.absolute())
    elif not ESFileManager.validateUploadFileType(expenseFile):
        raise IkValidateException('Unsupport file [%s]. Only %s allowed.' % (expenseFile, ESFileManager.ALLOW_FILE_TYPES))
    if eChequeFile is None:
        raise IkValidateException("Parameter [eChequeFile] is mandatory.")
    eChequeFile = Path(eChequeFile)
    if not eChequeFile.is_file():
        raise IkValidateException('Echeque file [%s] does not exist.' % eChequeFile.absolute())
    elif not ESFileManager.validateUploadFileType(eChequeFile):
        raise IkValidateException('Unsupport file [%s]. Only %s allowed.' % (eChequeFile, ESFileManager.ALLOW_FILE_TYPES))
    if expenseDtlRcs is None or len(expenseDtlRcs) == 0:
        raise IkValidateException("Please fill in the expense detail.")

    # get payee office
    payeeOffice = payeeRc.office
    if isNullBlank(payeeOffice):
        raise IkValidateException("Please update payee's office first.")
    payeeOfficeRc = payeeOffice
    if payeeOfficeRc is None:
        raise IkValidateException("Office [%s] does not exist." % payeeOffice)

    expenseSN = None
    expenseFileID = None
    expenseFileSeq = None
    echequeFileID = None
    echequeFileSeq = None
    isSuccess = False
    __EXPENSE_LOCK.acquire()
    try:
        # save expense file
        expenseFileID, expenseFileSeq = uploadExpenseFile(claimerID, payeeOffice, expenseFile)
        expenseFileRc = WciEsFile.objects.filter(id=expenseFileID).first()
        if eChequeFile is not None:
            echequeFileID, echequeFileSeq = __uploadEChequeFileForBillPayment(claimerID, payeeRc, eChequeFile)

        claimAmt = 0
        snSeq = 0
        for dtlRc in expenseDtlRcs:
            snSeq += 1
            dtlRc.sn = snSeq
            dtlRc.file = expenseFileRc
            dtlRc.ccy = payeeOfficeRc.ccy
            claimAmt = ESTools.add(Decimal(dtlRc.amt), Decimal(claimAmt))
        claimAmt = round_currency(claimAmt)

        # generate SN
        currentTime = datetime.now()
        expenseSN = SnManager.getNextSN(SnManager.SequenceType.SEQ_TYPE_EXPENSE_SN, payeeOffice)
        expenseHdrRc = WciEsHdr()
        expenseHdrRc.sn = expenseSN
        expenseHdrRc.sts = Status.SETTLED.value
        expenseHdrRc.claimer = claimerRc
        expenseHdrRc.submit_dt = currentTime
        expenseHdrRc.claim_amt = claimAmt
        expenseHdrRc.pay_amt = claimAmt
        expenseHdrRc.payee = payeeRc
        expenseHdrRc.payee_name = payeeRc.payee
        expenseHdrRc.bank_info = payeeRc.bank_info
        expenseHdrRc.default_approver = claimerRc
        expenseHdrRc.settle_by_prior_balance = SETTLE_BY_PRIOR_BALANCE_YES
        expenseHdrRc.po_no = None
        expenseHdrRc.rmk = expenseRmk
        expenseHdrRc.claimer_rmk = claimerRmk
        expenseHdrRc.is_petty_expense = False
        expenseHdrRc.assignPrimaryID()

        for dtlRc in expenseDtlRcs:
            dtlRc.hdr = expenseHdrRc

        payRc = WciEsPay()
        payRc.sts = Status.SETTLED.value
        payRc.ccy = payeeOfficeRc.ccy
        payRc.amt = claimAmt
        payRc.approver = claimerRc
        payRc.pay_dt = currentTime
        payRc.payer = claimerRc
        payRc.pay_dt = currentTime
        payRc.e_cheque_file_id = echequeFileID  # can be None if echeque file does not exist
        payRc.assignPrimaryID()

        expenseHdrRc.pay = payRc

        # events
        eventRemarks = "bill payment"
        eventRc1 = EventManager.add_expense_event(currentTime, claimerRc, expenseSN, None, Status.SUBMITTED, eventRemarks)
        eventRc2 = EventManager.add_expense_event(currentTime, claimerRc, expenseSN, Status.SUBMITTED, Status.APPROVED, eventRemarks)
        eventRc3 = EventManager.add_expense_event(currentTime, claimerRc, expenseSN, Status.APPROVED, Status.PAID, eventRemarks)
        eventRc4 = EventManager.add_expense_event(currentTime, claimerRc, expenseSN, Status.PAID, Status.SETTLED, eventRemarks)

        eventRc5 = EventManager.add_expense_pay_event(currentTime, claimerRc, expenseSN, None, Status.APPROVED, eventRemarks)
        eventRc6 = EventManager.add_expense_pay_event(currentTime, claimerRc, expenseSN, Status.APPROVED, Status.PAID, eventRemarks)
        eventRc7 = EventManager.add_expense_pay_event(currentTime, claimerRc, expenseSN, Status.PAID, Status.SETTLED, eventRemarks)

        ptrn = IkTransaction(userID=claimerID)
        ptrn.add(payRc)
        ptrn.add(expenseHdrRc)
        ptrn.add(expenseDtlRcs)
        ptrn.add(eventRc1)
        ptrn.add(eventRc2)
        ptrn.add(eventRc3)
        ptrn.add(eventRc4)
        ptrn.add(eventRc5)
        ptrn.add(eventRc6)
        ptrn.add(eventRc7)
        b = ptrn.save(updateDate=currentTime)
        if not b.value:
            raise IkValidateException(b.dataStr)

        # TODO: send email
        isSuccess = True
    except IkException as e:
        logger.error('Create bill payment failed: %s' % str(e))
        logger.error(e, exc_info=True)
        raise e
    except Exception as e:
        logger.error('Create bill payment failed: %s' % str(e))
        logger.error(e, exc_info=True)
        raise IkException('System error, please ask administrator to check.')
    finally:
        try:
            if not isSuccess:
                if expenseSN is not None:
                    try:
                        SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_EXPENSE_SN, payeeOfficeRc.sn, SnManager.SN2Number(expenseSN))
                    except Exception as e:
                        logger.error('Rollback bill payment expense file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_EXPENSE_SN.value, expenseFileSeq, str(e)))
                        logger.error(e, exc_info=True)
                if expenseFileSeq is not None:  # rollback expense file seq
                    try:
                        SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE, payeeOfficeRc.sn, expenseFileSeq)
                    except Exception as e:
                        logger.error('Rollback bill payment expense file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE.value, expenseFileSeq, str(e)))
                        logger.error(e, exc_info=True)
                if expenseFileID is not None:
                    try:
                        # reset the expense file
                        if not expenseFile.is_file():
                            esFile = ESFileManager.getFile(expenseFileID)
                            if esFile is not None and Path(esFile).is_file():
                                esFile = Path(esFile)
                                if not esFile.parent.is_dir():
                                    esFile.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(esFile, expenseFile)
                        if not ESFileManager.rollbackFileRecord(claimerID, expenseFileID):
                            logger.error('Delete bill payment expense file [%s] failed.' % expenseFileID)
                    except Exception as e:
                        logger.error('Delete bill payment expense file [%s] failed: %s' % (expenseFileID, str(e)))
                        logger.error(e, exc_info=True)
                if echequeFileSeq is not None:  # rollback echeque file seq
                    try:
                        SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE, payeeOfficeRc.sn, echequeFileSeq)
                    except Exception as e:
                        logger.error('Rollback bill payment echeque file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE.value, echequeFileSeq, str(e)))
                        logger.error(e, exc_info=True)
                if echequeFileID is not None:
                    try:
                        # reset the echeque file
                        if not eChequeFile.is_file():
                            esFile = ESFileManager.getFile(echequeFileID)
                            if esFile is not None and Path(esFile).is_file():
                                esFile = Path(esFile)
                                if not esFile.parent.is_dir():
                                    esFile.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(esFile, eChequeFile)
                        if not ESFileManager.rollbackFileRecord(claimerID, echequeFileID):
                            logger.error('Delete bill payment echeque file [%s] failed.' % echequeFileID)
                    except Exception as e:
                        logger.error('Delete bill payment echeque file [%s] failed: %s' % (echequeFileID, str(e)))
                        logger.error(e, exc_info=True)
        except:
            logger.error('Upload expense file failed when do the finally: %s' % str(e))
            logger.error(e, exc_info=True)
        __EXPENSE_LOCK.release()
    return expenseSN, echequeFileSeq