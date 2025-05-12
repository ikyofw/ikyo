"""Cash Advancement Manager
"""
import datetime
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

from django.db.models import Exists, OuterRef, Q, QuerySet, Sum
from django.utils.timezone import make_aware

import core.user.userManager as UserManager
import es.core.acl as acl
import es.core.ESFile as ESFileManager
import es.core.ESSeq as SnManager
import es.core.ESTools as ESTools
from core.core.exception import IkValidateException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.log.logger import logger
from core.utils.langUtils import isNotNullBlank, isNullBlank
from es.core import ES, ESSeq

from ..models import (Activity, Approver, AvailablePriorBalance,
                      CashAdvancement, Currency, Expense, ForeignExchange,
                      Office, Payee, PaymentMethod, Po, PriorBalance, User,
                      UserOffice)
from . import ESNotification, acl
from . import approver as ApproverManager
from . import po as po_manager
from .activity import ActivityType
from .finance import round_currency, round_rate
from .status import Status, validate_status_transition

__CA_NEW_LOCK = Lock()
__CA_OPERATION_LOCK = Lock()


__CASH_ADVANCEMENT_ACCEPT_EXPENSE_STATUS = (Status.SUBMITTED.value,
                                            Status.FIRST_APPROVED.value,
                                            Status.APPROVED.value,
                                            Status.SETTLED.value)


def submit_cash_advancement(claimer_id: int, cash_advancement_id: int, office_rc: Office, ccy_rc: Currency, payee_rc: Payee,
                            description: str, advance_amount: float, po_sn: str, approver_rc: User) -> Boolean2:
    # base validation
    claimer_rc = UserManager.getUser(claimer_id)
    if isNullBlank(claimer_rc):
        logger.error("Claimer doesn't exist. ID=%s" % claimer_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(office_rc):
        return Boolean2.FALSE("Office is mandatory.")
    if UserOffice.objects.filter(usr=claimer_rc, office=office_rc).first() is None:
        return Boolean2.FALSE("The applicant does not belong to office %s. Please verify." % office_rc.code)
    if isNullBlank(approver_rc):
        return Boolean2.FALSE("Approver is mandatory.")
    if isNullBlank(ccy_rc):
        return Boolean2.FALSE("Currency is mandatory.")
    elif ccy_rc.id != office_rc.ccy.id:
        logger.error("The office's default currency is [%s], but claimer submit the different currency [%s]. Please check." % (
            office_rc.ccy.code, ccy_rc.code))
        return Boolean2.FALSE("The office's default currency is [%s]. Please check." % (office_rc.ccy.code))
    if isNullBlank(payee_rc):
        return Boolean2.FALSE("Payee is mandatory.")
    elif payee_rc.office.id != office_rc.id:
        return Boolean2.FALSE("The payee's office and the applying office do not match. Please verify.")
    if not isinstance(advance_amount, int) and not isinstance(advance_amount, float):
        return Boolean2.FALSE("Advance Amount is mandatory.")
    advance_amount = ESTools.round2(float(advance_amount))
    if advance_amount <= 0:
        return Boolean2.FALSE("Advance Amount cannot less than 0.01.")
    description = str(description).strip() if isNotNullBlank(description) else None
    if isNullBlank(description):
        return Boolean2.FALSE("Description is mandatory.")
    # validate approver
    ApproverManager.validate_approver_result = ApproverManager.validate_approver(office_rc, claimer_rc, approver_rc, approver_rc, advance_amount, True)
    if not ApproverManager.validate_approver_result.value:
        return ApproverManager.validate_approver_result

    is_new = isNullBlank(cash_advancement_id)
    is_success = False
    ca_rc = None
    __CA_NEW_LOCK.acquire()
    try:
        # validate cancelled/rejected cash advancement
        if isNotNullBlank(cash_advancement_id):
            ca_rc = acl.add_query_filter(CashAdvancement.objects, claimer_rc).filter(id=cash_advancement_id).first()
            if ca_rc is None:
                logger.error("Cash advancement doesn't exist. ID=%s" % cash_advancement_id)
                return Boolean2.FALSE("Cash advancement doesn't exist.")
            elif ca_rc.claimer.id != claimer_id:
                logger.error("You are not the claimant of this record, so you don't have the authority to submit. This cash advancement is created by [%s]. ID=%s" % (
                    ca_rc.claimer.usr_nm, cash_advancement_id))
                return Boolean2.FALSE("You are not the claimant of this record, so you don't have the authority to submit.")
            elif ca_rc.office.id != office_rc.id:
                logger.error("System error. The database office [%s] is not the same as request office [%s]." % (ca_rc.office.code, office_rc.code))
                return Boolean2.FALSE("The current cash advancement does not match the selected office %s. Please verify." % office_rc.code)

            validate_status_result = validate_status_transition(ca_rc.sts, Status.SUBMITTED)
            if not validate_status_result.value:
                return validate_status_result
            # elif ca_rc.sts != Status.CANCELLED.value and ca_rc.sts != Status.REJECTED.value:
            #     logger.error("Only cancelled and rejected cash advancement can be edited. Please check. ID=%s, Current status is [%s]" % (
            #         cash_advancement_id, ca_rc.sts))
            #     return Boolean2.FALSE("Only cancelled and rejected cash advancement can be edited. Please check.")
        else:
            ca_rc = CashAdvancement()

        # validate purchase order No.
        po_rc = None
        if isNotNullBlank(po_sn):
            po_sn = str(po_sn).strip()
            b = po_manager.validate_po_permission(claimer_rc, po_sn)
            if not b.value:
                raise IkValidateException(b.data)
            po_rc = Po.objects.filter(sn=po_sn).first()
            # the purchase order no cannot exists in other cash advancements.
            other_ca_rcs = acl.add_query_filter(CashAdvancement.objects, claimer_rc).filter(po__sn__iexact=po_sn, office=office_rc)
            if not is_new:
                other_ca_rcs = other_ca_rcs.exclude(id=ca_rc.id)
            other_ca_rcs = other_ca_rcs.exclude(sts=Status.CANCELLED.value).exclude(sts=Status.REJECTED.value).order_by('-id')
            if len(other_ca_rcs) > 0:
                errorMessage = "Purchase order No. [%s] exists in cash advancement [%s]. Please check." % (po_sn, other_ca_rcs[0].sn)
                logger.error(errorMessage)
                return Boolean2.FALSE(errorMessage)

        submit_date = datetime.now()
        if is_new:
            # need to rollback if failed.
            ca_rc.sn = ESSeq.getNextSN(ESSeq.SequenceType.SEQ_TYPE_CASH_ADVANCEMENT_SN, office_rc.id)
        ca_rc.sts = Status.SUBMITTED.value
        ca_rc.office = office_rc
        ca_rc.ccy = ccy_rc
        ca_rc.claimer = claimer_rc
        ca_rc.claim_amt = advance_amount
        ca_rc.claim_dt = submit_date
        ca_rc.payee = payee_rc
        ca_rc.approver = approver_rc
        ca_rc.po = po_rc
        ca_rc.dsc = description
        ca_rc.assignPrimaryID()

        # add activity
        submit_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=submit_date, operator=claimer_rc, sts=ca_rc.sts)
        ca_rc.last_activity = submit_activity

        trn = IkTransaction(userID=claimer_id)
        trn.add(submit_activity)
        if is_new:
            trn.add(ca_rc)
        else:
            trn.modify(ca_rc)
        saveResult = trn.save(updateDate=submit_date)
        if not saveResult.value:
            logger.error("Save failed: %s" % saveResult.value)
            return saveResult
        is_success = True
        return Boolean2(True, ca_rc.id)
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        try:
            if not is_success:
                if is_new and isNotNullBlank(ca_rc) and isNotNullBlank(ca_rc.sn):
                    logger.info('Rollback office [%s] sequence [%s][%s].' % (office_rc.code, ESSeq.SequenceType.SEQ_TYPE_CASH_ADVANCEMENT_SN.value, ca_rc.sn))
                    ESSeq.rollbackSeq(ESSeq.SequenceType.SEQ_TYPE_CASH_ADVANCEMENT_SN, office_rc, ESSeq.SN2Number(ca_rc.sn))
        except Exception as e:
            logger.error("Rollback cash advancement sequence [%s] failed: %s" % (ca_rc.sn, str(e)), e, exc_info=True)
        __CA_NEW_LOCK.release()
        if is_success:
            ESNotification.send_submit_cancel_reject_cash_advancement_notify(claimer_id, ca_rc)


