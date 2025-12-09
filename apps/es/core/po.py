'''
Description: PO Manager
version:
Author: YL
Date: 2025-04-15 09:46:53
'''
import logging
from datetime import datetime
from threading import Lock

from django.db.models import Q

import core.core.fs as ikfs
from core.core.exception import *
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.utils.lang_utils import isNotNullBlank, isNullBlank

from ..models import *
from . import acl, approver, es, es_file, es_seq
from .es_notification import send_po_notify

logger = logging.getLogger('ikyo')

__FILE_UPLOAD_LOCK = Lock()
__LOCK = Lock()


def is_saveable(operator_rc: User, po_rc: Po, is_admin: bool) -> bool:
    """ Check the operator can save po or not

        if status == "submitted", can save but can't update status
    Args:
        operator_rc (User): operator
        po_rc (Po): po
        is_admin (bool): is admin or not

    Returns:
        bool: Can save or not
    """
    if isNullBlank(po_rc.status) or po_rc.status == Po.SAVED_STATUS or (po_rc.status == Po.SUBMITTED_STATUS and (is_admin or po_rc.assigned_approver == operator_rc)):
        return True
    return False


def is_submittable(operator_rc: User, po_rc: Po) -> bool:
    """ Check the operator can submit po or not

        only allow None / saved / rejected status po to submit.
    Args:
        operator_rc (User): operator
        po_rc (Po): po

    Returns:
        bool: Can submit or not
    """
    if po_rc.ik_is_status_new():
        return True
    if po_rc.status == Po.SAVED_STATUS or po_rc.status == po_rc.REJECTED_STATUS:
        if isNullBlank(po_rc.submitter) or po_rc.submitter == operator_rc:
            return True
    return False


def is_approvable(operator_rc: User, po_rc: Po, is_admin: bool) -> bool:
    """ Check the operator can approve po or not

        only allow admin / approver / approver assistant to approve
    Args:
        operator_rc (User): operator
        po_rc (Po): po

    Returns:
        bool: Can approve or not
    """
    if po_rc.status == Po.SUBMITTED_STATUS:
        if is_admin or po_rc.assigned_approver == operator_rc:
            return True
        for assistant_approver_rc in approver.get_approver_assistants(po_rc.office, po_rc.assigned_approver):
            if assistant_approver_rc == operator_rc:
                return True
    return False


def is_rejectable(operator_rc: User, po_rc: Po, is_admin: bool) -> bool:
    """ Check the operator can reject po or not

        only allow admin / approver / approver assistant to reject
    Args:
        operator_rc (User): operator
        po_rc (Po): po

    Returns:
        bool: Can reject or not
    """
    if po_rc.status == Po.SUBMITTED_STATUS or po_rc.status == Po.APPROVED_STATUS:
        if is_admin or po_rc.assigned_approver == operator_rc:
            return True
        for assistant_approver_rc in approver.get_approver_assistants(po_rc.office, po_rc.assigned_approver):
            if assistant_approver_rc == operator_rc:
                return True
    return False


def validate_po_permission(user_rc: User, po_sn: str) -> Boolean2:
    """
        Check if the user has permission to use PO

        Args:
        user_rc (User): User
        po_sn (str): po

    Returns:
        bool: Can use or not
    """
    po_rc = Po.objects.filter(sn=po_sn).first()
    if isNullBlank(po_rc):
        return Boolean2(False, "PO [%s] doesn't exist." % po_sn)
    queryset = Po.objects.filter(deleter__isnull=True, status=Po.APPROVED_STATUS)
    if not acl.is_es_admin(user_rc):
        queryset = queryset.filter(Q(cre_usr_id=user_rc.id) | Q(submitter_id=user_rc.id) | Q(assigned_approver_id=user_rc.id))
    queryset = queryset.filter(sn=po_sn).first()
    if isNullBlank(queryset):
        return Boolean2(False, "Permission deny: PO [%s]. Please check." % po_sn)
    return Boolean2(True, po_rc.id)


def is_deletable(operator_rc: User, po_rc: Po) -> bool:
    """ Check the operator can delete po or not

    Args:
        operator_rc (User): operator
        po_rc (Po): po

    Returns:
        bool: Can delete or not
    """
    if po_rc.status == Po.REJECTED_STATUS:
        if po_rc.submitter == operator_rc or po_rc.assigned_approver == operator_rc:
            return True
    return False


