"""Expense management
"""
import os
import shutil
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from threading import Lock

from django.db import connection
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils.timezone import make_aware

import core.core.fs as ikfs
import core.user.userManager as UserManager
import core.utils.db as dbUtils
import es.core.acl as acl
import es.core.ESFile as ESFileManager
import es.core.ESSeq as SnManager
import es.core.ESTools as ESTools
import es.core.po as po_manager
from core.core.exception import IkException, IkValidateException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.log.logger import logger
from core.utils.langUtils import isNotNullBlank, isNullBlank
from es.models import *

from . import CA, ESNotification, petty_expense
from .activity import ActivityType
from .approver import get_office_first_approvers, is_need_second_approval
from .const import *
from .finance import round_currency
from .office import get_office_by_id, validate_user_office
from .setting import is_enable_automatic_settlement_upon_approval
from .status import Status, validate_status_transition
from .supporting_document import get_upload_supporting_document_setting

AllowMultipleClaims = True
PDF_FILE_EXTENSION = 'pdf'

__FILE_UPLOAD_SYNCHRONIZED = Lock()
__EXPENSE_LOCK = Lock()


def getFileUploadLock() -> Lock:
    return __FILE_UPLOAD_SYNCHRONIZED


def getExpensePriorBalanceAmount(hdrID: int) -> float:
    pbRcs = PriorBalance.objects.filter(expense__id=hdrID)
    amount = 0
    for r in pbRcs:
        amount = round_currency(ESTools.add(amount, r.balance_amt))
    return float(round_currency(amount))


def __create_draft_expense(claimer_rc: User, office_rc: Office) -> Expense:
    # only allow one draft expense for each office for a claimer
    expense_rc = acl.add_query_filter(Expense.objects, claimer_rc).filter(claimer=claimer_rc, office=office_rc, sts=Status.DRAFT.value).order_by('id').first()
    if expense_rc is None:
        expense_rc = Expense()
        expense_rc.sn = SnManager.getDraftSN(office_rc)
        expense_rc.office = office_rc
        expense_rc.claimer = claimer_rc
        expense_rc.sts = Status.DRAFT.value
        trn = IkTransaction()
        trn.add(expense_rc)
        b = trn.save()
        if not b.value:
            raise IkException(b.dataStr)
    return expense_rc


def __read_expense_or_create_draft_expense(claimer_rc: User, office_rc: Office, expense_id: int, is_create_draft_expense: bool = False) -> Expense:
    expense_rc = None
    if isNotNullBlank(expense_id):
        expense_rc = acl.add_query_filter(Expense.objects, claimer_rc).filter(id=expense_id).first()
        if expense_rc is None:
            logger.error("Expense doesn't exist. id=%s" % expense_id)
            raise IkValidateException("Expense doesn't exist. Please check.")
        elif expense_rc.claimer.id != claimer_rc.id:
            logger.error('User [%s] try to upload file to expense [%s] created by [%s]. Permission deny. ExpenseHeader ID=%s.' %
                         (claimer_rc.usr_nm, expense_rc.sn, expense_rc.claimer.usr_nm, expense_id))
            raise IkValidateException('Permission deny.')
        elif expense_rc.sts != Status.DRAFT.value \
                and expense_rc.sts != Status.CANCELLED.value \
                and expense_rc.sts != Status.REJECTED.value:
            logger.error('User [%s] try to upload file to [%s] expense [%s]. Permission deny. ExpenseHeader ID=%s.' %
                         (claimer_rc.usr_nm, expense_rc.sts, expense_rc.sn, expense_id))
            raise IkValidateException('Permission deny. The [%s] expense cannot be edit.' % expense_rc.sts)
    elif is_create_draft_expense:
        expense_rc = __create_draft_expense(claimer_rc, office_rc)
    return expense_rc


def prepare_upload_file(office_rc: Office, file_category: ESFileManager.FileCategory, file: Path, specified_file_seq: int = None) -> File:
    seq_type = None
    if file_category == ESFileManager.FileCategory.PAYMENT_RECORD:
        seq_type = SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE
    elif file_category == ESFileManager.FileCategory.INVOICE:
        seq_type = SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE
    elif file_category == ESFileManager.FileCategory.EXCHANGE_RATE_RECEIPT:
        seq_type = SnManager.SequenceType.SEQ_TYPE_EXCHANGE_RECEIPT_FILE
    elif file_category == ESFileManager.FileCategory.SUPPORTING_DOCUMENT:
        seq_type = SnManager.SequenceType.SEQ_TYPE_SUPPORTING_DOCUMENT
    elif file_category == ESFileManager.FileCategory.PO:
        seq_type = SnManager.SequenceType.SEQ_TYPE_PO_FILE
    else:
        raise IkValidateException('UnSupport file category: %s' % (file_category.value))

    file_seq = None
    if isNotNullBlank(specified_file_seq):
        file_seq = specified_file_seq
    else:
        file_seq = SnManager.getNextSeq(seq_type, office_rc.id)
    file_rc = File()
    file_rc.assignPrimaryID()
    new_file_id = file_rc.id

    relative_path_str = ikfs.number2Path(new_file_id)

    # save file
    file_type = ikfs.getFileExtension(file)
    save_file_name = '%s.%s' % (file_seq, file_type)
    file_absolute_path = ESFileManager.getUploadFileAbsolutePath(relative_path_str, save_file_name)
    if file_absolute_path.is_file():
        logger.error("File is exists, please ask administrator to check: FileID=%s, Path=%s" % (new_file_id, file_absolute_path.absolute()))
        raise IkValidateException("System error: File is exists.")
    # move file to ES file system
    if not file_absolute_path.parent.is_dir():
        file_absolute_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(file, file_absolute_path)
    ESFileManager.delete_really_file(file)  # delete empty folder
    if not file_absolute_path.is_file():
        logger.error("Move file [%s] to [%s] failed." % (file.absolute(), file_absolute_path.absolute()))
        raise IkValidateException('System error: save upload failed. Please ask administrator to check.')
    file_rc.tp = file_category.value
    file_rc.office = office_rc
    file_rc.seq = file_seq
    file_rc.file_tp = file_type.upper()
    file_rc.file_original_nm = Path(file).name
    file_rc.file_nm = save_file_name
    file_rc.file_size = os.path.getsize(file_absolute_path.absolute())
    file_rc.file_path = relative_path_str
    file_rc.is_empty_file = False
    file_rc.sha256 = ESFileManager.calculateFileHash(file_absolute_path)
    return file_rc


def get_last_draft_expense(claimer: User, officeID: int) -> Expense:
    return acl.add_query_filter(Expense.objects, claimer).filter(claimer_id=claimer.id, office_id=officeID, sts=Status.DRAFT.value).order_by('id').first()


def upload_expense_file(claimer_rc: User,
                        office_rc: Office,
                        uploaded_file_path: Path,
                        is_no_invoice_file: bool = False,
                        expense_id: int = None,
                        expense_item_id: int = None,
                        specified_file_id: int = None  # replace file (original file's id)
                        ) -> tuple:
    """
        upload expense file
        return (fileID, fileSeq)
    """
    if isNullBlank(uploaded_file_path):
        raise IkValidateException('Parameter [tempUploadFile] is mandatory.')
    elif not Path(uploaded_file_path).is_file():
        raise IkValidateException("File [%s] doesn't exist." % uploaded_file_path)
    if not ESFileManager.validateUploadFileType(uploaded_file_path):
        raise IkValidateException('UnSupport file [%s]. Only %s allowed.' % (uploaded_file_path, ESFileManager.ALLOW_FILE_TYPES))
    uploaded_file_hash = ESFileManager.calculateFileHash(uploaded_file_path)

    is_success = False
    new_file_rc = None
    delete_original_file_info = None
    __FILE_UPLOAD_SYNCHRONIZED.acquire()
    try:
        expense_rc = __read_expense_or_create_draft_expense(claimer_rc, office_rc, expense_id, True)
        # check file is exists or not
        if expense_rc.sts == Status.DRAFT.value:
            exist_draft_file_rc = DraftFile.objects.filter(tp=DraftFile.EXPENSE, claimer=claimer_rc, office=office_rc, file__sha256=uploaded_file_hash).first()
            if exist_draft_file_rc is not None:
                raise IkValidateException("This file exists. Please check. File name is [%s]. SN is %s." %
                                          (exist_draft_file_rc.file.file_original_nm, exist_draft_file_rc.file.seq))
        else:
            exist_expense_file_rc = ExpenseDetail.objects.filter(hdr=expense_rc, file__sha256=uploaded_file_hash).first()
            if exist_expense_file_rc is not None:
                raise IkValidateException("This file exists. Please check. File name is [%s]. SN is %s." %
                                          (exist_expense_file_rc.file.file_original_nm, exist_expense_file_rc.file.seq))

        old_file_rc = None
        associated_expense_item_rcs = None
        associated_draft_file_rcs = None
        if isNotNullBlank(specified_file_id):
            validate_result = checkExpenseFileAccessPermission(expense_rc.id, specified_file_id, claimer_rc, office_rc.id, True)
            if not validate_result.value:
                raise IkValidateException(validate_result.data)
            old_file_rc = File.objects.filter(id=specified_file_id).first()
            if old_file_rc is None:
                logger.error("Replace file failed. The original file doesn't exists. ID=%s" % specified_file_id)
                raise IkValidateException("Original file doesn't exist.")
            associated_expense_item_rcs = [rc for rc in ExpenseDetail.objects.filter(hdr=expense_rc, file=old_file_rc)]
            associated_draft_file_rcs = DraftFile.objects.filter(file=old_file_rc)
            delete_original_file_info = (old_file_rc.id, old_file_rc.file_nm)
        original_file_seq = old_file_rc.seq if old_file_rc else None

        expense_dtl_rc = None
        if isNotNullBlank(expense_item_id):  # update expense file for selected expense
            expense_dtl_rc = ExpenseDetail.objects.filter(id=expense_item_id).first()
            if expense_dtl_rc is None:
                logger.error('Expense is not exists. ID=%s' % expense_item_id)
                raise IkValidateException("Expense doesn't exist.")
            elif expense_dtl_rc.hdr.id != expense_rc.id:
                logger.error("System error. The expense [%s]'s hdr id is not the same as expense_id [%]" % (expense_item_id, expense_rc.id))
                raise IkValidateException("System error.")

        new_file_rc = prepare_upload_file(office_rc, ESFileManager.FileCategory.INVOICE, uploaded_file_path, original_file_seq)
        new_file_rc.is_empty_file = is_no_invoice_file
        if expense_dtl_rc is not None:
            expense_dtl_rc.file = new_file_rc

        newDraftFileRc = DraftFile()
        newDraftFileRc.tp = DraftFile.EXPENSE
        newDraftFileRc.claimer = claimer_rc
        newDraftFileRc.office = office_rc
        newDraftFileRc.file = new_file_rc

        def updateExpenseFile(_ikTransaction, _djangoTransaction, ikTransactionModel):
            if associated_expense_item_rcs is not None and ikTransactionModel.modelData == associated_expense_item_rcs:
                for rc in associated_expense_item_rcs:
                    rc.file = new_file_rc
                    rc.ik_set_status_modified(forceUpgradeVersionNo=True)

        trn = IkTransaction(userID=claimer_rc.id)
        if associated_expense_item_rcs is not None:
            for rc in associated_expense_item_rcs:
                rc.file = None
            trn.modify(associated_expense_item_rcs)
        if associated_draft_file_rcs is not None:
            trn.delete(associated_draft_file_rcs)
        if old_file_rc is not None:
            trn.delete(old_file_rc)
        trn.add(new_file_rc)
        if expense_dtl_rc is not None:
            trn.modify(expense_dtl_rc)
        if newDraftFileRc is not None:
            trn.add(newDraftFileRc)
        if associated_expense_item_rcs is not None:
            trn.modify(associated_expense_item_rcs)
        saveResult = trn.save(afterSaveModels=updateExpenseFile)
        if not saveResult.value:
            raise IkValidateException(saveResult.dataStr)
        is_success = True
        return new_file_rc.id, new_file_rc.seq
    except IkException as e:
        logger.error('%s uploads expense file failed: %s' % (claimer_rc.usr_nm, str(e)))
        logger.error(e, exc_info=True)
        raise e
    except Exception as e:
        logger.error('Upload expense file failed: %s' % str(e))
        logger.error(e, exc_info=True)
        raise IkException('System error, please ask administrator to check.')
    finally:
        try:
            if is_success:
                try:
                    if delete_original_file_info is not None:
                        # delete the old file
                        originalFile = ESFileManager.getIdFile(delete_original_file_info[0], delete_original_file_info[1])
                        __delete_file_from_file_system(originalFile)
                except Exception as e:
                    logger.error('delete_original_file_info[%s] failed: %s' % (delete_original_file_info, str(e)), e, exc_info=True)
            else:  # failed
                if isNotNullBlank(uploaded_file_path) and uploaded_file_path.is_file():
                    ESFileManager.delete_really_file(uploaded_file_path)
                if new_file_rc is not None:
                    if isNotNullBlank(new_file_rc.seq):  # rollback file seq
                        try:
                            SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE, new_file_rc.office.id, new_file_rc.seq)
                        except Exception as e:
                            logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                         (SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE.value, new_file_rc.seq, str(e)))
                            logger.error(e, exc_info=True)
                    if isNotNullBlank(new_file_rc.id):
                        try:
                            if not ESFileManager.rollbackFileRecord(claimer_rc.id, new_file_rc.id):
                                logger.error('Delete echeque file [%s] failed.' % new_file_rc.id)
                        except Exception as e:
                            logger.error('Delete echeque file [%s] failed: %s' % (new_file_rc.id, str(e)))
                            logger.error(e, exc_info=True)
        except Exception as e:
            logger.error('Upload expense file failed when do the finally: %s' % str(e), e, exc_info=True)
        __FILE_UPLOAD_SYNCHRONIZED.release()