def cancel_cash_advancement(operator_id: int, cash_advancement_id: int, cancel_reason: str) -> Boolean2:
    # base validation
    operator_rc = UserManager.getUser(operator_id)
    if isNullBlank(operator_rc):
        logger.error("Operator doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Operator doesn't exist.")
    if isNullBlank(cash_advancement_id):
        logger.error("Parameter [cash_advancement_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    if isNullBlank(cancel_reason):
        logger.error("Cancel reason is mandatory.")
        return Boolean2.FALSE("Please fill in the Cancel Reason first.")
    cancel_reason = str(cancel_reason).strip()

    is_success = False
    __CA_OPERATION_LOCK.acquire()
    try:
        # validate
        ca_rc = acl.add_query_filter(CashAdvancement.objects, operator_rc).filter(id=cash_advancement_id).first()
        if ca_rc is None:
            logger.error("Cash advancement doesn't exist. ID=%s" % cash_advancement_id)
            return Boolean2.FALSE("Cash advancement doesn't exist.")
        if ca_rc.claimer.id != operator_id:
            logger.error("User %s doesn't have permission to cancel cash advancement %s." % (operator_rc.usr_nm, ca_rc.sn))
            return Boolean2.FALSE("Permission deny!")
        validate_status_result = validate_status_transition(ca_rc.sts, Status.CANCELLED)
        if not validate_status_result.value:
            return validate_status_result

        # elif ca_rc.claimer.id != operator_rc.id:
        #     logger.error("You are not the claimant of this record, so you don't have the authority to submit. This cash advancement is created by [%s]. ID=%s" % (ca_rc.claimer.usr_nm, cash_advancement_id))
        #     return Boolean2.FALSE("You are not the claimant of this record, so you don't have the authority to submit.")
        # elif ca_rc.sts != Status.SUBMITTED.value:
        #     logger.error("Only submitted cash advancement can be cancelled. Please check. ID=%s, Current status is [%s]" % (cash_advancement_id, ca_rc.sts))
        #     return Boolean2.FALSE("Only submitted cash advancement can be cancelled. Please check.")

        # if not acl.is_cancelable(ca_rc.sts, ca_rc.claimer.id, operator_rc.id):
        #     logger.error("You don't have permission to cancel this cash advancement. ID=%s, Current status is [%s]" % (
        #         cash_advancement_id, ca_rc.sts))
        #     return Boolean2.FALSE("You don't have permission to cancel this cash advancement.")

        cancel_date = datetime.now()
        ca_rc.sts = Status.CANCELLED.value

        cancel_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=cancel_date, operator=operator_rc, sts=ca_rc.sts, dsc=cancel_reason)
        ca_rc.last_activity = cancel_activity

        trn = IkTransaction(userID=operator_rc.id)
        trn.add(cancel_activity)
        trn.modify(ca_rc)
        result = trn.save(updateDate=cancel_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Cash advancement [%s] has been cancelled." % ca_rc.sn)
    except Exception as e:
        logger.error("Cancel cash advancement [%s] failed: %s" % (
            ca_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        __CA_OPERATION_LOCK.release()
        if is_success:
            ESNotification.send_submit_cancel_reject_cash_advancement_notify(operator_id, ca_rc)


def reject_cash_advancement(operator_id: int, cash_advancement_id: int, reject_reason: str) -> Boolean2:
    rejector_rc = UserManager.getUser(operator_id)
    if isNullBlank(rejector_rc):
        logger.error("Claimer doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(cash_advancement_id):
        logger.error("Parameter [cash_advancement_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    if isNullBlank(reject_reason):
        return Boolean2.FALSE("Please fill in the Reject Reason first.")
    reject_reason = str(reject_reason).strip()

    is_success = False
    __CA_OPERATION_LOCK.acquire()
    try:
        # validate
        ca_rc = acl.add_query_filter(CashAdvancement.objects, rejector_rc).filter(id=cash_advancement_id).first()
        if ca_rc is None:
            logger.error("Cash advancement doesn't exist. ID=%s" %
                         cash_advancement_id)
            return Boolean2.FALSE("Cash advancement doesn't exist.")
        elif ca_rc.claimer.id == rejector_rc.id and not acl.is_office_admin(rejector_rc, ca_rc.office):
            logger.error("[%s] Please cancel this cash advancement instead of rejecting it. ID=%s" % (
                ca_rc.claimer.usr_nm, cash_advancement_id))
            return Boolean2.FALSE("Please cancel this cash advancement instead of rejecting it.")
        elif ca_rc.sts != Status.SUBMITTED.value and ca_rc.sts != Status.FIRST_APPROVED.value and ca_rc.sts != Status.APPROVED.value:
            logger.error("Only submitted or first approved or approved expense can be rejected. Please check. ID=%s, Current status is [%s]" % (
                cash_advancement_id, ca_rc.sts))
            return Boolean2.FALSE("Only submitted or first approved or approved expense can be rejected. Please check.")

        validate_status_result = validate_status_transition(ca_rc.sts, Status.REJECTED)
        if not validate_status_result.value:
            return validate_status_result
        if not acl.is_rejectable(rejector_rc, ca_rc.sts, ca_rc.payee, ca_rc.claim_amt, ca_rc.approver):
            logger.error("You don't have permission to reject this cash advancement. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (ca_rc.id, ca_rc.sn, rejector_rc.id, rejector_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to reject this cash advancement.")

        reject_date = datetime.now()
        ca_rc.sts = Status.REJECTED.value

        reject_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=reject_date, operator=rejector_rc, sts=ca_rc.sts, dsc=reject_reason)
        ca_rc.last_activity = reject_activity

        trn = IkTransaction(userID=rejector_rc.id)
        trn.add(reject_activity)
        trn.modify(ca_rc)
        result = trn.save(updateDate=reject_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Cash advancement [%s] has been rejected." % ca_rc.sn)
    except Exception as e:
        logger.error("Cancel cash advancement [%s] failed: %s" % (
            ca_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        __CA_OPERATION_LOCK.release()
        if is_success:
            ESNotification.send_submit_cancel_reject_cash_advancement_notify(operator_id, ca_rc)


def approve_cash_advancement(operator_id: int, cash_advancement_id: int) -> Boolean2:
    approver_rc = UserManager.getUser(operator_id)
    if isNullBlank(approver_rc):
        logger.error("Approver doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(cash_advancement_id):
        logger.error("Parameter [cash_advancement_id] is mandatory.")
        return Boolean2.FALSE("System error.")

    is_success = False
    ca_rc = None
    __CA_OPERATION_LOCK.acquire()
    try:
        # validate
        ca_rc = acl.add_query_filter(CashAdvancement.objects, approver_rc).filter(id=cash_advancement_id).first()
        if ca_rc is None:
            logger.error("Cash advancement doesn't exist. ID=%s" %
                         cash_advancement_id)
            return Boolean2.FALSE("Cash advancement doesn't exist.")
        # validate status
        validate_status_result = validate_status_transition(ca_rc.sts, Status.APPROVED)
        if not validate_status_result.value:
            return validate_status_result
        is_second_approval = ca_rc.sts == Status.FIRST_APPROVED.value
        is_final_approval = True
        # check need to second approve or not
        if ca_rc.sts == Status.SUBMITTED.value:
            if ApproverManager.is_need_second_approval(ca_rc.office, approver_rc, ca_rc.claim_amt):
                is_final_approval = False

        # validate approver
        if not acl.is_approverable(approver_rc, ca_rc.sts, ca_rc.payee, ca_rc.claim_amt, ca_rc.approver):
            logger.error("You don't have permission to approve this cash advancement. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (ca_rc.id, ca_rc.sn, approver_rc.id, approver_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to approve this cash advancement.")

        approve_date = datetime.now()
        ca_rc.sts = Status.APPROVED.value if is_final_approval else Status.FIRST_APPROVED.value
        approve_activity = None
        if is_second_approval:
            approve_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=approve_date, operator=approver_rc, sts=ca_rc.sts)
            ca_rc.approve2_activity = approve_activity
        else:
            approve_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=approve_date, operator=approver_rc, sts=ca_rc.sts)
            ca_rc.approve_activity = approve_activity
        ca_rc.last_activity = approve_activity

        trn = IkTransaction(userID=approver_rc.id)
        trn.add(approve_activity)
        trn.modify(ca_rc)
        result = trn.save(updateDate=approve_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Cash advancement [%s] has been approved." % ca_rc.sn)
    except Exception as e:
        logger.error("Approve cash advancement [%s] failed: %s" % (
            ca_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        __CA_OPERATION_LOCK.release()
        if is_success:
            ESNotification.send_approve_cash_advancement_notify(operator_id, ca_rc)


def settle_cash_advancement(operator_id: int, cash_advancement_id: int, payment_method_rc: PaymentMethod, payment_record_no: str, payment_record_file: Path, payment_remarks: str) -> Boolean2:
    operator_rc = UserManager.getUser(operator_id)
    if isNullBlank(operator_rc):
        logger.error("Claimer doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(cash_advancement_id):
        logger.error("Parameter [cash_advancement_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    # validate payment method
    if isNullBlank(payment_method_rc):
        return Boolean2.FALSE("Transaction Type doesn't exist.")
    # validate payment No.
    if isNullBlank(payment_record_no):
        return Boolean2.FALSE("Transfer No. is mandatory.")
    payment_record_no = str(payment_record_no).strip()
    # validate payment record file
    if isNullBlank(payment_record_file):
        return Boolean2.FALSE("Payment record file is mandatory.")
    elif not payment_record_file.is_file():
        logger.error("Payment record file doesn't exist. Path=%s" %
                     str(payment_record_file))
        return Boolean2.FALSE("Payment record file doesn't exist.")
    elif not ESFileManager.validateUploadFileType(payment_record_file):
        return Boolean2.FALSE('Unsupport file [%s]. Only %s allowed.' % (payment_record_file.name, ESFileManager.ALLOW_FILE_TYPES))
    # payment remarks
    payment_remarks = None if isNullBlank(payment_remarks) else str(payment_remarks).strip()

    is_success = False
    payment_record_fileID, payment_record_fileSeq = None, None
    ca_rc = None
    __CA_OPERATION_LOCK.acquire()
    ES.getFileUploadLock().acquire()
    try:
        # validate
        ca_rc = acl.add_query_filter(CashAdvancement.objects, operator_rc).filter(id=cash_advancement_id).first()
        if ca_rc is None:
            logger.error("Cash advancement doesn't exist. ID=%s" %
                         cash_advancement_id)
            return Boolean2.FALSE("Cash advancement doesn't exist.")

        # validate status
        # user maybe can settle from submitted expense directly
        validate_status_result = validate_status_transition(ca_rc.sts, Status.SETTLED)
        if not validate_status_result.value:
            return validate_status_result

        if not acl.is_settlable(operator_rc, ca_rc.sts, ca_rc.payee, ca_rc.claim_amt, ca_rc.approver):
            logger.error("You don't have permission to pay this cash advancement. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (ca_rc.id, ca_rc.sn, operator_rc.id, operator_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to pay this cash advancement.")
        is_submitted_to_settle = ca_rc.sts == Status.SUBMITTED.value
        is_first_approved_to_settle = ca_rc.sts == Status.FIRST_APPROVED.value

        payment_record_file_rc = ES.prepare_upload_file(
            ca_rc.office, ESFileManager.FileCategory.PAYMENT_RECORD, payment_record_file)
        payment_record_fileID, payment_record_fileSeq = payment_record_file_rc.id, payment_record_file_rc.seq

        pay_date = datetime.now()
        ca_rc.sts = Status.SETTLED.value
        ca_rc.pay_amt = ca_rc.claim_amt
        ca_rc.payment_tp = payment_method_rc
        ca_rc.payment_number = payment_record_no
        ca_rc.payment_record_file = payment_record_file_rc

        approve_activity = None
        if is_submitted_to_settle or is_first_approved_to_settle:
            # TODO: check approveable. E.g. 2nd approve
            approve_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=pay_date,
                                        operator=operator_rc, sts=Status.APPROVED.value, dsc='[Automatic approved.]')
            ca_rc.approve_activity = approve_activity
            ca_rc.last_activity = approve_activity

        pay_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=pay_date,
                                operator=operator_rc, sts=Status.SETTLED.value, dsc=payment_remarks)
        ca_rc.payment_activity = pay_activity
        ca_rc.last_activity = pay_activity

        trn = IkTransaction(userID=operator_rc.id)
        if isNotNullBlank(approve_activity):
            trn.add(approve_activity)
        trn.add(pay_activity)
        trn.add(payment_record_file_rc)
        trn.modify(ca_rc)
        result = trn.save(updateDate=pay_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Cash advancement [%s] has been settled." % ca_rc.sn)
    except Exception as e:
        logger.error("Settle cash advancement [%s] failed: %s" % (
            ca_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        try:
            if not is_success:
                payment_record_fileID, payment_record_fileSeq
                if isNotNullBlank(payment_record_fileSeq):  # rollback file seq
                    try:
                        newSeq = SnManager.rollbackSeq(
                            SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE, ca_rc.office, payment_record_fileSeq, exact=True)
                        if newSeq != payment_record_fileSeq - 1:
                            logger.warning("Rollback payment record file sequence failed. Current=%s, Rollback Sequence=%s" % (
                                newSeq, payment_record_fileSeq))
                    except Exception as e:
                        logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE.value, payment_record_fileSeq, str(e)), e, exc_info=True)
                if isNotNullBlank(payment_record_fileID):
                    try:
                        if not ESFileManager.rollbackFileRecord(operator_id, payment_record_fileID):
                            logger.error(
                                'Delete echeque file [%s] failed.' % payment_record_fileID)
                    except Exception as e:
                        logger.error('Delete echeque file [%s] failed: %s' % (
                            payment_record_fileID, str(e)), e, exc_info=True)
        except Exception as e:
            logger.error('Rollback the uploaded payment record file failed. %s' % str(
                e), e, exc_info=True)

        __CA_OPERATION_LOCK.release()
        ES.getFileUploadLock().release()


def revert_settled_cash_advancement(operator_id: int, cash_advancement_id: int, reason: str) -> Boolean2:
    operator_rc = UserManager.getUser(operator_id)
    if isNullBlank(operator_rc):
        logger.error("Claimer doesn't exist. ID=%s" % operator_id)
        return Boolean2.FALSE("Claimer doesn't exist.")
    if isNullBlank(cash_advancement_id):
        logger.error("Parameter [cash_advancement_id] is mandatory.")
        return Boolean2.FALSE("System error.")
    if isNullBlank(reason):
        return Boolean2.FALSE("Revert Settled Payment Reason is mandatory.")
    reason = str(reason).strip()

    is_success = False
    ca_rc = None
    payment_record_file_rc = None
    __CA_OPERATION_LOCK.acquire()
    ES.getFileUploadLock().acquire()
    try:
        # validate
        ca_rc = acl.add_query_filter(CashAdvancement.objects, operator_rc).filter(id=cash_advancement_id).first()
        if ca_rc is None:
            logger.error("Cash advancement doesn't exist. ID=%s" % cash_advancement_id)
            return Boolean2.FALSE("Cash advancement doesn't exist.")

        validate_status_result = validate_status_transition(ca_rc.sts, Status.SUBMITTED)
        if not validate_status_result.value:
            return validate_status_result

        if not acl.can_revert_settled_payment(operator_rc, ca_rc.sts, ca_rc.office):
            logger.error("You don't have permission to revert this settled cash advancement. ID=%s, SN=%S, OperatorID=%s, OperatorName=%s"
                         % (ca_rc.id, ca_rc.sn, operator_rc.id, operator_rc.usr_nm))
            return Boolean2.FALSE("You don't have permission to revert this settled cash advancement.")

        # validate expense data
        if PriorBalance.objects.filter(ca=ca_rc).count() > 0:
            return Boolean2(False, "This cash advancement is in use, please check the prior balance table.")

        # check this payment is from submitted status or approved status
        last_approve_activity_rc = Activity.objects.filter(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, sts=Status.APPROVED.value).order_by('-id').first()
        last_settled_activity_rc = Activity.objects.filter(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, sts=Status.SETTLED.value).order_by('-id').first()
        is_settled_from_submitted = (last_approve_activity_rc.cre_usr.id ==
                                     last_settled_activity_rc.cre_usr.id and last_approve_activity_rc.cre_dt == last_settled_activity_rc.cre_dt)

        revert_date = datetime.now()
        ca_rc.sts = Status.SUBMITTED.value if is_settled_from_submitted else Status.APPROVED.value
        payment_record_file_rc = ca_rc.payment_record_file
        ca_rc.payment_record_file = None
        ca_rc.pay_amt = None
        ca_rc.payment_activity = None
        ca_rc.payment_tp = None
        ca_rc.payment_number = None

        revert_settled_payment_activity = Activity(tp=ActivityType.CASH_ADVANCEMENT.value, transaction_id=ca_rc.id, operate_dt=revert_date,
                                                   operator=operator_rc, sts=ca_rc.sts, dsc="[Revert settled payment.] Reason: " + reason)
        ca_rc.last_activity = revert_settled_payment_activity

        trn = IkTransaction(userID=operator_id)
        trn.add(revert_settled_payment_activity)
        trn.modify(ca_rc)
        result = trn.save(updateDate=revert_date)
        if not result.value:
            return result
        is_success = True
        return Boolean2.TRUE("Revert settled cash advancement [%s] to %s." % (ca_rc.sn, ca_rc.sts))
    except Exception as e:
        logger.error("Revert settled cash advancement [%s] failed: %s" % (
            ca_rc.sn, e), e, exc_info=True)
        return Boolean2(False, "System error, please ask administrator to check!")
    finally:
        try:
            if is_success:
                ESNotification.send_submit_cancel_reject_cash_advancement_notify(operator_id, ca_rc)
                # try to rollback the sequence if the current sequence is the last one
                payment_record_fileID = payment_record_file_rc.id
                payment_record_fileSeq = payment_record_file_rc.seq
                if isNotNullBlank(payment_record_fileSeq):  # rollback file seq
                    try:
                        SnManager.rollbackSeq(
                            SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE, ca_rc.office, payment_record_fileSeq)
                    except Exception as e:
                        logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                     (SnManager.SequenceType.SEQ_TYPE_PAYMENT_RECORD_FILE.value, payment_record_fileSeq, str(e)), e, exc_info=True)
                if isNotNullBlank(payment_record_fileID):
                    try:
                        if not ESFileManager.rollbackFileRecord(operator_id, payment_record_fileID):
                            logger.error(
                                'Delete echeque file [%s] failed.' % payment_record_fileID)
                    except Exception as e:
                        logger.error('Delete echeque file [%s] failed: %s' % (
                            payment_record_fileID, str(e)), e, exc_info=True)
        except Exception as e:
            logger.error('Rollback the uploaded payment record file failed. %s' % str(
                e), e, exc_info=True)

        __CA_OPERATION_LOCK.release()
        ES.getFileUploadLock().release()


def getAvailablePriorBalanceRcs(payeeRc: Payee, currency: Currency = None) -> list[AvailablePriorBalance]:
    """Get available prior balance records if the payee selected and it's settled by prior balance.

    """
    ca_rcs = CashAdvancement.objects.filter(office=payeeRc.office, payee=payeeRc, sts=Status.SETTLED.value).order_by('sn')
    availableRcs = []
    for ca_rc in ca_rcs:
        _normalExpense, _pettyExpenses, _fxExpenses, usages, fxUsages = getCashAdvancementUsage(ca_rc)
        for fxRc, total, used, left in fxUsages:
            if left > 0 and (currency is None or currency.id == fxRc.fx_ccy.id):
                availableRcs.append(AvailablePriorBalance(
                    ca=ca_rc, ccy=fxRc.fx_ccy, total_amt=total, balance_amt=left, fx=fxRc))
        for ccyRc, isFx, total, used, left in usages:
            if not isFx and left > 0 and (currency is None or currency.id == ccyRc.id):
                availableRcs.append(AvailablePriorBalance(
                    ca=ca_rc, ccy=ccyRc, total_amt=total, balance_amt=left, fx=None))
    return availableRcs


def getAvailablePriorBalanceCCYRcs(payeeRc: Payee, updateCurrencyCodeForFX: bool = False) -> list[Currency]:
    """
        updateCurrencyCodeForFX: add " (FX)" to currency's code. E.g. USD (FX)

        Return [default payee's currency if exists, fx ccy1, fx ccy2]
    """
    ccyRcs = []
    ccyIDs = []
    rcs = getAvailablePriorBalanceRcs(payeeRc)
    for rc in rcs:
        if rc.ccy.id not in ccyIDs:
            ccyIDs.append(rc.ccy.id)
            if updateCurrencyCodeForFX and isNotNullBlank(rc.fx):
                rc.ccy.code = '%s (FX)' % rc.ccy.code
            ccyRcs.append(rc.ccy)
    return ccyRcs


def getCashAdvancementUsage(cashAdvRc: CashAdvancement):
    normalExpense = []
    pettyExpenses = []
    fxExpenses = []
    usages = []
    fxUsages = []  # [[fx, total, used, left]]

    if cashAdvRc.sts != Status.DRAFT.value and cashAdvRc.sts != Status.SUBMITTED.value:
        # fx records
        usedAmount = 0
        fxCCYRcs = {}
        fxAmounts = {}
        for fxRc in ForeignExchange.objects.filter(ca=cashAdvRc, sts=Status.APPROVED.value).order_by('id'):
            usedAmount = ESTools.add(usedAmount, fxRc.amt)
            fxAmount = fxAmounts.get(fxRc.fx_ccy.id, 0)
            fxAmount = ESTools.add(fxAmount, fxRc.fx_amt)
            fxAmounts[fxRc.fx_ccy.id] = fxAmount
            fxCCYRcs[fxRc.fx_ccy.id] = fxRc.fx_ccy
            fxUsages.append([fxRc, fxRc.fx_amt, 0, fxRc.fx_amt])
        localTotalAmount = ESTools.sub(cashAdvRc.claim_amt, usedAmount)

        # prior balance
        fxUsedAmounts = {}
        usedLocalAmount = 0
        for pbRc in PriorBalance.objects.filter(ca=cashAdvRc, expense__sts__in=__CASH_ADVANCEMENT_ACCEPT_EXPENSE_STATUS):
            if isNotNullBlank(pbRc.fx):
                fxUsedAmount = fxUsedAmounts.get(pbRc.fx.fx_ccy.id, 0)
                fxUsedAmount = ESTools.add(fxUsedAmount, pbRc.fx_balance_amt)
                fxUsedAmounts[pbRc.fx.fx_ccy.id] = fxUsedAmount
                fxExpenses.append(pbRc)
                if pbRc.fx.fx_ccy.id not in fxAmounts.keys():
                    logger.error("Cash advancement [%s] doesn't have FX CCY [%s], but prior balance used [%s]! Please check." % (
                        cashAdvRc.sn, pbRc.fx.fx_ccy.code, pbRc.fx_balance_amt))
                for fxData in fxUsages:
                    if fxData[0].id == pbRc.fx.id:
                        fxUsed = float(round_currency(ESTools.add(fxData[2], pbRc.fx_balance_amt)))
                        fxLeft = float(round_currency(ESTools.sub(fxData[1], fxUsed)))
                        fxData[2] = fxUsed
                        fxData[3] = fxLeft
                        break
            else:
                usedLocalAmount = ESTools.add(usedLocalAmount, pbRc.balance_amt)
                if pbRc.expense.is_petty_expense is True:
                    pettyExpenses.append(pbRc)
                else:
                    normalExpense.append(pbRc)
        # calculate left amount
        # the first item is the default currency usage
        usages.append((cashAdvRc.ccy, False, float(round_currency(localTotalAmount)),
                       float(round_currency(usedLocalAmount)),
                       float(round_currency(ESTools.sub(localTotalAmount, usedLocalAmount)))))
        for fxID, fxAmount in fxAmounts.items():
            fxUsedAmount = fxUsedAmounts.get(fxID, 0)
            fxLeft = float(round_currency(
                ESTools.sub(fxAmount, fxUsedAmount)))
            usages.append((fxCCYRcs[fxID], True, float(round_currency(
                fxAmount)), float(round_currency((fxUsedAmount))), fxLeft))

    if cashAdvRc.sts == Status.CANCELLED.value or cashAdvRc.sts == Status.REJECTED.value:
        # normally, the cancelled/rejected expense doesn't have prior records
        if len(normalExpense) == 0 and len(pettyExpenses) == 0 and len(fxExpenses) == 0 and len(usages) == 1:
            # the item 0 always is the default currency usage
            usages.clear()  # remove default currency usage

    normalExpense.sort(key=lambda x: x.expense.sn)
    pettyExpenses.sort(key=lambda x: x.expense.sn)
    fxExpenses.sort(key=lambda x: x.expense.sn)
    return normalExpense, pettyExpenses, fxExpenses, usages, fxUsages


def getPriorBalanceInfo(expenseHdrRc: Expense):
    # TODO: speed up
    pbRcs = PriorBalance.objects.filter(expense=expenseHdrRc).order_by('id')
    tableData = []
    for pbRc in pbRcs:
        claimCCY = None
        rate = None
        amount = None
        claimAmount = None
        previousExpenditureAmount = 0
        if isNotNullBlank(pbRc.fx):
            claimCCY = "%s (FX)" % pbRc.fx.fx_ccy.code
            rate = float(round_rate(pbRc.fx.fx_rate))
            amount = float(round_currency(pbRc.fx.fx_amt))
            claimAmount = float(round_currency(pbRc.fx_balance_amt))
            previousExpenditureAmount = PriorBalance.objects.filter(ca=pbRc.ca, fx__isnull=False, fx__sts=Status.APPROVED.value, id__lt=pbRc.id,
                                                                    expense__sts__in=__CASH_ADVANCEMENT_ACCEPT_EXPENSE_STATUS).aggregate(total=Sum('fx_balance_amt'))['total']
        else:
            claimCCY = pbRc.ca.office.ccy.code
            totalFxUsedAmount = ForeignExchange.objects.filter(ca=pbRc.ca, sts=Status.APPROVED.value).aggregate(total=Sum('amt'))['total']
            if isNullBlank(totalFxUsedAmount):
                totalFxUsedAmount = 0
            amount = float(round_currency(ESTools.sub(pbRc.ca.claim_amt, totalFxUsedAmount)))
            claimAmount = float(round_currency(pbRc.claim_amt))
            previousExpenditureAmount = PriorBalance.objects.filter(
                ca=pbRc.ca, fx__isnull=True, id__lt=pbRc.id, expense__sts__in=__CASH_ADVANCEMENT_ACCEPT_EXPENSE_STATUS).aggregate(total=Sum('balance_amt'))['total']

        leftAmount = float(round_currency(ESTools.sub(ESTools.sub(amount, previousExpenditureAmount if isNotNullBlank(previousExpenditureAmount) else 0), claimAmount)))

        rowData = {}
        rowData['payee'] = pbRc.ca.payee.payee
        rowData['ca_sn'] = pbRc.ca.sn
        rowData['claim_ccy'] = claimCCY
        rowData['rate'] = rate
        rowData['amt'] = amount
        rowData['previous_expenditure_amt'] = previousExpenditureAmount
        rowData['this_claim_amt'] = claimAmount
        rowData['left_amt'] = leftAmount
        tableData.append(rowData)
    return tableData


def query_cash_advancements(retriever: User, office_rc: Office, ca_queryset: QuerySet, query_parameters: dict) -> QuerySet:
    if isNullBlank(retriever):
        raise IkValidateException("Parameter [receiver] is mandatory.")
    if isNullBlank(office_rc):
        raise IkValidateException("Parameter [office_rc] is mandatory.")
    if isNullBlank(ca_queryset):
        raise IkValidateException("Parameter [ca_queryset] is mandatory.")
    elif not issubclass(ca_queryset.model, CashAdvancement):
        raise IkValidateException("Parameter [ca_queryset] should be a CashAdvancement instance.")
    if isNullBlank(query_parameters):
        query_parameters = {}

    # Add base query ACL (Access Control List)
    ca_queryset = acl.add_query_filter(ca_queryset, retriever)

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
    query_payment_record_filename = get_prm('payment_record_filename')
    query_claim_date_from = get_prm('claim_date_from')
    query_claim_date_to = get_prm('claim_date_to')
    query_approved_date_from = get_prm('approve_date_from')
    query_approved_date_to = get_prm('approve_date_to')
    query_settle_date_from = get_prm('settle_date_from')
    query_settle_date_to = get_prm('settle_date_to')
    query_desc = get_prm('description')

    if isNotNullBlank(query_id):
        ca_queryset = ca_queryset.filter(id=query_id)
    else:
        if isNotNullBlank(query_sn):
            ca_queryset = ca_queryset.filter(sn__icontains=query_sn)
        if isNotNullBlank(query_po):
            ca_queryset = ca_queryset.filter(po__sn__icontains=query_po)
        if isNotNullBlank(query_status):
            ca_queryset = ca_queryset.filter(sts=query_status)
        if isNotNullBlank(query_claimer):
            ca_queryset = ca_queryset.filter(claimer__usr_nm__icontains=query_claimer)
        if isNotNullBlank(query_payee):
            ca_queryset = ca_queryset.filter(payee__payee__icontains=query_payee)
        if isNotNullBlank(query_payment_record_filename):
            ca_queryset = ca_queryset.filter(payment_record_file__file_original_nm__icontains=query_payment_record_filename)
        if isNotNullBlank(query_claim_date_from):
            query_claim_date_from = datetime.strptime(query_claim_date_from, "%Y-%m-%d")
            ca_queryset = ca_queryset.filter(claim_dt__gte=make_aware(datetime(query_claim_date_from.year, query_claim_date_from.month, query_claim_date_from.day, 0, 0, 0)))
        if isNotNullBlank(query_claim_date_to):
            query_claim_date_to = datetime.strptime(query_claim_date_to, "%Y-%m-%d")
            nextDay = query_claim_date_to + timedelta(days=1)
            ca_queryset = ca_queryset.filter(claim_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0)))
        if isNotNullBlank(query_approved_date_from):
            query_approved_date_from = datetime.strptime(query_approved_date_from, "%Y-%m-%d")
            ca_queryset = ca_queryset.filter(Q(approve2_activity__isnull=False, approve2_activity__sts=Status.APPROVED.value, approve2_activity__operate_dt__gte=make_aware(datetime(query_approved_date_from.year, query_approved_date_from.month, query_approved_date_from.day, 0, 0, 0)))
                                             | Q(approve2_activity__isnull=True, approve_activity__isnull=False, approve_activity__sts=Status.APPROVED.value, approve_activity__operate_dt__gte=make_aware(datetime(query_approved_date_from.year, query_approved_date_from.month, query_approved_date_from.day, 0, 0, 0))))
        if isNotNullBlank(query_approved_date_to):
            query_approved_date_to = datetime.strptime(query_approved_date_to, "%Y-%m-%d")
            nextDay = query_approved_date_to + timedelta(days=1)
            ca_queryset = ca_queryset.filter(Q(approve2_activity__isnull=False, approve2_activity__sts=Status.APPROVED.value, approve2_activity__operate_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0)))
                                             | Q(approve2_activity__isnull=True, approve_activity__isnull=False, approve_activity__sts=Status.APPROVED.value, approve_activity__operate_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0))))
        if isNotNullBlank(query_settle_date_from):
            query_settle_date_from = datetime.strptime(query_settle_date_from, "%Y-%m-%d")
            ca_queryset = ca_queryset.filter(payment_activity__operate_dt__gte=make_aware(
                datetime(query_settle_date_from.year, query_settle_date_from.month, query_settle_date_from.day, 0, 0, 0)))
        if isNotNullBlank(query_settle_date_to):
            query_settle_date_to = datetime.strptime(query_settle_date_to, "%Y-%m-%d")
            nextDay = query_settle_date_to + timedelta(days=1)
            ca_queryset = ca_queryset.filter(payment_activity__operate_dt__lt=make_aware(datetime(nextDay.year, nextDay.month, nextDay.day, 0, 0, 0)))
        if isNotNullBlank(query_desc):
            ca_queryset = ca_queryset.filter(dsc__icontains=query_desc)
    return ca_queryset