def save_or_submit_po_detail(user_rc: User, is_admin: bool, office_rc: Office, po_dtl1: Po, po_quo_rcs: list[PoQuotation], po_dtl2: Po, status: str) -> Boolean2:
    """ Save / Submit PO

    Args:
        user_rc (User): user
        is_admin (bool): is admin
        office_rc (Office): office
        po_dtl1 (Po): po detail
        po_quo_rcs (list[PoQuotation]): po quotation list
        po_dtl2 (Po): po detail
        status (str): status

    Raises:
        IkValidateException: Office is required.

    Returns:
        Boolean2: Save / Submit result
    """
    if isNullBlank(office_rc):
        logger.error("office_rc is empty for 'save_or_submit_po_detail' method, please check.")
        raise IkValidateException("Office don't exist.")

    is_success = False
    delete_file = []
    try:
        __LOCK.acquire()
        now = datetime.now()
        # 1. save po
        po_rc = po_dtl1
        if po_dtl1.ik_is_status_new():
            po_rc = Po()
            po_rc.sn = _get_next_sn()
        elif po_dtl1.ik_is_status_modified() or po_dtl2.ik_is_status_modified():
            po_rc = Po.objects.filter(id=po_dtl1.id).first()
            po_rc.ik_set_status_modified()

        # validate
        if status == Po.SAVED_STATUS:
            if not is_saveable(user_rc, po_rc, is_admin):
                logger.error("You don't have permission to save this po ID=%s, SN=%s, OperatorID=%s, OperatorName=%s"
                             % (po_rc.id, po_rc.sn, user_rc.id, user_rc.usr_nm))
                return Boolean2(False, "You don't have permission to save this po.")
        elif status == Po.SUBMITTED_STATUS:
            if not is_submittable(user_rc, po_rc):
                logger.error("You don't have permission to submit this po ID=%s, SN=%s, OperatorID=%s, OperatorName=%s"
                             % (po_rc.id, po_rc.sn, user_rc.id, user_rc.usr_nm))
                return Boolean2(False, "You don't have permission to submit this po.")
        else:
            return Boolean2(False, "Unknown status.")

        if po_rc.ik_is_status_new() or po_rc.ik_is_status_modified():
            po_rc.office = office_rc
            po_rc.purchase_item = po_dtl1.purchase_item
            po_rc.recommendation = po_dtl2.recommendation
            po_rc.assigned_approver_id = po_dtl2.assigned_approver_id
            if isNullBlank(po_rc.status) or po_rc.status != Po.SUBMITTED_STATUS:
                po_rc.status = status
            if status == Po.SUBMITTED_STATUS:
                po_rc.submit_dt = now
                po_rc.submitter = user_rc

        # only submit
        if po_rc.ik_is_status_retrieve() and po_rc.status != status and po_rc.status != Po.SUBMITTED_STATUS:
            po_rc.ik_set_status_modified()
            po_rc.status = status
            if status == Po.SUBMITTED_STATUS:
                po_rc.submit_dt = now
                po_rc.submitter = user_rc

        # 2. save po quotations
        for quo_rc in po_quo_rcs:
            if quo_rc.ik_is_status_delete() and isNotNullBlank(quo_rc.file):
                delete_file.append((quo_rc.file.id, quo_rc.file.seq))
            if quo_rc.ik_is_status_new():
                quo_rc.po = po_rc

        ptrn = IkTransaction(userID=user_rc.id)
        ptrn.add(po_rc)
        ptrn.add(po_quo_rcs)
        b = ptrn.save()
        if b.value:
            is_success = True
            return Boolean2(True, po_rc.id)
        else:
            return Boolean2(False, "%s failed." % "Save" if status == Po.SAVED_STATUS else "Submit")
    except IkException as e:
        logger.error('%s %s po detail failed: %s' % (user_rc.usr_nm, "save" if status == Po.SAVED_STATUS else "submit", str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(False, "%s failed: %s" % ("Save" if status == Po.SAVED_STATUS else "Submit", str(e)))
    except Exception as e:
        logger.error('%s failed: %s' % ("Save" if status == Po.SAVED_STATUS else "Submit", str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')
    finally:
        if is_success:
            try:
                if isNotNullBlank(delete_file) and len(delete_file) > 0:  # delete po quotation file
                    for file_id, file_seq in delete_file:
                        try:
                            es_seq.rollbackSeq(es_seq.SequenceType.SEQ_TYPE_PO_FILE, office_rc, file_seq)
                        except Exception as e:
                            logger.error('Rollback file [%s] sequence [%s] failed: %s' %
                                         (es_seq.SequenceType.SEQ_TYPE_PO_FILE.value, file_seq, str(e)), e, exc_info=True)

                        try:
                            if not es_file.rollbackFileRecord(user_rc.id, file_id):
                                logger.error('Delete po quotation file [%s] failed.' % file_id)
                        except Exception as e:
                            logger.error('Delete po quotation file [%s] failed: %s' % (file_id, str(e)), e, exc_info=True)
                        try:
                            # delete the file
                            es_file.deleteESFileAndFolder(es_file.getFile(file_id))
                        except Exception as e:
                            logger.error('Delete po quotation file [%s] failed: %s' % (file_id, str(e)), e, exc_info=True)
            except:
                logger.error('Delete po quotation file failed: %s' % str(e))
                logger.error(e, exc_info=True)

            # send notification
            if status == Po.SUBMITTED_STATUS:
                send_po_notify(user_rc.id, po_rc)
        __LOCK.release()


def approve_or_reject(user_rc: User, is_admin: bool, po_id: int, rmk: str, status: str) -> Boolean2:
    """ Approve / Reject PO

    Args:
        user_rc (User): user
        is_admin (bool): is admin
        po_id (int): po id
        rmk (str): approve / reject remark
        status (str): status

    Returns:
        Boolean2: Approve / Reject result
    """
    if isNullBlank(po_id):
        return Boolean2(False, "PO ID is null, please ask administrator to check.")
    if status == Po.REJECTED_STATUS and isNullBlank(rmk):
        return Boolean2(False, "Remark is required.")

    # validate
    po_rc = Po.objects.filter(id=po_id).first()
    if status == Po.APPROVED_STATUS:
        if not is_approvable(user_rc, po_rc, is_admin):
            logger.error("You don't have permission to approve this po ID=%s, SN=%s, OperatorID=%s, OperatorName=%s"
                         % (po_rc.id, po_rc.sn, user_rc.id, user_rc.usr_nm))
            return Boolean2(False, "You don't have permission to approve this po.")
    elif status == Po.REJECTED_STATUS:
        if not is_rejectable(user_rc, po_rc, is_admin):
            logger.error("You don't have permission to reject this po ID=%s, SN=%s, OperatorID=%s, OperatorName=%s"
                         % (po_rc.id, po_rc.sn, user_rc.id, user_rc.usr_nm))
            return Boolean2(False, "You don't have permission to reject this po.")
    else:
        return Boolean2(False, "Unknown status.")

    is_success = False
    try:
        __LOCK.acquire()
        now = datetime.now()
        if status == Po.APPROVED_STATUS:  # approve
            po_rc.approver = user_rc
            po_rc.approve_dt = now
        elif status == Po.REJECTED_STATUS:  # reject
            po_rc.rejecter = user_rc
            po_rc.reject_dt = now
        po_rc.rmk = rmk
        po_rc.status = status
        po_rc.ik_set_status_modified()

        ptrn = IkTransaction(userID=user_rc.id)
        ptrn.add(po_rc)
        b = ptrn.save()
        if b.value:
            is_success = True
            return Boolean2(True, po_id)
        else:
            return Boolean2(False, "%s failed." % "Approve" if status == Po.APPROVED_STATUS else "Reject")
    except IkException as e:
        logger.error('%s %s po failed: %s' % (user_rc.usr_nm, "approve" if status == Po.APPROVED_STATUS else "reject", str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(False, "%s failed: %s" % ("Approve" if status == Po.APPROVED_STATUS else "Reject", str(e)))
    except Exception as e:
        logger.error('%s failed: %s' % ("Approve" if status == Po.APPROVED_STATUS else "Reject", str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')
    finally:
        # send notification
        if is_success:
            send_po_notify(user_rc.id, po_rc)
        __LOCK.release()


def delete(user_rc: User, po_id: int, status: str) -> Boolean2:
    """ Delete PO

    Args:
        user_rc (User): user
        po_id (int): po id
        status (str): status

    Returns:
        Boolean2: Delete result
    """
    if isNullBlank(po_id):
        return Boolean2(False, "PO ID is null, please ask administrator to check.")
    if status != Po.DELETED_STATUS:
        return Boolean2(False, "Delete failed: Unknown status.")
    try:
        __LOCK.acquire()
        po_rc = Po.objects.filter(id=po_id).first()
        now = datetime.now()
        po_rc.deleter = user_rc
        po_rc.delete_dt = now
        po_rc.status = status
        po_rc.ik_set_status_modified()

        ptrn = IkTransaction(userID=user_rc.id)
        ptrn.add(po_rc)
        b = ptrn.save()
        if b.value:
            is_success = True
            return Boolean2(True, "Deleted.")
        else:
            return Boolean2(False, "Delete failed.")
    except IkException as e:
        logger.error('%s delete po failed: %s' % (user_rc.usr_nm, str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(False, "Delete failed: %s" % str(e))
    except Exception as e:
        logger.error('Delete po failed: %s' % str(e))
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')
    finally:
        __LOCK.release()


def upload_quotation_file(user_rc: User, class_nm: str, quo_id: int, upload_files) -> Boolean2:
    """ Upload Po Quotation file

    Args:
        user_rc (User): user
        class_nm (str): class name
        quo_id (int): quotation id
        upload_files (_type_): upload file

    Raises:
        IkValidateException: validate file exists or not

    Returns:
        Boolean2: upload result
    """
    if isNullBlank(upload_files) or len(upload_files) == 0 or isNullBlank(upload_files[0]):
        return Boolean2(False, "Please select a file to upload.")
    upload_file = upload_files[0]
    file_type = ikfs.getFileExtension(upload_file.name)
    if file_type.lower() not in ['pdf', 'jpg', 'jpeg', 'png']:
        return Boolean2(False, "Only PDF/PNG/JPG/JPEG attachment accept. - %s" % upload_file.name)
    quo_rc = PoQuotation.objects.filter(id=quo_id).first()
    if isNullBlank(quo_rc):
        return Boolean2(False, "Po quotation ID=[%s] does not exists, please ask administrator to check." % str(quo_id))

    is_success = False
    new_file_rc = None
    uploaded_file_path = es_file.save_uploaded_really_file(upload_file, class_nm, user_rc.usr_nm)
    uploaded_file_hash = es_file.calculateFileHash(uploaded_file_path)
    __FILE_UPLOAD_LOCK.acquire()
    try:
        # check file is exists or not
        exist_file_rc = PoQuotation.objects.filter(id=quo_id, file__sha256=uploaded_file_hash).first()
        if isNotNullBlank(exist_file_rc):
            raise IkValidateException("This file exists. Please check. File name is [%s]. SN is %s." %
                                      (exist_file_rc.file.file_original_nm, exist_file_rc.file.seq))

        new_file_rc = es.prepare_upload_file(quo_rc.po.office, es_file.FileCategory.PO, uploaded_file_path)
        if isNotNullBlank(new_file_rc):
            quo_rc.file = new_file_rc
            quo_rc.ik_set_status_modified()

        ptrn = IkTransaction(userID=user_rc.id)
        ptrn.add(new_file_rc)
        ptrn.modify(quo_rc)
        b = ptrn.save()
        if not b.value:
            return Boolean2(False, "Upload po quotation file failed: %s" % b.dataStr)
        is_success = True
        return Boolean2(True, new_file_rc.id)
    except IkException as e:
        logger.error('%s upload po quotation file failed: %s' % (user_rc.usr_nm, str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(True, str(e))
    except Exception as e:
        logger.error('Upload po quotation file failed: %s' % str(e))
        logger.error(e, exc_info=True)
        return Boolean2(True, 'System error, please ask administrator to check.')
    finally:
        try:
            if not is_success:  # failed
                if isNotNullBlank(uploaded_file_path) and uploaded_file_path.is_file():
                    es_file.delete_really_file(uploaded_file_path)
                if isNotNullBlank(new_file_rc):
                    if isNotNullBlank(new_file_rc.seq):  # rollback file seq
                        try:
                            es_seq.rollbackSeq(es_seq.SequenceType.SEQ_TYPE_PO_FILE, new_file_rc.office.id, new_file_rc.seq)
                        except Exception as e:
                            logger.error('Rollback po quotation file [%s] sequence [%s] failed: %s' %
                                         (es_seq.SequenceType.SEQ_TYPE_PO_FILE.value, new_file_rc.seq, str(e)))
                            logger.error(e, exc_info=True)
                    if isNotNullBlank(new_file_rc.id):
                        try:
                            if not es_file.rollbackFileRecord(user_rc.id, new_file_rc.id):
                                logger.error('Delete po quotation file [%s] failed.' % new_file_rc.id)
                        except Exception as e:
                            logger.error('Delete po quotation file [%s] failed: %s' % (new_file_rc.id, str(e)))
                            logger.error(e, exc_info=True)
        except Exception as e:
            logger.error('Upload po quotation file failed when do the finally: %s' % str(e), e, exc_info=True)
        __FILE_UPLOAD_LOCK.release()


def upload_po_file(user_rc: User, class_nm: str, po_id: int, rmk: str, upload_file) -> Boolean2:
    """ Upload Sign Po file

    Args:
        user_rc (User): user
        class_nm (str): class name
        po_id (int): po id
        upload_files (_type_): upload file

    Raises:
        IkValidateException: validate file exists or not

    Returns:
        Boolean2: upload result
    """
    file_type = ikfs.getFileExtension(upload_file.name)
    if file_type.lower() not in ['pdf', 'jpg', 'jpeg', 'png']:
        return Boolean2(False, "Only PDF/PNG/JPG/JPEG attachment accept. - %s" % upload_file.name)
    po_rc = Po.objects.filter(id=po_id).first()
    if isNullBlank(po_rc):
        return Boolean2(False, "Po ID=[%s] does not exists, please ask administrator to check." % str(po_id))

    is_success = False
    new_file_rc = None
    old_file_info = (po_rc.file.id, po_rc.file.file_nm) if isNotNullBlank(po_rc.file) else None
    uploaded_file_path = es_file.save_uploaded_really_file(upload_file, class_nm, user_rc.usr_nm)
    uploaded_file_hash = es_file.calculateFileHash(uploaded_file_path)
    __FILE_UPLOAD_LOCK.acquire()
    try:
        # check file is exists or not
        exist_file_rc = Po.objects.filter(id=po_id, file__sha256=uploaded_file_hash).first()
        if isNotNullBlank(exist_file_rc):
            raise IkValidateException("This file exists. Please check. File name is [%s]. SN is %s." %
                                      (exist_file_rc.file.file_original_nm, exist_file_rc.file.seq))

        new_file_rc = es.prepare_upload_file(po_rc.office, es_file.FileCategory.PO, uploaded_file_path)
        if isNotNullBlank(new_file_rc):
            po_rc.file = new_file_rc
            po_rc.file_rmk = rmk
            po_rc.ik_set_status_modified()

        # delete old file
        file_rc = None
        if isNotNullBlank(old_file_info):
            file_rc = File.objects.filter(id=old_file_info[0])

        ptrn = IkTransaction(userID=user_rc.id)
        ptrn.add(new_file_rc)
        ptrn.modify(po_rc)
        if isNotNullBlank(file_rc):
            ptrn.delete(file_rc)
        b = ptrn.save()
        if not b.value:
            return Boolean2(False, "Upload po file failed: %s" % b.dataStr)
        is_success = True
        return Boolean2(True, new_file_rc.id)
    except IkException as e:
        logger.error('%s upload po file failed: %s' % (user_rc.usr_nm, str(e)))
        logger.error(e, exc_info=True)
        return Boolean2(True, str(e))
    except Exception as e:
        logger.error('Upload po file failed: %s' % str(e))
        logger.error(e, exc_info=True)
        return Boolean2(True, 'System error, please ask administrator to check.')
    finally:
        try:
            if is_success:
                if isNotNullBlank(old_file_info):
                    # delete the old file
                    original_file = es_file.getIdFile(old_file_info[0], old_file_info[1])
                    es_file.delete_really_file(original_file)
            else:  # failed
                if isNotNullBlank(uploaded_file_path) and uploaded_file_path.is_file():
                    es_file.delete_really_file(uploaded_file_path)
                if isNotNullBlank(new_file_rc):
                    if isNotNullBlank(new_file_rc.seq):  # rollback file seq
                        try:
                            es_seq.rollbackSeq(es_seq.SequenceType.SEQ_TYPE_PO_FILE, new_file_rc.office.id, new_file_rc.seq)
                        except Exception as e:
                            logger.error('Rollback po file [%s] sequence [%s] failed: %s' %
                                         (es_seq.SequenceType.SEQ_TYPE_PO_FILE.value, new_file_rc.seq, str(e)))
                            logger.error(e, exc_info=True)
                    if isNotNullBlank(new_file_rc.id):
                        try:
                            if not es_file.rollbackFileRecord(user_rc.id, new_file_rc.id):
                                logger.error('Delete po file [%s] failed.' % new_file_rc.id)
                        except Exception as e:
                            logger.error('Delete po file [%s] failed: %s' % (new_file_rc.id, str(e)))
                            logger.error(e, exc_info=True)
        except Exception as e:
            logger.error('Upload po file failed when do the finally: %s' % str(e), e, exc_info=True)
        __FILE_UPLOAD_LOCK.release()


def _get_next_sn() -> str:
    sn_prefix = 'P'
    sn_format = "{:04d}"
    seq = 1
    year = datetime.now().year
    last_rc = Po.objects.filter(sn__contains=sn_prefix + str(year)).order_by('-id').first()
    if isNotNullBlank(last_rc):
        last_sn = last_rc.sn
        prefix_len = len(sn_prefix) + len(str(year))
        last_seq = last_sn[prefix_len:]
        seq = int(last_seq) + 1
    return sn_prefix + str(year) + sn_format.format(seq)