def delete_uploaded_expense_file(claimer_rc: User,
                                 office_rc: Office,
                                 uploaded_file_id: int,
                                 expense_id: int = None,
                                 ) -> Boolean2:
    """delete expense file
    """
    is_success = False
    delete_file_info = None
    __FILE_UPLOAD_SYNCHRONIZED.acquire()
    try:
        expense_rc = __read_expense_or_create_draft_expense(claimer_rc, office_rc, expense_id, True)

        validate_result = checkExpenseFileAccessPermission(expense_rc.id, uploaded_file_id, claimer_rc, office_rc.id, validateClaimerOnly=True)
        if not validate_result.value:
            return IkValidateException(message=validate_result.data)

        file_rc = File.objects.filter(id=uploaded_file_id).first()
        delete_file_info = (file_rc.id, file_rc.file_nm)
        draft_file_rc = None
        if expense_rc.sts == Status.DRAFT.value:
            draft_file_rc = DraftFile.objects.filter(tp=DraftFile.EXPENSE, claimer=claimer_rc, office=office_rc, file=file_rc).first()
        expense_item_rcs = ExpenseDetail.objects.filter(hdr=expense_rc, file=file_rc)
        for expenseRc in expense_item_rcs:
            expenseRc.file = None

        is_need_to_rollback_file_seq = (file_rc.seq == SnManager.getCurrentSeq(SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE, office_rc.id))

        trn = IkTransaction(userID=claimer_rc.id)
        if draft_file_rc is not None:
            trn.delete(draft_file_rc)
        trn.modify(expense_item_rcs)
        trn.delete(file_rc)
        if is_need_to_rollback_file_seq:
            SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_EXPENSE_FILE, office_rc.id, file_rc.seq, transaction=trn)
        save_result = trn.save()
        if not save_result.value:
            raise IkValidateException(save_result.dataStr)
        is_success = True
        return Boolean2(True, 'Deleted.')
    except IkValidateException as e:
        logger.error('%s delete expense file failed: %s' % (claimer_rc.usr_nm if claimer_rc is not None else '', str(e)), e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error('%s delete expense file failed: %s' % (claimer_rc.usr_nm if claimer_rc is not None else '', str(e)), e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')
    finally:
        try:
            if is_success:
                try:
                    if delete_file_info is not None:
                        # delete the old file
                        old_file = ESFileManager.getIdFile(delete_file_info[0], delete_file_info[1])
                        __delete_file_from_file_system(old_file)
                except Exception as e:
                    logger.error('delete_original_file_info[%s] failed: %s' % (delete_file_info, str(e)), e, exc_info=True)
        except Exception as e:
            logger.error('Delete expense file failed when do the finally: %s' % str(e), e, exc_info=True)
        __FILE_UPLOAD_SYNCHRONIZED.release()


def __delete_file_from_file_system(file_path: Path) -> None:
    # TODO: delete file and folder.
    # 1. delete converted pdf file from picture for WCI1
    # pdfFile = Path(os.path.join(file_path.parent.absolute(), "%s.%s" % (file_path.stem, PDF_FILE_EXTENSION)))
    # ESFileManager.deleteESFileAndFolder(pdfFile)
    # TODO: for wci1, need to delete the swf files
    ESFileManager.deleteESFileAndFolder(file_path)


def save_expense_details(claimer_rc: User, office_rc: Office, expense_rc: Expense, expense_detail_rcs: list[ExpenseDetail]) -> Boolean2:
    if isNullBlank(claimer_rc):
        logger.error("Operator doesn't exist.")
        raise IkValidateException('Operator does not exist.')
    if isNullBlank(office_rc):
        logger.error("Office doesn't exist.")
        raise IkValidateException("Office don't exist.")
    work_office_ccy_rc = office_rc.ccy
    if isNullBlank(work_office_ccy_rc):
        raise IkValidateException("Please set the default currency unit for the applicant's region. The office name is [%s]." % office_rc.name)

    if isNotNullBlank(expense_rc):
        if expense_rc.claimer.id != claimer_rc.id:
            logger.error('User [%s] try to upload file to expense [%s] created by [%s]. Permission deny. ExpenseHeader ID=%s.' %
                         (claimer_rc.usr_nm, expense_rc.sn, expense_rc.claimer.usr_nm, expense_rc.id))
            raise IkValidateException('Permission deny.')
        elif expense_rc.sts != Status.DRAFT.value \
                and expense_rc.sts != Status.CANCELLED.value \
                and expense_rc.sts != Status.REJECTED.value:
            logger.error('User [%s] try to upload file to [%s] expense [%s]. Permission deny. ExpenseHeader ID=%s.' %
                         (claimer_rc.usr_nm, expense_rc.sts, expense_rc.sn, expense_rc.id))
            raise IkValidateException('Permission deny. The [%s] expense cannot be edited.' % expense_rc.sts)
    else:
        expense_rc = __create_draft_expense(claimer_rc, office_rc)

    # validate the expenses
    last_input_incurrence_date = None
    last_input_description = None
    last_input_category_rc = None
    last_input_ccy_rc = None
    last_input_ex_rate = None
    last_input_project = None
    item_seq = 0
    row_seq = 0
    for expense_item_rc in expense_detail_rcs:
        row_seq += 1
        if expense_item_rc.ik_is_status_delete():
            continue
        item_seq += 1
        if expense_item_rc.ik_is_status_new():
            if isNullBlank(expense_item_rc.incur_dt):
                expense_item_rc.incur_dt = last_input_incurrence_date
            if isNullBlank(expense_item_rc.dsc):
                expense_item_rc.dsc = last_input_description
            if isNullBlank(expense_item_rc.cat):
                expense_item_rc.cat = last_input_category_rc
            if isNullBlank(expense_item_rc.ccy):
                expense_item_rc.ccy = last_input_ccy_rc if last_input_ccy_rc is not None else work_office_ccy_rc
            if isNullBlank(expense_item_rc.ex_rate) and expense_item_rc.ccy.id != work_office_ccy_rc.id:
                expense_item_rc.ex_rate = last_input_ex_rate
            elif expense_item_rc.ccy.id == work_office_ccy_rc.id and isNotNullBlank(expense_item_rc.ex_rate):
                expense_item_rc.ex_rate = None
            if isNullBlank(expense_item_rc.prj_nm):
                expense_item_rc.prj_nm = last_input_project
        if isNullBlank(expense_item_rc.incur_dt):
            raise IkValidateException("Incurrence Date is mandatory. Please check row %s." % row_seq)
        if isNullBlank(expense_item_rc.dsc):
            raise IkValidateException("Expense Description is mandatory! Please check row %s." % row_seq)
        expense_item_rc.dsc = str(expense_item_rc.dsc).strip()
        if isNullBlank(expense_item_rc.cat):
            raise IkValidateException("Category is mandatory. Please check row %s." % row_seq)
        if isNullBlank(expense_item_rc.ccy):
            expense_item_rc.ccy = work_office_ccy_rc
        if isNotNullBlank(expense_item_rc.ex_rate):
            # a payee can submit other office's express
            if expense_item_rc.ex_rate == 0:
                expense_item_rc.ex_rate = None
            elif expense_item_rc.ex_rate < 0:
                raise IkValidateException("The Ex. Rate should be greater than 0. Please check row %s." % row_seq)
        if expense_item_rc.ccy.id != expense_item_rc.ccy.id and isNullBlank(expense_item_rc.ex_rate):
            raise IkValidateException("The Ex. Rate is mandatory for CCY [%s]. Please check row %s." % (expense_item_rc.ccy.code, row_seq))
        elif expense_item_rc.ccy.id == work_office_ccy_rc.id and isNotNullBlank(expense_item_rc.ex_rate):
            if expense_item_rc.ex_rate == 1:
                expense_item_rc.ex_rate = None
            else:
                raise IkValidateException("The Ex. Rate should be empty when the CCY [%s] is the same as local region currency. Please check row %s." % (
                    expense_item_rc.ccy.code, row_seq))
        if isNullBlank(expense_item_rc.prj_nm):
            expense_item_rc.prj_nm = None
        else:
            expense_item_rc.prj_nm = str(expense_item_rc.prj_nm).strip()
        if isNullBlank(expense_item_rc.dsc):
            expense_item_rc.dsc = None
        else:
            expense_item_rc.dsc = str(expense_item_rc.dsc).strip()
        # validate expense record - end
        if expense_item_rc.ik_is_status_retrieve():
            if expense_item_rc.seq != item_seq:
                expense_item_rc.ik_set_status_modified()
        expense_item_rc.seq = item_seq
        expense_item_rc.hdr = expense_rc
        expense_item_rc.office = office_rc
        expense_item_rc.claimer = claimer_rc

        last_input_incurrence_date = expense_item_rc.incur_dt
        last_input_description = expense_item_rc.dsc
        last_input_category_rc = expense_item_rc.cat
        last_input_ccy_rc = expense_item_rc.ccy
        last_input_ex_rate = expense_item_rc.ex_rate
        last_input_project = expense_item_rc.prj_nm

    # update expense header record information. E.g. total amount
    payee_ccy_rc = expense_rc.payee.office.ccy if isNotNullBlank(expense_rc.payee) else work_office_ccy_rc
    original_claim_amount = expense_rc.claim_amt
    new_claim_amount = __getTotalAmount(expense_detail_rcs, payee_ccy_rc)
    is_expense_info_changed = False
    if original_claim_amount != new_claim_amount:
        expense_rc.claim_amt = new_claim_amount
        is_expense_info_changed = True

    pyiTrn = IkTransaction(userID=claimer_rc.id)
    pyiTrn.add(expense_detail_rcs)
    if is_expense_info_changed:
        pyiTrn.modify(expense_rc)
    return pyiTrn.save()


def __getTotalAmount(expenseDetailRcs: list[ExpenseDetail], ccy: Currency) -> Decimal:
    totalAmount = 0
    for rc in expenseDetailRcs:
        if rc.ik_is_status_delete():
            continue
        if rc.ccy.id == ccy.id:
            totalAmount = ESTools.add(totalAmount, rc.amt)
        else:
            if isNotNullBlank(rc.ex_rate):
                totalAmount = ESTools.add(totalAmount, round_currency(ESTools.mul(rc.amt, rc.ex_rate)))
            else:
                totalAmount = ESTools.add(totalAmount, rc.amt)
    return totalAmount


def getInvoiceAmount(localCCY: str, fileID: int) -> Decimal:
    if isNullBlank(localCCY):
        raise IkValidateException("Parameter [localCCY] is mandatory.")
    if type(fileID) != int:
        raise IkValidateException("Parameter [fileID] is incorrect.")
    fileRc = File.objects.filter(id=fileID).first()
    if fileRc is None:
        raise IkValidateException('File [%s] does not exist.' % fileID)
    totalAmount = 0
    for rc in ExpenseDetail.objects.filter(file=fileRc).all():
        if rc.ccy == localCCY:
            totalAmount = ESTools.add(Decimal(totalAmount), rc.amt)
        else:
            ex_rate = 1 if isNullBlank(rc.ex_rate) else rc.ex_rate
            totalAmount = ESTools.add(Decimal(totalAmount), Decimal(round_currency(rc.amt * ex_rate)))
    return round_currency(totalAmount)


def submitExpense(claimer_rc: User, office_rc: Office, expense_id: int, payeeID: int, approverID: int,
                  expenseDescription: str,
                  isSettleByPriorBalance: bool, priorBalanceRcs: list[AvailablePriorBalance] = None,
                  priorBalanceCCYID: int = None, isSettleByPettyCash: bool = False, po_sn: str = None) -> int:
    ''' Submit expenses. 
        Return new expense ID if success, otherwise raise IkValidateException.
    '''
    if isNullBlank(claimer_rc):
        logger.error("Claimer doesn't exist.")
        raise IkValidateException("Claimer doesn't exist.")
    if isNullBlank(office_rc):
        logger.error("Office doesn't exist.")
        raise IkValidateException("Office don't exist.")
    if not validate_user_office(office_rc, claimer_rc):
        logger.error("You don't have permission to access to this office. claimerID=%s OfficeID=%s" % (office_rc.id, claimer_rc.id))
        raise IkValidateException("You don't have permission to access to this office.")
    if isNullBlank(payeeID):
        raise IkValidateException("Payee is mandatory.")
    if isNullBlank(approverID):
        raise IkValidateException("Approver is mandatory.")

    approver_rc = UserManager.getUser(approverID)
    if approver_rc is None:
        logger.error("Approver doesn't exist. id=%d" % (approverID))
        raise IkValidateException("Approver doesn't exist.")

    # check payee
    payeeRc = Payee.objects.filter(id=payeeID).first()
    if payeeRc is None:
        logger.error("Payee doesn't exist. ID=%s" % payeeID)
        raise IkValidateException("Payee doesn't exist.")
    elif payeeRc.office.id != office_rc.id:
        logger.error("Office [%s] doesn't have payee [%s]. OfficeID=%s, PayeeID=%s" % (office_rc.name, payeeRc.payee, office_rc.id, payeeRc.id))
        raise IkValidateException("Office [%s] doesn't have payee [%s]." % (office_rc.name, payeeRc.payee, payeeRc.id))
    payeeDefaultCCYRc = payeeRc.office.ccy
    if isNullBlank(payeeDefaultCCYRc):
        raise IkValidateException("Please set the payee office's CCY first. The office is [%s]." % office_rc.name)

    # check approver
    office_all_approver_rcs = get_office_first_approvers(office_rc, claimer_rc)
    is_approver_exists = False
    for office_approver_rc in office_all_approver_rcs:
        if office_approver_rc.id == approverID:
            is_approver_exists = True
            break
    if not is_approver_exists:
        logger.error("Office [%s] doesn't have approver [%s]. OfficeID=%s, approverID=%s" % (office_rc.name, approver_rc.usr_nm, office_rc.id, approverID))
        raise IkValidateException("Office [%s] doesn't have approver [%s]." % (office_rc.name, approver_rc.usr_nm))

    expenseDescription = str(expenseDescription).strip() if isNotNullBlank(expenseDescription) else None

    # validate prior balance
    priorBalanceCCYRc = None
    if isSettleByPriorBalance:
        if isNullBlank(priorBalanceCCYID):
            raise IkValidateException("Settle by Prior Balance CCY is mandatory.")
        priorBalanceCCYRc = Currency.objects.filter(id=priorBalanceCCYID).first()
        if priorBalanceCCYRc is None:
            logger.error("priorBalanceCCYID doesn't exist. id=%s" % priorBalanceCCYID)
            raise IkValidateException("Prior Balance CCY doesn't exist.")
    isSettleByFXCash = isSettleByPriorBalance and priorBalanceCCYRc.id != payeeDefaultCCYRc.id
    if isSettleByPriorBalance and (isNullBlank(priorBalanceRcs) or len(priorBalanceRcs) == 0):  # TODO: check this checking
        if isSettleByFXCash:
            raise IkValidateException("Please fill in the foreign expense table.")
        else:
            raise IkValidateException("Please fill in prior balance table.")

    isSubmitSuccess = False
    newExpenseSN = None
    hdr_rc = None
    __EXPENSE_LOCK.acquire()
    try:
        # check expense hdr

        if isNotNullBlank(expense_id):
            hdr_rc = acl.add_query_filter(Expense.objects, claimer_rc).filter(id=expense_id).first()
            if hdr_rc is not None:
                if hdr_rc.claimer.id != claimer_rc.id:
                    logger.error("You doesn't have permission to submit this expense! ClaimerID=%s, PayeeID=%s" % (claimer_rc.id, hdr_rc.id))
                    raise IkValidateException("You doesn't have permission to submit this expense!")
                elif hdr_rc.sts != Status.DRAFT.value \
                        and hdr_rc.sts != Status.REJECTED.value \
                        and hdr_rc.sts != Status.CANCELLED.value:
                    logger.error("This expense has been submitted! ClaimerID=%s, ExpenseID=%s, ExpenseSN=%s" % (claimer_rc.id, hdr_rc.id, hdr_rc.sn))
                    raise IkValidateException("This expense has been submitted! Its SN is [%s]." % hdr_rc.sn)
        else:
            hdr_rc = __create_draft_expense(claimer_rc, office_rc)
        isDraft = hdr_rc.sts == Status.DRAFT.value

        # validate purchase order No.
        po_rc = None
        if isNotNullBlank(po_sn):
            po_sn = str(po_sn).strip()
            b = po_manager.validate_po_permission(claimer_rc, po_sn)
            if not b.value:
                raise IkValidateException(b.data)
            po_rc = Po.objects.filter(sn=po_sn).first()

        # expense records
        expense_dtl_rcs = [rc for rc in ExpenseDetail.objects.filter(hdr=hdr_rc).order_by('file__seq', 'incur_dt', 'cat__cat', 'seq')]
        if len(expense_dtl_rcs) == 0:
            raise IkValidateException("Please add expense first.")
        fileIDs, fileRcs = [], []
        totalExpenseClaimAmount = 0
        for expenseRc in expense_dtl_rcs:
            # TODO: do more validate. E.g. description
            ccyRc = expenseRc.ccy
            if expenseRc.amt <= 0:
                raise IkValidateException("Claim amount [%s] should be greater than 0. Please check expense table." % expenseRc.amt)
            exRate = expenseRc.ex_rate
            if ccyRc.id != payeeDefaultCCYRc.id:
                if isNullBlank(exRate):
                    raise IkValidateException(
                        "The payee office's CCY is %s. But this expense's CCY is not the same, then please fill in the Ex. Rate field which CCY is not %s." %
                        (payeeDefaultCCYRc.code, payeeDefaultCCYRc.code))
                elif exRate <= 0:
                    raise IkValidateException("The Ex. Rate should be greater than 0 for CCY %s. Please check. rate=%s" % (ccyRc.code, exRate))
            elif isNotNullBlank(exRate):
                exRate = None
                expenseRc.ex_rate = exRate
                expenseRc.ik_set_status_modified()
            if isNullBlank(expenseRc.file):
                raise IkValidateException("The [File] column is mandatory.")
            elif expenseRc.file.office.id != office_rc.id:
                raise IkValidateException("This expense cannot use file [%s]." % expenseRc.file.seq)
            if expenseRc.file.id not in fileIDs:
                fileIDs.append(expenseRc.file.id)
                fileRcs.append(expenseRc)

            if isSettleByFXCash:
                if ccyRc.id != priorBalanceCCYRc.id:
                    raise IkValidateException("The expense item's CCY should be %s. Please check Expense Details." % priorBalanceCCYRc.code)
                elif isNullBlank(exRate):
                    exRate = 1
                    expenseRc.ex_rate = exRate
                    expenseRc.ik_set_status_modified()
                if expenseRc.ex_rate != 1:
                    raise IkValidateException("The Rate should be 1. Please check Expense Details.")
            elif ccyRc.id != payeeDefaultCCYRc.id:
                if isNullBlank(exRate):
                    raise IkValidateException("The payee office's CCY is %s. But this expense's CCY is not the same, then please fill in the Ex. Rate field which CCY is not %s."
                                              % (payeeDefaultCCYRc.code, payeeDefaultCCYRc.code))
                elif exRate <= 0:
                    raise IkValidateException("The Ex. Rate should be greater than 0 for CCY %s. Please check." % ccyRc.code)
            elif ccyRc.id == payeeDefaultCCYRc.id and isNotNullBlank(exRate):
                exRate = None
                expenseRc.ex_rate = exRate
                expenseRc.ik_set_status_modified()

            if ccyRc.id == payeeDefaultCCYRc.id:
                totalExpenseClaimAmount = ESTools.add(totalExpenseClaimAmount, expenseRc.amt)
            else:
                totalExpenseClaimAmount = ESTools.add(totalExpenseClaimAmount, round_currency(expenseRc.amt * exRate))
        # TODO: validate the file is not exists in other expense

        # validate prior balance - start
        thisPayAmount = None
        priorBalanceOldRcs = None  # delete the old records
        priorBalanceNewRcs = None  # always create the new record
        if priorBalanceRcs and len(priorBalanceRcs) > 0:
            validatePBResult = __validatePriorBalances(hdr_rc, expense_dtl_rcs, payeeRc, priorBalanceCCYRc, isSettleByFXCash, priorBalanceRcs, totalExpenseClaimAmount)
            if not validatePBResult.value:
                raise IkValidateException(validatePBResult.data)
            priorBalanceOldRcs, priorBalanceNewRcs, priorBalancePayAmount, totalDefaultCCYAmount, thisPayAmount = validatePBResult.data
            if isSettleByFXCash:
                hdr_rc.claim_amt = float(round_currency(totalDefaultCCYAmount))
                hdr_rc.fx_ccy = priorBalanceCCYRc
                hdr_rc.fx_amt = round_currency(priorBalancePayAmount)

            priorBalancePayAmount = 0
            totalDefaultCCYAmount = 0
            if isSettleByPriorBalance:
                availablePbRcs = CA.getAvailablePriorBalanceRcs(payeeRc, priorBalanceCCYRc)
                if len(availablePbRcs) == 0:
                    raise IkValidateException("No available prior balance found for this claim. Please check.")
                settleByPriorBalanceAmount = None
                if isSettleByFXCash:
                    settleByPriorBalanceAmount = __getTotalAmount(expense_dtl_rcs, priorBalanceCCYRc)
                    settleByPriorBalanceAmount = float(round_currency(settleByPriorBalanceAmount))

                priorBalanceOldRcs = list(PriorBalance.objects.filter(expense=hdr_rc).order_by('id'))
                priorBalanceNewRcs = []
                foundAvailablePbRcs = []
                for pbRc in priorBalanceRcs:
                    thisClaim = pbRc.deduction_amt
                    if isNullBlank(thisClaim):
                        continue
                    thisClaim = round_currency(thisClaim)
                    if thisClaim == 0:
                        continue
                    elif thisClaim < 0:
                        raise IkValidateException("This Claim column cannot equal to or less than 0. Please check Prior Balances table. This Claim = %s." % thisClaim)
                    elif ESTools.isGreater(thisClaim, pbRc.balance_amt):
                        raise IkValidateException("This Amount cannot greater than Left Amount %s. Please check %s, This Claim=%s" % (pbRc.balance_amt, pbRc.ca.sn, thisClaim))
                    pbRc.deduction_amt = thisClaim

                    if pbRc.ccy.id != priorBalanceCCYRc.id:
                        raise IkValidateException("System error. The prior balance's currency is [%s], it's not the same as request currency [%s]." % (
                            pbRc.ccy.code, priorBalanceCCYRc.code))

                    # check this record exists or not
                    availableValidate = False
                    for availablePbRc in availablePbRcs:
                        if availablePbRc.ca.id == pbRc.ca.id and availablePbRc.ccy.id == pbRc.ccy.id \
                                and (isNullBlank(availablePbRc.fx) and isNullBlank(pbRc.fx) or isNotNullBlank(availablePbRc.fx) and isNotNullBlank(pbRc.fx) and availablePbRc.fx.id == pbRc.fx.id):
                            if availablePbRc.balance_amt != pbRc.balance_amt:
                                raise IkValidateException("Concurrency error, please refresh the screen to try again.")
                            if availablePbRc in foundAvailablePbRcs:
                                raise IkValidateException("Duplicate prior balance records, please refresh the screen to try again.")
                            foundAvailablePbRcs.append(availablePbRc)
                            availableValidate = True
                            break
                    if not availableValidate:
                        raise IkValidateException("Concurrency error, please refresh the screen to try again.")
                    priorBalancePayAmount = ESTools.add(priorBalancePayAmount, thisClaim)

                    # prepare data object for saving
                    pbNewRc = PriorBalance(ca=pbRc.ca, expense=hdr_rc)
                    if isSettleByFXCash:
                        pbNewRc.balance_amt = round_currency(ESTools.div(pbRc.deduction_amt, pbRc.fx.fx_rate))
                        pbNewRc.fx_balance_amt = pbRc.deduction_amt
                        pbNewRc.fx = pbRc.fx
                    else:
                        pbNewRc.balance_amt = pbRc.deduction_amt
                    priorBalanceNewRcs.append(pbNewRc)
                    totalDefaultCCYAmount = ESTools.add(totalDefaultCCYAmount, pbNewRc.balance_amt)

                priorBalancePayAmount = float(round_currency(priorBalancePayAmount))
                if priorBalancePayAmount == 0:
                    raise IkValidateException("Total settle by prior balance amount cannot be 0. Please check.")
                elif priorBalancePayAmount > totalExpenseClaimAmount:
                    raise IkValidateException("Total settle by prior balance amount is greater than claim amount. Please check. The claim amount is %s." % totalExpenseClaimAmount)
                elif isSettleByFXCash and settleByPriorBalanceAmount != priorBalancePayAmount:
                    raise IkValidateException("No enough cash for this payment. Please check. CCY=%s" % priorBalanceCCYRc.code)
                if isSettleByFXCash:
                    hdr_rc.claim_amt = float(round_currency(totalDefaultCCYAmount))
                    hdr_rc.fx_ccy = priorBalanceCCYRc
                    hdr_rc.fx_amt = round_currency(priorBalancePayAmount)
                # __validateExpensePriorBalance(hdr_rc)
            # validate prior balance - end

            thisPayAmount = float(round_currency(ESTools.sub(totalExpenseClaimAmount, priorBalancePayAmount)))

        draftFileRcs = DraftFile.objects.filter(tp=DraftFile.EXPENSE, claimer=claimer_rc, office=office_rc, file_id__in=fileIDs).all()

        supporting_document_setting = get_upload_supporting_document_setting(claimer_rc, office_rc, approver_rc)
        if supporting_document_setting == SupportingDocumentSetting.REQUIRE and isNullBlank(hdr_rc.supporting_doc):
            raise IkValidateException("The [Supporting Document] is mandatory. Please upload first.")
        elif supporting_document_setting == SupportingDocumentSetting.DISABLE and isNotNullBlank(hdr_rc.supporting_doc):
            raise IkValidateException("The [Supporting Document] is not allowed. Please remove it first.")

        # update expense hdr
        now = datetime.now()
        originalStatus = hdr_rc.sts
        hdr_rc.sts = Status.SUBMITTED.value
        hdr_rc.office = office_rc
        hdr_rc.claimer = claimer_rc
        hdr_rc.submit_dt = now
        hdr_rc.claim_amt = totalExpenseClaimAmount
        hdr_rc.pay_amt = thisPayAmount
        hdr_rc.payee = payeeRc
        hdr_rc.approver = approver_rc
        hdr_rc.use_prior_balance = isSettleByPriorBalance
        hdr_rc.po = po_rc
        hdr_rc.dsc = expenseDescription

        if isDraft:
            newExpenseSN = SnManager.getNextSN(SnManager.SequenceType.SEQ_TYPE_EXPENSE_SN, office_rc.id)
            hdr_rc.sn = newExpenseSN

        submit_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id,
                                   operate_dt=now, operator=claimer_rc, sts=hdr_rc.sts)
        hdr_rc.last_activity = submit_activity
        hdr_rc.is_petty_expense = isSettleByPettyCash
        if isSettleByPettyCash:
            hdr_rc.pay_amt = hdr_rc.claim_amt

        pytrn = IkTransaction(userID=claimer_rc.id)
        pytrn.add(submit_activity)
        pytrn.modify(hdr_rc)
        pytrn.add(expense_dtl_rcs)
        pytrn.delete(draftFileRcs)
        if isNotNullBlank(priorBalanceOldRcs) and len(priorBalanceOldRcs) > 0:
            pytrn.delete(priorBalanceOldRcs)
        if isNotNullBlank(priorBalanceNewRcs) and len(priorBalanceNewRcs) > 0:
            pytrn.add(priorBalanceNewRcs)
        b = pytrn.save(updateDate=now)
        if not b.value:
            raise IkException(b.dataStr)
        isSubmitSuccess = True
        return hdr_rc.id
    except Exception as e:
        logger.error(e, exc_info=True)
        if isinstance(e, IkValidateException):
            raise e
        raise IkValidateException("System error, please ask administrator to check!")
    finally:
        if isSubmitSuccess:
            ESNotification.send_submit_cancel_reject_expense_notify(claimer_rc.id, hdr_rc)
        else:
            if isNotNullBlank(newExpenseSN):
                try:
                    SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_EXPENSE_SN, office_rc.code, SnManager.SN2Number(newExpenseSN))
                except Exception as e:
                    logger.error(e, exc_info=True)
        __EXPENSE_LOCK.release()


def __validatePriorBalances(expenseHdrRc: Expense, expenseRcs: list[ExpenseDetail], payeeRc: Payee, priorBalanceCCYRc: Currency, isSettleByFXCash: bool,
                            priorBalanceRcs: list[AvailablePriorBalance], totalExpenseClaimAmount: float) -> Boolean2:
    priorBalanceOldRcs = None  # delete the old records
    priorBalanceNewRcs = None  # always create the new record
    priorBalancePayAmount = 0
    totalDefaultCCYAmount = 0

    availablePbRcs = CA.getAvailablePriorBalanceRcs(payeeRc, priorBalanceCCYRc)
    if len(availablePbRcs) == 0:
        return Boolean2.FALSE("No available prior balance found for this claim. Please check.")
    settleByPriorBalanceAmount = None
    if isSettleByFXCash:
        settleByPriorBalanceAmount = __getTotalAmount(expenseRcs, priorBalanceCCYRc)
        settleByPriorBalanceAmount = float(round_currency(settleByPriorBalanceAmount))

    priorBalanceOldRcs = list(PriorBalance.objects.filter(expense=expenseHdrRc).order_by('id'))
    priorBalanceNewRcs = []
    foundAvailablePbRcs = []
    for pbRc in priorBalanceRcs:
        thisClaim = pbRc.deduction_amt
        if isNullBlank(thisClaim):
            continue
        thisClaim = round_currency(thisClaim)
        if thisClaim == 0:
            continue
        elif thisClaim < 0:
            return Boolean2.FALSE("This Claim column cannot equal to or less than 0. Please check Prior Balances table. This Claim = %s." % thisClaim)
        elif ESTools.isGreater(thisClaim, pbRc.balance_amt):
            return Boolean2.FALSE("This Amount cannot greater than Left Amount %s. Please check %s, This Claim=%s" % (pbRc.balance_amt, pbRc.ca.sn, thisClaim))
        pbRc.deduction_amt = thisClaim

        if pbRc.ccy.id != priorBalanceCCYRc.id:
            return Boolean2.FALSE("System error. The prior balance's currency is [%s], it's not the same as request currency [%s]." % (pbRc.ccy.code, priorBalanceCCYRc.code))

        # check this record exists or not
        availableValidate = False
        for availablePbRc in availablePbRcs:
            if availablePbRc.ca.id == pbRc.ca.id and availablePbRc.ccy.id == pbRc.ccy.id \
                    and (isNullBlank(availablePbRc.fx) and isNullBlank(pbRc.fx) or isNotNullBlank(availablePbRc.fx) and isNotNullBlank(pbRc.fx) and availablePbRc.fx.id == pbRc.fx.id):
                if availablePbRc.balance_amt != pbRc.balance_amt:
                    return Boolean2.FALSE("Concurrency error, please refresh the screen to try again.")
                if availablePbRc in foundAvailablePbRcs:
                    return Boolean2.FALSE("Duplicate prior balance records, please refresh the screen to try again.")
                foundAvailablePbRcs.append(availablePbRc)
                availableValidate = True
                break
        if not availableValidate:
            return Boolean2.FALSE("Concurrency error, please refresh the screen to try again.")
        priorBalancePayAmount = ESTools.add(priorBalancePayAmount, thisClaim)

        # prepare data object for saving
        pbNewRc = PriorBalance(ca=pbRc.ca, expense=expenseHdrRc)
        if isSettleByFXCash:
            pbNewRc.balance_amt = round_currency(ESTools.div(pbRc.deduction_amt, pbRc.fx.fx_rate))
            pbNewRc.fx_balance_amt = pbRc.deduction_amt
            pbNewRc.fx = pbRc.fx
        else:
            pbNewRc.balance_amt = pbRc.deduction_amt
        priorBalanceNewRcs.append(pbNewRc)
        totalDefaultCCYAmount = ESTools.add(totalDefaultCCYAmount, pbNewRc.balance_amt)

    priorBalancePayAmount = float(round_currency(priorBalancePayAmount))
    if priorBalancePayAmount == 0:
        return Boolean2.FALSE("Total settle by prior balance amount cannot be 0. Please check.")
    elif priorBalancePayAmount > totalExpenseClaimAmount:
        return Boolean2.FALSE("Total settle by prior balance amount is greater than claim amount. Please check. The claim amount is %s." % totalExpenseClaimAmount)
    elif isSettleByFXCash and settleByPriorBalanceAmount != priorBalancePayAmount:
        return Boolean2.FALSE("No enough cash for this payment. Please check. CCY=%s" % priorBalanceCCYRc.code)
    # __validateExpensePriorBalance(expenseHdrRc)
    thisPayAmount = float(round_currency(ESTools.sub(totalExpenseClaimAmount, priorBalancePayAmount)))
    return Boolean2.TRUE((priorBalanceOldRcs, priorBalanceNewRcs, priorBalancePayAmount, totalDefaultCCYAmount, thisPayAmount))


# YL, 2023-05-23 - start
def approve_expense(operator_id: int, expense_hdr_id: int) -> Boolean2:
    approver_rc = UserManager.getUser(operator_id)
    if approver_rc is None:
        logger.error("Approver doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(expense_hdr_id):
        logger.error("Parameter [expense_hdr_id] is mandatory.")
        return Boolean2.FALSE("System error.")

    is_success = False
    hdr_rc = None
    __EXPENSE_LOCK.acquire()
    try:
        hdr_rc = acl.add_query_filter(Expense.objects, approver_rc).filter(id=expense_hdr_id).first()
        hdr_rc: Expense
        if hdr_rc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_hdr_id)
            return Boolean2.FALSE("Expense doesn't exist.")

        # validate status
        validate_status_result = validate_status_transition(hdr_rc.sts, Status.APPROVED)
        if not validate_status_result.value:
            return validate_status_result

        is_second_approval = hdr_rc.sts == Status.FIRST_APPROVED.value
        is_final_approval = True
        # check need to second approve or not
        if hdr_rc.sts == Status.SUBMITTED.value:
            if is_need_second_approval(hdr_rc.office, approver_rc, hdr_rc.claim_amt):
                is_final_approval = False
        # validate approver
        if not acl.is_approverable(approver_rc, hdr_rc.sts, hdr_rc.payee, hdr_rc.claim_amt, hdr_rc.approver):
            logger.error("You don't have permission to approve this expense. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (hdr_rc.id, hdr_rc.sn, approver_rc.id, approver_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to approve this expense.")

        approve_date = datetime.now()
        hdr_rc.sts = Status.APPROVED.value if is_final_approval else Status.FIRST_APPROVED.value
        approve_activity = None
        if is_second_approval:
            approve_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=approve_date,
                                        operator=approver_rc, sts=hdr_rc.sts)
            hdr_rc.approve2_activity = approve_activity
        else:
            approve_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=approve_date,
                                        operator=approver_rc, sts=hdr_rc.sts)
            hdr_rc.approve_activity = approve_activity

        settle_activity = None
        if is_enable_automatic_settlement_upon_approval() and is_final_approval and hdr_rc.use_prior_balance and hdr_rc.pay_amt == 0:
            hdr_rc.pay_amt = 0
            settle_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=approve_date,
                                       operator=approver_rc, sts=Status.SETTLED.value, dsc='[Automatic settled.]')
            hdr_rc.payment_activity = settle_activity

            hdr_rc.sts = Status.SETTLED.value
            hdr_rc.last_activity = settle_activity
        else:
            hdr_rc.last_activity = approve_activity

        trn = IkTransaction(userID=approver_rc.id)
        trn.add(approve_activity)
        if settle_activity:
            trn.add(settle_activity)
        trn.modify(hdr_rc)
        result = trn.save(updateDate=approve_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Expense [%s] has been %s." % (hdr_rc.sn, 'settled' if settle_activity else 'approved'))
    except Exception as e:
        logger.error("Approve expense [%s] failed: %s" % (hdr_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        __EXPENSE_LOCK.release()
        if is_success:
            ESNotification.send_approve_confirm_petty_expense_notify(operator_id, hdr_rc)


def cancel_expense(operator_id: int, expense_hdr_id: int, cancel_reason: str) -> Boolean2:
    # base validation
    canceller_rc = UserManager.getUser(operator_id)
    if canceller_rc is None:
        logger.error("Operator doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Operator doesn't exist.")
    if isNullBlank(expense_hdr_id):
        logger.error("Parameter [expense_hdr_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    if isNullBlank(cancel_reason):
        logger.error("Cancel reason is mandatory.")
        return Boolean2.FALSE("Please fill in the Cancel Reason first.")
    cancel_reason = str(cancel_reason).strip()

    is_success = False
    __EXPENSE_LOCK.acquire()
    try:
        # validate
        hdr_rc = acl.add_query_filter(Expense.objects, canceller_rc).filter(id=expense_hdr_id).first()
        if hdr_rc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_hdr_id)
            return Boolean2.FALSE("Expense doesn't exist.")
        if hdr_rc.claimer.id != operator_id:
            logger.error("User %s doesn't have permission to cancel expense %s." % (canceller_rc.usr_nm, hdr_rc.sn))
            return Boolean2.FALSE("Permission deny!")
        validate_status_result = validate_status_transition(hdr_rc.sts, Status.CANCELLED)
        if not validate_status_result.value:
            return validate_status_result

        cancel_date = datetime.now()
        hdr_rc.sts = Status.CANCELLED.value
        hdr_rc.use_prior_balance = False
        hdr_rc.pay_amt = hdr_rc.claim_amt

        cancel_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id,
                                   operate_dt=cancel_date, operator=canceller_rc, sts=hdr_rc.sts, dsc=cancel_reason)
        hdr_rc.last_activity = cancel_activity

        prior_balance_rcs = PriorBalance.objects.filter(expense=hdr_rc).all()
        for r in prior_balance_rcs:
            r.ik_set_status_delete()

        trn = IkTransaction(userID=canceller_rc.id)
        trn.add(cancel_activity)
        trn.add(prior_balance_rcs)
        trn.modify(hdr_rc)
        result = trn.save(updateDate=cancel_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Expense [%s] has been cancelled." % hdr_rc.sn)
    except Exception as e:
        logger.error("Cancel cash advancement [%s] failed: %s" % (hdr_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        __EXPENSE_LOCK.release()
        if is_success:
            ESNotification.send_submit_cancel_reject_expense_notify(operator_id, hdr_rc)


def reject_expense(operator_id: int, expense_hdr_id: int, reject_reason: str) -> Boolean2:
    rejector_rc = UserManager.getUser(operator_id)
    if rejector_rc is None:
        logger.error("Claimer doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(expense_hdr_id):
        logger.error("Parameter [expense_hdr_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    if isNullBlank(reject_reason):
        return Boolean2.FALSE("Please fill in the Reject Reason first.")
    reject_reason = str(reject_reason).strip()

    is_success = False
    __EXPENSE_LOCK.acquire()
    try:
        # validate
        hdr_rc = acl.add_query_filter(Expense.objects, rejector_rc).filter(id=expense_hdr_id).first()
        if hdr_rc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_hdr_id)
            return Boolean2.FALSE("Expense doesn't exist.")
        elif hdr_rc.claimer.id == rejector_rc.id and not acl.is_office_admin(rejector_rc, hdr_rc.office):
            logger.error("[%s] Please cancel this expense instead of rejecting it. ID=%s" % (hdr_rc.claimer.usr_nm, expense_hdr_id))
            return Boolean2.FALSE("Please cancel this expense instead of rejecting it.")
        elif hdr_rc.sts != Status.SUBMITTED.value and hdr_rc.sts != Status.FIRST_APPROVED.value and hdr_rc.sts != Status.APPROVED.value:
            logger.error("Only submitted or first approved or approved expense can be rejected. Please check. ID=%s, Current status is [%s]" % (expense_hdr_id, hdr_rc.sts))
            return Boolean2.FALSE("Only submitted or first approved or approved expense can be rejected. Please check.")

        validate_status_result = validate_status_transition(hdr_rc.sts, Status.REJECTED)
        if not validate_status_result.value:
            return validate_status_result
        if not acl.is_rejectable(rejector_rc, hdr_rc.sts, hdr_rc.payee, hdr_rc.claim_amt, hdr_rc.approver, hdr_rc.is_petty_expense, isNotNullBlank(hdr_rc.petty_expense_activity)):
            logger.error("You don't have permission to reject this expense. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (hdr_rc.id, hdr_rc.sn, rejector_rc.id, rejector_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to reject this expense.")

        reject_date = datetime.now()
        hdr_rc.sts = Status.REJECTED.value
        hdr_rc.use_prior_balance = False
        hdr_rc.pay_amt = hdr_rc.claim_amt

        reject_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id,
                                   operate_dt=reject_date, operator=rejector_rc, sts=hdr_rc.sts, dsc=reject_reason)
        hdr_rc.last_activity = reject_activity

        prior_balance_rcs = PriorBalance.objects.filter(expense=hdr_rc).all()
        for r in prior_balance_rcs:
            r.ik_set_status_delete()

        trn = IkTransaction(userID=rejector_rc.id)
        trn.add(reject_activity)
        trn.add(prior_balance_rcs)
        trn.modify(hdr_rc)
        result = trn.save(updateDate=reject_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Expense [%s] has been rejected." % hdr_rc.sn)
    except Exception as e:
        logger.error("Cancel cash advancement [%s] failed: %s" % (hdr_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        __EXPENSE_LOCK.release()
        if is_success:
            ESNotification.send_submit_cancel_reject_expense_notify(operator_id, hdr_rc)


def confirm_petty_cash_expense(operator_id: int, expense_id: int, priorBalanceRcs: list[AvailablePriorBalance]) -> Boolean2:
    operator_rc = UserManager.getUser(operator_id)
    if operator_rc is None:
        logger.error("Operator [%s] doesn't exist. ID=" % operator_id)
        raise IkValidateException("Operator doesn't exist.")
    if not priorBalanceRcs or len(priorBalanceRcs) == 0:
        return Boolean2.FALSE("Please select one or more than one Cash Payment to fill in the \"This Claim\" field.")
    is_success = False
    hdr_rc = None
    __EXPENSE_LOCK.acquire()
    try:
        hdr_rc = acl.add_query_filter(Expense.objects, operator_rc).filter(id=expense_id).first()
        hdr_rc: Expense
        if not hdr_rc:
            return Boolean2.FALSE("The expense does not exist, please check.")
        if not hdr_rc.is_petty_expense:
            return Boolean2.FALSE("This is not a petty cash expense. Please check.")
        elif isNotNullBlank(hdr_rc.petty_expense_activity):
            return Boolean2.FALSE("This petty cash expense has been submitted. Please check.")
        elif hdr_rc.sts != Status.APPROVED.value:
            return Boolean2.FALSE("This petty cash expense's status has been changed. Please check.")
        if not acl.is_approved_petty_expense_confirmable(operator_rc, hdr_rc.sts, hdr_rc.office, hdr_rc.claim_amt):
            return Boolean2.FALSE("You don't have permission to submit this petty cash expense.")
        petty_admin_rc = petty_expense.get_petty_admin_setting(hdr_rc.office)

        expense_dtl_rcs = [rc for rc in ExpenseDetail.objects.filter(hdr=hdr_rc).order_by('file__seq', 'incur_dt', 'cat__cat', 'seq')]
        validatePBResult = __validatePriorBalances(hdr_rc, expense_dtl_rcs, petty_admin_rc.admin_payee, hdr_rc.office.ccy, False, priorBalanceRcs, hdr_rc.claim_amt)
        if not validatePBResult.value:
            raise IkValidateException(validatePBResult.data)
        priorBalanceOldRcs, priorBalanceNewRcs, _priorBalancePayAmount, _totalDefaultCCYAmount, thisPayAmount = validatePBResult.data
        if thisPayAmount != 0:
            return Boolean2.FALSE("The total pay amount should be " + str(hdr_rc.pay_amt) + ". Please check Settle Petty Expense by Prior Balance Detail table.")

        now = datetime.now()
        hdr_rc.is_petty_expense = True
        hdr_rc.petty_expense_submit_usr = operator_rc
        hdr_rc.petty_expense_submit_dt = now

        petty_expense_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=hdr_rc.petty_expense_submit_dt,
                                          operator=hdr_rc.petty_expense_submit_usr, sts=hdr_rc.sts, dsc='Confirm Petty Cash Expense.')
        hdr_rc.last_activity = petty_expense_activity

        petty_expense_settle_activity = None
        if is_enable_automatic_settlement_upon_approval():
            hdr_rc.sts = Status.SETTLED.value
            petty_expense_settle_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=hdr_rc.petty_expense_submit_dt,
                                                     operator=hdr_rc.petty_expense_submit_usr, sts=hdr_rc.sts, dsc='Automatic settled.')
            hdr_rc.last_activity = petty_expense_settle_activity

        hdr_rc.petty_expense_activity = petty_expense_activity

        pytrn = IkTransaction(userID=operator_id)
        pytrn.add(petty_expense_activity)
        if petty_expense_settle_activity:
            pytrn.add(petty_expense_settle_activity)
        pytrn.modify(hdr_rc)
        pytrn.delete(priorBalanceOldRcs)
        pytrn.add(priorBalanceNewRcs)
        b = pytrn.save(updateDate=now)
        if not b.value:
            return b
        is_success = True
        return Boolean2.TRUE("Submitted petty cash expense to accounting.")
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    finally:
        __EXPENSE_LOCK.release()
        if is_success:
            ESNotification.send_approve_confirm_petty_expense_notify(operator_id, hdr_rc)


def settle_expense(operator_id: int, expense_id: int, payment_tp: PaymentMethod, payment_number: str, payment_record_file: Path, payment_rmk: str) -> Boolean2:
    operator_rc = UserManager.getUser(operator_id)
    if operator_rc is None:
        logger.error("Claimer doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(expense_id):
        logger.error("Parameter [expense_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    # payment remark
    payment_rmk = None if isNullBlank(payment_rmk) else str(payment_rmk).strip()

    # validate payment record file
    if isNotNullBlank(payment_record_file):
        if not payment_record_file.is_file():
            logger.error("Payment record file doesn't exist. Path=%s" % str(payment_record_file))
            return Boolean2.FALSE("Payment record file doesn't exist.")
        elif not ESFileManager.validateUploadFileType(payment_record_file):
            return Boolean2.FALSE('UnSupport file [%s]. Only %s allowed.' % (payment_record_file.name, ESFileManager.ALLOW_FILE_TYPES))

    is_success = False
    payment_record_file_rc, payment_record_fileID, payment_record_fileSeq = None, None, None
    hdr_rc = None
    __EXPENSE_LOCK.acquire()
    __FILE_UPLOAD_SYNCHRONIZED.acquire()
    try:
        # validate
        hdr_rc = acl.add_query_filter(Expense.objects, operator_rc).filter(id=expense_id).first()
        if hdr_rc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_id)
            return Boolean2.FALSE("Expense doesn't exist.")

        # validate status
        # user maybe can settled from submitted expense directly
        validate_status_result = validate_status_transition(hdr_rc.sts, Status.SETTLED)
        if not validate_status_result.value:
            return validate_status_result

        if not acl.is_settlable(operator_rc, hdr_rc.sts, hdr_rc.payee, hdr_rc.claim_amt, hdr_rc.approver, hdr_rc.is_petty_expense, isNotNullBlank(hdr_rc.petty_expense_activity)):
            logger.error("You don't have permission to pay this expense. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (hdr_rc.id, hdr_rc.sn, operator_rc.id, operator_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to pay this expense.")
        is_submitted_to_settle = hdr_rc.sts == Status.SUBMITTED.value
        is_first_approved_to_settle = hdr_rc.sts == Status.FIRST_APPROVED.value

        if isNotNullBlank(payment_record_file):
            payment_record_file_rc = prepare_upload_file(
                hdr_rc.office, ESFileManager.FileCategory.PAYMENT_RECORD, payment_record_file)
            payment_record_fileID, payment_record_fileSeq = payment_record_file_rc.id, payment_record_file_rc.seq

        pay_date = datetime.now()
        hdr_rc.sts = Status.SETTLED.value
        hdr_rc.pay_amt = hdr_rc.claim_amt
        hdr_rc.payment_tp = payment_tp
        hdr_rc.payment_number = payment_number
        hdr_rc.payment_record_file = payment_record_file_rc

        approve_activity = None
        if is_submitted_to_settle or is_first_approved_to_settle:
            approve_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=pay_date,
                                        operator=operator_rc, sts=Status.APPROVED.value, dsc='Automatic approved.')
            hdr_rc.approve_activity = approve_activity
            hdr_rc.last_activity = approve_activity

        pay_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, operate_dt=pay_date,
                                operator=operator_rc, sts=Status.SETTLED.value, dsc=payment_rmk)
        hdr_rc.payment_activity = pay_activity
        hdr_rc.last_activity = pay_activity

        trn = IkTransaction(userID=operator_rc.id)
        if approve_activity is not None:
            trn.add(approve_activity)
        trn.add(pay_activity)
        if payment_record_file_rc is not None:
            trn.add(payment_record_file_rc)
        trn.modify(hdr_rc)
        result = trn.save(updateDate=pay_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Expense [%s] has been settled." % hdr_rc.sn)
    except Exception as e:
        logger.error("Settle expense [%s] failed: %s" % (hdr_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        try:
            if not is_success:
                if isNotNullBlank(payment_record_fileSeq):  # rollback file seq
                    try:
                        newSeq = SnManager.rollbackSeq(
                            SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE, hdr_rc.office, payment_record_fileSeq, exact=True)
                        if newSeq != payment_record_fileSeq - 1:
                            logger.warning("Rollback payment record file sequence failed. Current=%s, Rollback Sequence=%s" % (newSeq, payment_record_fileSeq))
                    except Exception as e:
                        logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE.value, payment_record_fileSeq, str(e)), e, exc_info=True)
                if isNotNullBlank(payment_record_fileID):
                    try:
                        if not ESFileManager.rollbackFileRecord(operator_id, payment_record_fileID):
                            logger.error('Delete echeque file [%s] failed.' % payment_record_fileID)
                    except Exception as e:
                        logger.error('Delete echeque file [%s] failed: %s' % (payment_record_fileID, str(e)), e, exc_info=True)
        except Exception as e:
            logger.error('Rollback the uploaded payment record file failed. %s' % str(e), e, exc_info=True)

        __EXPENSE_LOCK.release()
        __FILE_UPLOAD_SYNCHRONIZED.release()


def revert_settled_expense(operator_id: int, expense_hdr_id: int, reason: str) -> Boolean2:
    operator_rc = UserManager.getUser(operator_id)
    if operator_rc is None:
        logger.error("Claimer doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(expense_hdr_id):
        logger.error("Parameter [expense_hdr_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    if isNullBlank(reason):
        return Boolean2.FALSE("Revert Settled Payment Reason is mandatory.")
    reason = str(reason).strip()

    is_success = False
    hdr_rc = None
    payment_record_file_rc = None
    __EXPENSE_LOCK.acquire()
    __FILE_UPLOAD_SYNCHRONIZED.acquire()
    try:
        # validate
        hdr_rc = acl.add_query_filter(Expense.objects, operator_rc).filter(id=expense_hdr_id).first()
        if hdr_rc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_hdr_id)
            return Boolean2.FALSE("Expense doesn't exist.")

        validate_status_result = validate_status_transition(hdr_rc.sts, Status.SUBMITTED)
        if not validate_status_result.value:
            return validate_status_result

        if not acl.can_revert_settled_payment(operator_rc, hdr_rc.sts, hdr_rc.office):
            logger.error("You don't have permission to revert this settled expense. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (hdr_rc.id, hdr_rc.sn, operator_rc.id, operator_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to revert this settled expense.")

        # check this payment is from submitted status or approved status
        last_approve_activity_rc = Activity.objects.filter(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, sts=Status.APPROVED.value).order_by('-id').first()
        last_settled_activity_rc = Activity.objects.filter(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id, sts=Status.SETTLED.value).order_by('-id').first()
        is_settled_from_submitted = (last_approve_activity_rc.cre_usr.id ==
                                     last_settled_activity_rc.cre_usr.id and last_approve_activity_rc.cre_dt == last_settled_activity_rc.cre_dt)

        revert_date = datetime.now()
        hdr_rc.sts = Status.SUBMITTED.value if is_settled_from_submitted else Status.APPROVED.value
        payment_record_file_rc = hdr_rc.payment_record_file
        hdr_rc.payment_record_file = None
        hdr_rc.pay_amt = None
        hdr_rc.payment_activity = None
        hdr_rc.payment_tp = None
        hdr_rc.payment_number = None

        revert_settled_payment_activity = Activity(tp=ActivityType.EXPENSE.value, transaction_id=hdr_rc.id,
                                                   operate_dt=revert_date, operator=operator_rc, sts=hdr_rc.sts, dsc="[Revert settled payment.] Reason: " + reason)
        hdr_rc.last_activity = revert_settled_payment_activity

        trn = IkTransaction(userID=operator_id)
        trn.add(revert_settled_payment_activity)
        trn.modify(hdr_rc)
        result = trn.save(updateDate=revert_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Revert settled expense [%s] to %s." % (hdr_rc.sn, hdr_rc.sts))
    except Exception as e:
        logger.error("Revert settled expense [%s] failed: %s" % (hdr_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        try:
            if is_success:
                ESNotification.send_submit_cancel_reject_expense_notify(operator_id, hdr_rc)
                # try to rollback the sequence if the current sequence is the last one
                payment_record_fileID = payment_record_file_rc.id if isNotNullBlank(payment_record_file_rc) else None
                payment_record_fileSeq = payment_record_file_rc.seq if isNotNullBlank(payment_record_file_rc) else None
                if isNotNullBlank(payment_record_fileSeq):  # rollback file seq
                    try:
                        SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE, hdr_rc.office, payment_record_fileSeq)
                    except Exception as e:
                        logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE.value, payment_record_fileSeq, str(e)), e, exc_info=True)
                if isNotNullBlank(payment_record_fileID):
                    try:
                        if not ESFileManager.rollbackFileRecord(operator_id, payment_record_fileID):
                            logger.error('Delete echeque file [%s] failed.' % payment_record_fileID)
                    except Exception as e:
                        logger.error('Delete echeque file [%s] failed: %s' % (payment_record_fileID, str(e)), e, exc_info=True)
        except Exception as e:
            logger.error('Rollback the uploaded payment record file failed. %s' % str(e), e, exc_info=True)

        __EXPENSE_LOCK.release()
        __FILE_UPLOAD_SYNCHRONIZED.release()


def getCashAdvancedPriorBalance(payeeID: int, deadline: datetime) -> float:
    with connection.cursor() as cursor:
        cursor.execute("SELECT wci_es_get_total_cash_advanced_balance(" + str(payeeID) +
                       "," + dbUtils.toSqlField(deadline.strftime('%Y-%m-%d %H:%M:%S')) + ")")
        results = dbUtils.dictfetchall(cursor)
        return results[0]['wci_es_get_total_cash_advanced_balance']


def checkExpenseFileAccessPermission(expense_id: int, fileID: int, requesterRc: User, officeID: int = None, validateClaimerOnly: bool = False) -> Boolean2:
    """
        Only allow file's owner, approver, accounting and sysadmin can read the file.
    """
    hdrRc = acl.add_query_filter(Expense.objects, requesterRc).filter(id=expense_id).first()
    if hdrRc is None:
        logger.error("Expense doesn't exists. ID=%s" % expense_id)
        return Boolean2(False, "Expense doesn't exist.")
    fileRc = File.objects.filter(id=fileID).first()
    if fileRc is None:
        logger.error("File doesn't exists. ID=%s" % fileID)
        return Boolean2(False, "File doesn't exist.")
    if requesterRc is None:
        logger.error("Requester doesn't exists.")
        return Boolean2(False, "Requester doesn't exist.")

    # check office
    office_rc = None
    if isNotNullBlank(officeID):
        office_rc = get_office_by_id(officeID)
        if office_rc is None:
            logger.error("Office doesn't exists. ID=%s" % officeID)
            return Boolean2(False, "Office doesn't exist.")
    if office_rc is None:
        office_rc = hdrRc.office
    elif office_rc.id != hdrRc.office.id:
        return Boolean2(False, "The specified office is not the same as expense's office.")
        # TODO: check the request can access to specified office or not

    # check the file is belong to this expense or not
    if isNullBlank(hdrRc.supporting_doc) or hdrRc.supporting_doc.id != fileRc.id:
        if hdrRc.sts == Status.DRAFT.value:
            draftFileRc = DraftFile.objects.filter(tp=DraftFile.EXPENSE, claimer=requesterRc, file=fileRc)
            if office_rc is not None:
                draftFileRc = draftFileRc.filter(office=office_rc)
            draftFileRc = draftFileRc.first()
            if draftFileRc is None:
                return Boolean2(False, "The draft file doesn't belong to this expense.")
        else:
            # check expense file and payment file
            expenseRc = ExpenseDetail.objects.filter(hdr=hdrRc, file=fileRc)
            if expenseRc is None and isNotNullBlank(hdrRc.pay) and isNotNullBlank(hdrRc.pay.pay_file) and hdrRc.pay.pay_file.id != fileRc.id:
                return Boolean2(False, "The file doesn't exist in this expense.")

    # check requester's permission
    if hdrRc.claimer.id == requesterRc.id:  # Only the claimer can access to his draft file.
        return Boolean2(True, "Requester is the expense's owner.")
    elif hdrRc.sts == Status.DRAFT.value:
        return Boolean2(False, "Only claimer can access to this draft expense.")
    if validateClaimerOnly:
        return Boolean2(False, "Permission deny. Only allow claimer can access to this file.")
    # check requester
    if acl.is_office_admin(requesterRc, office_rc):
        return Boolean2(True, "Admin")
    if isNotNullBlank(hdrRc.approver) and hdrRc.approver.id == requesterRc.id:
        return Boolean2(True, "User is the default approver.")
    # check the accounting
    fpRc = Accounting.objects.filter(office=office_rc, usr=requesterRc).first()
    if fpRc is not None:
        return Boolean2(True, "Requester is finance personnel for office [%s]." % office_rc.name)
    return Boolean2(False, "Permission deny.")


def __validateExpensePriorBalance(hdrRc: Expense) -> None:
    """Raise IkValidateException if validate failed.
    """
    pbRcs = PriorBalance.objects.filter(expense=hdrRc)
    if len(pbRcs) == 0:
        raise IkValidateException("Prior Balance record doesn't found.")
    pbAmount = 0
    for pbRc in pbRcs:
        pbAmount = ESTools.round2(ESTools.add(pbAmount, pbRc.claim_amt))
    if abs(float(ESTools.sub(hdrRc.claim_amt, ESTools.add(pbAmount, hdrRc.pay_amt)))) > 0.000001:
        raise IkValidateException("Claim amount doesn't equal to (pay amount + prior balance amount). Please check.")


def uploadExpenseSupportingDocument(operatorID: int, expense_rc: Expense, temp_upload_file: Path) -> tuple:
    """
        upload expense supporting document file

        return (fileID, fileSeq)
    """
    user_rc = UserManager.getUser(operatorID)
    if user_rc is None:
        logger.error('Operator [%s] does not exist.' % operatorID)
        raise IkValidateException('Operator does not exist.')

    if expense_rc is None:
        raise IkValidateException('Expense is not found. Please check.')
    expense_rc = acl.add_query_filter(Expense.objects, user_rc).filter(id=expense_rc.id).first()

    if temp_upload_file is None:
        raise IkValidateException('Parameter [tempUploadFile] is mandatory.')
    elif not Path(temp_upload_file).is_file():
        raise IkValidateException('File [%s] does not exist.' % temp_upload_file)
    # only pdf allow
    file_type = (temp_upload_file if isinstance(temp_upload_file, Path) else Path(temp_upload_file)).suffix[1:]
    if file_type.upper() != 'PDF':
        raise IkValidateException('Only accept PDF file.')

    old_file_rc = None
    new_file_rc = None
    is_success = False
    getFileUploadLock().acquire()
    try:
        if expense_rc.sts == Status.DRAFT.value \
                or expense_rc.sts == Status.CANCELLED.value \
            or expense_rc.sts == Status.REJECTED.value \
                or expense_rc.sts == Status.FIRST_APPROVED.value \
                or expense_rc.sts == Status.SUBMITTED.value:
            if (expense_rc.sts == Status.CANCELLED.value or expense_rc.sts == Status.REJECTED.value) and expense_rc.claimer.id != operatorID:
                logger.error('Permission deny. Only expense claimer can upload file to this expense. expense_id=%s, operatorID=%s' %
                             (expense_rc.id, operatorID))
                raise IkValidateException('Permission deny. Only expense claimer can upload file to this expense.')
            elif expense_rc.sts == Status.SUBMITTED.value or expense_rc.sts == Status.FIRST_APPROVED.value:
                if not acl.is_approverable(user_rc, expense_rc.sts, expense_rc.payee, expense_rc.claim_amt, expense_rc.approver):
                    logger.error('Permission deny. Only approver can overwrite the supporting document.. expense_id=%s, operatorID=%s' %
                                 (expense_rc.id, operatorID))
                    raise IkValidateException('Permission deny. Only approver can overwrite the supporting document.')
        else:
            logger.error('Permission deny. Only approver can overwrite the submitted supporting document.. expense_id=%s, operatorID=%s' %
                         (expense_rc.id, operatorID))
            raise IkValidateException('Permission deny. Only approver can overwrite the submitted supporting document.')

        # check the old file exists or not
        is_draft = expense_rc.sts == Status.DRAFT.value
        old_file_rc = expense_rc.supporting_doc
        # submitted: use the new sequence
        new_file_rc = prepare_upload_file(expense_rc.office, ESFileManager.FileCategory.SUPPORTING_DOCUMENT,
                                          temp_upload_file, old_file_rc.seq if (is_draft and isNotNullBlank(old_file_rc)) else None)
        if isNotNullBlank(old_file_rc) and old_file_rc.sha256 == new_file_rc.sha256:
            raise IkValidateException("The uploaded file is the same as previous file. Please check.")

        expense_rc.supporting_doc = new_file_rc

        pytrn = IkTransaction(userID=operatorID)
        if isNotNullBlank(old_file_rc):
            pytrn.delete(old_file_rc)
        pytrn.add(new_file_rc)
        pytrn.modify(expense_rc)
        b = pytrn.save()
        if not b.value:
            raise IkValidateException(b.dataStr)
        is_success = True
    except IkException as e:
        logger.error('Upload expense file failed: %s' % str(e), e, exc_info=True)
        raise e
    except Exception as e:
        logger.error('Upload expense file failed: %s' % str(e), e, exc_info=True)
        raise IkException('System error, please ask administrator to check.')
    finally:
        try:
            if not is_success:
                if isNotNullBlank(new_file_rc):
                    if isNotNullBlank(new_file_rc.seq):  # rollback file seq
                        try:
                            SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_SUPPORTING_DOCUMENT, expense_rc.office, new_file_rc.seq)
                        except Exception as e:
                            logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                         (SnManager.SequenceType.SEQ_TYPE_SUPPORTING_DOCUMENT.value, new_file_rc.seq, str(e)), e, exc_info=True)
                    if isNotNullBlank(new_file_rc.id):
                        try:
                            if not ESFileManager.rollbackFileRecord(operatorID, new_file_rc.id):
                                logger.error('Delete echeque file [%s] failed.' % new_file_rc.id)
                        except Exception as e:
                            logger.error('Delete echeque file [%s] failed: %s' % (new_file_rc.id, str(e)), e, exc_info=True)
            else:  # success
                if isNotNullBlank(old_file_rc):
                    if isNotNullBlank(old_file_rc.id):
                        try:
                            if not ESFileManager.rollbackFileRecord(operatorID, old_file_rc.id):
                                logger.error('Delete echeque file [%s] failed.' % old_file_rc.id)
                        except Exception as e:
                            logger.error('Delete echeque file [%s] failed: %s' % (old_file_rc.id, str(e)), e, exc_info=True)
        except:
            logger.error('Upload expense file failed when do the finally: %s' % str(e))
            logger.error(e, exc_info=True)
        getFileUploadLock().release()
        if isNotNullBlank(temp_upload_file) and temp_upload_file.is_file():
            logger.debug('Delete temp upload file: %s' % temp_upload_file)
            try:
                Path(temp_upload_file).unlink()
            except Exception as e:
                logger.error('delete the temp file [%s] failed: %s' % (temp_upload_file.absolute(), str(e)))
                logger.error(e, exc_info=True)
    return (new_file_rc.id, new_file_rc.seq) if is_success else (None, None)


def deleteExpenseSupportingDocument(operatorID: int, expenseHdrRc: Expense) -> int:
    """
        delete expense supporting document file
    """
    claimer_rc = UserManager.getUser(operatorID)
    if claimer_rc is None:
        logger.error('Operator [%s] does not exist.' % operatorID)
        raise IkValidateException('Operator does not exist.')

    if expenseHdrRc is None:
        raise IkValidateException('Expense is not found. Please check.')
    elif isNullBlank(expenseHdrRc.supporting_doc):
        raise IkValidateException("Supporting document doesn't exist.")

    fileID, fileSeq, supporting_doc_file_path = None, None, None
    is_success = False
    getFileUploadLock().acquire()
    try:
        # check the old file exists or not
        uploadFileRc = expenseHdrRc.supporting_doc
        fileID, fileSeq = uploadFileRc.id, uploadFileRc.seq
        supporting_doc_file_path = ESFileManager.getReallyFile(uploadFileRc)
        expenseHdrRc.supporting_doc = None

        pytrn = IkTransaction(userID=operatorID)
        pytrn.modify(expenseHdrRc)
        pytrn.delete(uploadFileRc)
        b = pytrn.save()
        if not b.value:
            raise IkValidateException(b.dataStr)
        logger.info("[%s] delete the supporting document in office [%s]. FileID=%s, FileSeq=%s, ExpenseHdrID=%s" %
                    (claimer_rc.usr_nm, expenseHdrRc.office.code, fileID, fileSeq, expenseHdrRc.id))
        is_success = True
    except IkException as e:
        logger.error('Upload expense file failed: %s' % str(e), e, exc_info=True)
        raise e
    except Exception as e:
        logger.error('Upload expense file failed: %s' % str(e), e, exc_info=True)
        logger.error(e, exc_info=True)
        raise IkException('System error, please ask administrator to check.')
    finally:
        try:
            if is_success:
                if isNotNullBlank(fileSeq):  # rollback file seq
                    try:
                        SnManager.rollbackSeq(SnManager.SequenceType.SEQ_TYPE_SUPPORTING_DOCUMENT, expenseHdrRc.office, fileSeq)
                    except Exception as e:
                        logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_SUPPORTING_DOCUMENT.value, fileSeq, str(e)), e, exc_info=True)
                if isNotNullBlank(fileID):
                    try:
                        if not ESFileManager.rollbackFileRecord(operatorID, fileID):
                            logger.error('Delete echeque file [%s] failed.' % fileID)
                    except Exception as e:
                        logger.error('Delete echeque file [%s] failed: %s' % (fileID, str(e)), e, exc_info=True)
                    try:
                        # delete the file
                        ESFileManager.deleteESFileAndFolder(supporting_doc_file_path)
                    except Exception as e:
                        logger.error('Delete echeque file [%s] failed: %s' % (fileID, str(e)), e, exc_info=True)
        except:
            logger.error('Upload expense file failed when do the finally: %s' % str(e))
            logger.error(e, exc_info=True)
        getFileUploadLock().release()
    return fileID if is_success else None


def getExpenseSupportingDocumentFilename(fileRc: File) -> str:
    f = ESFileManager.getFile(fileRc.id)
    fileType = Path(f).suffix[1:]
    sn = SnManager.getSupportingDocumentFileSN(fileRc.seq)
    return "%s.%s" % (sn, fileType)


def query_expenses(retriever: User, office_rc: Office, expense_queryset: QuerySet, query_parameters: dict) -> QuerySet:
    if retriever is None:
        raise IkValidateException("Parameter [receiver] is mandatory.")
    if office_rc is None:
        raise IkValidateException("Parameter [office_rc] is mandatory.")
    if expense_queryset is None:
        raise IkValidateException("Parameter [expense_queryset] is mandatory.")
    elif not issubclass(expense_queryset.model, Expense):
        raise IkValidateException("Parameter [expense_queryset] should be a Expense instance.")
    if query_parameters is None:
        query_parameters = {}

    # Add base query ACL (Access Control List)
    expense_queryset = acl.add_query_filter(expense_queryset, retriever)

    # add query prms
    def get_prm(name: str) -> object:
        prm = query_parameters.get(name, None)
        if type(prm) == str:
            prm = prm.strip()
        return prm
    query_id = get_prm('id')
    query_sn = get_prm('sn')
    query_po = get_prm('po')
    query_status = get_prm('status')
    query_claimer = get_prm('claimer')
    query_payee = get_prm('payee')
    query_expense_page_no = get_prm('expense_page_no')
    query_payment_record_page_no = get_prm('payment_record_page_no')
    query_payment_record_filename = get_prm('payment_record_filename')
    query_support_document_page_no = get_prm('support_document_page_no')
    query_claim_date_from = get_prm('claim_date_from')
    query_claim_date_to = get_prm('claim_date_to')
    query_approved_date_from = get_prm('approve_date_from')
    query_approved_date_to = get_prm('approve_date_to')
    query_settle_date_from = get_prm('settle_date_from')
    query_settle_date_to = get_prm('settle_date_to')
    query_cat = get_prm('cat')
    query_prj_nm = get_prm('prj_nm')
    query_desc = get_prm('description')

    def get_page_nos(page_no_str) -> list[int]:
        page_nos = [int]
        for page_no1 in str(query_payment_record_page_no).split(","):
            if page_no1.strip() != '':
                for page_no2 in str(page_no1).split(" "):
                    if page_no2.strip() != '':
                        try:
                            page_nos.append(int(page_no2))
                        except:
                            pass
        return page_nos

    if isNotNullBlank(query_id):
        expense_queryset = expense_queryset.filter(id=query_id)
    else:
        if isNotNullBlank(query_sn):
            expense_queryset = expense_queryset.filter(sn__icontains=query_sn)
        if isNotNullBlank(query_po):
            expense_queryset = expense_queryset.filter(po__sn__icontains=query_po)
        if isNotNullBlank(query_status):
            expense_queryset = expense_queryset.filter(sts=query_status)
        if isNotNullBlank(query_claimer):
            expense_queryset = expense_queryset.filter(claimer__usr_nm__icontains=query_claimer)
        if isNotNullBlank(query_payee):
            expense_queryset = expense_queryset.filter(payee__payee__icontains=query_payee)
        if isNotNullBlank(query_support_document_page_no):
            page_nos = query_payment_record_page_no(query_support_document_page_no)
            if len(page_nos) > 0:
                expense_queryset = expense_queryset.filter(supporting_doc__seq__in=page_nos)
        if isNotNullBlank(query_expense_page_no):
            page_nos = get_page_nos(query_payment_record_page_no)
            if len(page_nos) > 0:
                page_no_subquery = ExpenseDetail.objects.filter(hdr=OuterRef('pk'), file__seq=page_nos)
                expense_queryset = expense_queryset.filter(Exists(page_no_subquery))
        if isNotNullBlank(query_expense_page_no):
            page_nos = query_payment_record_page_no(query_payment_record_page_no)
            if len(page_nos) > 0:
                expense_queryset = expense_queryset.filter(payment_record_file__seq__in=page_nos)
        if isNotNullBlank(query_payment_record_filename):
            expense_queryset = expense_queryset.filter(payment_record_file__file_original_nm__icontains=query_payment_record_filename)
        if isNotNullBlank(query_claim_date_from):
            query_claim_date_from = datetime.strptime(query_claim_date_from, "%Y-%m-%d")
            expense_queryset = expense_queryset.filter(submit_dt__gte=make_aware(
                datetime(query_claim_date_from.year, query_claim_date_from.month, query_claim_date_from.day, 0, 0, 0)))
        if isNotNullBlank(query_claim_date_to):
            query_claim_date_to = datetime.strptime(query_claim_date_to, "%Y-%m-%d")
            nextDay = query_claim_date_to + timedelta(days=1)
            expense_queryset = expense_queryset.filter(submit_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0)))
        if isNotNullBlank(query_approved_date_from):
            query_approved_date_from = datetime.strptime(query_approved_date_from, "%Y-%m-%d")
            expense_queryset = expense_queryset.filter(Q(approve2_activity__isnull=False, approve2_activity__sts=Status.APPROVED.value, approve2_activity__operate_dt__gte=make_aware(datetime(query_approved_date_from.year, query_approved_date_from.month, query_approved_date_from.day, 0, 0, 0)))
                                                       | Q(approve2_activity__isnull=True, approve_activity__isnull=False, approve_activity__sts=Status.APPROVED.value, approve_activity__operate_dt__gte=make_aware(datetime(query_approved_date_from.year, query_approved_date_from.month, query_approved_date_from.day, 0, 0, 0))))
        if isNotNullBlank(query_approved_date_to):
            query_approved_date_to = datetime.strptime(query_approved_date_to, "%Y-%m-%d")
            nextDay = query_approved_date_to + timedelta(days=1)
            expense_queryset = expense_queryset.filter(Q(approve2_activity__isnull=False, approve2_activity__sts=Status.APPROVED.value, approve2_activity__operate_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0)))
                                                       | Q(approve2_activity__isnull=True, approve_activity__isnull=False, approve_activity__sts=Status.APPROVED.value, approve_activity__operate_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0))))
        if isNotNullBlank(query_settle_date_from):
            query_settle_date_from = datetime.strptime(query_settle_date_from, "%Y-%m-%d")
            expense_queryset = expense_queryset.filter(payment_activity__operate_dt__gte=make_aware(
                datetime(query_settle_date_from.year, query_settle_date_from.month, query_settle_date_from.day, 0, 0, 0)))
        if isNotNullBlank(query_settle_date_to):
            query_settle_date_to = datetime.strptime(query_settle_date_to, "%Y-%m-%d")
            nextDay = query_settle_date_to + timedelta(days=1)
            expense_queryset = expense_queryset.filter(payment_activity__operate_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0)))
        if isNotNullBlank(query_cat):
            expense_queryset = expense_queryset.filter(expensedetail__cat__cat__icontains=query_cat)
        if isNotNullBlank(query_prj_nm):
            expense_queryset = expense_queryset.filter(expensedetail__prj_nm__icontains=query_prj_nm)
        if isNotNullBlank(query_desc):
            expense_queryset = expense_queryset.filter(Q(dsc__icontains=query_desc) | Q(expensedetail__dsc__icontains=query_desc))
    return expense_queryset.distinct()
