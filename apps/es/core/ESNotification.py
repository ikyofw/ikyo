"""ES Notification.
"""
import logging
import traceback
from enum import Enum, unique

import core.user.userManager as UserManager
from core.core.lang import Boolean2
from core.core.mailer import MailManager
from core.inbox import InboxManager
from core.menu.menuManager import MenuManager
from core.models import User
from core.sys.systemSetting import SystemSetting
from core.utils.langUtils import isNotNullBlank, isNullBlank

from ..models import *
from . import approver, const
from .accounting import get_accounting_user_ids
from .activity import ActivityType
from .expense_type import ExpenseType
from .petty_expense import get_petty_admin
from .setting import (is_enable_default_inbox_message,
                      is_enable_email_notification)
from .status import Status

logger = logging.getLogger('ikyo')


__NOTIFICATION_ADAPTERS = []


def add_notification_func(callback_func) -> None:
    """
    Add a notification callback function to the list of notification adapters.

    Args:
        callback_func (function): The callback function to be added. The function parameters: (sender_id, receiver_ids, category_str, record_status, summary_str, params_dict) -> core.core.lang.Boolean2
    """
    if callback_func is not None and callback_func not in __NOTIFICATION_ADAPTERS:
        __NOTIFICATION_ADAPTERS.append(callback_func)

    if callback_func is not None and callback_func not in __NOTIFICATION_ADAPTERS:
        __NOTIFICATION_ADAPTERS.append(callback_func)


def get_notification_funcs() -> list:
    return [r for r in __NOTIFICATION_ADAPTERS]


@unique
class MessageCategory(Enum):
    """Inbox message category
    """
    CLAIM = "Expense"  # INBOX_NOTIFY_CATEGORY_CLAIM
    ADVANCEMENT = "Cash Advancement"  # INBOX_NOTIFY_CATEGORY_CASH_ADVANCEMENT
    EXCHANGE = "Cash Exchange"  # INBOX_NOTIFY_CATEGORY_CASH_ADVANCEMENT
    PO = "PO"  # INBOX_NOTIFY_CATEGORY_PO
    # TS_REMINDER = "TS Reminder"  # INBOX_NOTIFY_CATEGORY_TS_REMINDER


def __is_add_notify_url(status: str, claimer_id: int, receiver_id: int) -> bool:
    return status != Status.REJECTED.value or claimer_id == receiver_id


'''
    Submit & Cancel & Reject Notification
'''


def send_submit_cancel_reject_expense_notify(operator_id: int, expense_record: Expense) -> None:
    return __send_submit_cancel_reject_notify(operator_id, ExpenseType.EXPENSE, expense_record)


def send_submit_cancel_reject_cash_advancement_notify(operator_id: int, cash_advancement_record: CashAdvancement) -> None:
    return __send_submit_cancel_reject_notify(operator_id, ExpenseType.CASH_ADVANCEMENT, cash_advancement_record)


def __send_submit_cancel_reject_notify(operator_id: int, payment_type: ExpenseType, hdr_rc: Expense | CashAdvancement) -> None:
    try:
        need_to_send_mail = is_enable_email_notification()
        need_to_send_inbox = is_enable_default_inbox_message()
        if not need_to_send_mail and not need_to_send_inbox:
            logger.info("ignore send email and inbox.")
            return

        # email
        operator_name = User.objects.filter(id=operator_id).first().usr_nm
        subject = None
        template_file = None
        error_msg_header = "Send notify email failed: "
        send_to_user_id_list = []
        parameters = {}

        # hdr normal
        sn = hdr_rc.sn
        office_rc = hdr_rc.office
        payee_id = hdr_rc.payee_id
        claimer_id = hdr_rc.claimer_id
        claimer_name = hdr_rc.claimer.usr_nm
        approver_id = hdr_rc.approver_id
        status = hdr_rc.sts
        claim_amt = hdr_rc.claim_amt

        # 1. Expense
        if payment_type == ExpenseType.EXPENSE:
            if isNullBlank(hdr_rc):
                logger.info(
                    "Expense ID: %s does not exist, send submit or cancel or reject expense email failed." % hdr_rc.id)
                return
            dtl_rcs = ExpenseDetail.objects.filter(hdr=hdr_rc).order_by("seq")

            if status == Status.SUBMITTED.value:
                subject = "%s %s an expense: %s" % (claimer_name, status, sn)
                template_file = "submit-expense.html"
            elif status == Status.CANCELLED.value:
                subject = "%s %s an expense: %s" % (claimer_name, status, sn)
                template_file = "cancel-expense.html"
            elif status == Status.REJECTED.value:
                subject = "%s %s an expense: %s" % (operator_name, status, sn)
                template_file = "reject-expense.html"
            else:
                logger.error(error_msg_header + "UnSupport status: %s" % status)

            prior_balance_rcs = PriorBalance.objects.filter(expense=hdr_rc)
            prior_balance_payee_amt = 0
            for prior_balance_rc in prior_balance_rcs:
                prior_balance_payee_amt += prior_balance_rc.balance_amt if isNotNullBlank(prior_balance_rc.balance_amt) else 0

            parameters.update({"expense": hdr_rc})
            parameters.update({"priorBalancePayeeAmt": prior_balance_payee_amt if prior_balance_payee_amt > 0 else None})
            parameters.update({"settleByPriorBalance": const.getSettleByPriorBalanceDisplayValue(hdr_rc.use_prior_balance)})

        # 2. Cash Advancement
        elif payment_type == ExpenseType.CASH_ADVANCEMENT:
            if isNullBlank(hdr_rc):
                logger.info("Cash advancement ID: %s does not exist, send submit or cancel or reject cash advancement failed." % hdr_rc.id)
                return

            if status == Status.SUBMITTED.value:
                subject = "%s %s a cash advancement: %s" % (
                    claimer_name, status, sn)
                template_file = "submit-cash-advancement.html"
            elif status == Status.CANCELLED.value:
                subject = "%s %s a cash advancement: %s" % (
                    claimer_name, status, sn)
                template_file = "cancel-cash-advancement.html"
            elif status == Status.REJECTED.value:
                subject = "%s %s a cash advancement: %s" % (
                    operator_name, status, sn)
                template_file = "reject-cash-advancement.html"
            else:
                logger.error(error_msg_header + "UnSupport status: %s" % status)

            parameters.update({"ca": hdr_rc})

        parameters.update({"subject": subject})

        # add email receivers
        if status == Status.SUBMITTED.value or status == Status.CANCELLED.value:  # submit | cancel
            send_to_user_id_list.append(approver_id)
            # assistant approver
            for assistant_approver in approver.get_approver_assistants(office_rc, hdr_rc.approver, True):
                send_to_user_id_list.append(assistant_approver.id)
        elif status == Status.REJECTED.value:  # reject
            send_to_user_id_list.append(claimer_id)
        send_to_user_id_list = list(set(send_to_user_id_list))

        # 1. send email
        if need_to_send_mail:
            try:
                _send_mail(subject, send_to_user_id_list,
                           None, template_file, parameters)
            except Exception as e:
                traceback.print_exc()
                logger.error("ES send email failure.", exc_info=True)

        # 2. send inbox
        if need_to_send_inbox:
            try:
                # financial activity
                financial_activity_rc = Activity.objects.filter(tp=ActivityType.EXPENSE.value if payment_type == ExpenseType.EXPENSE else ActivityType.CASH_ADVANCEMENT.value).filter(
                    transaction_id=hdr_rc.id, sts=status).order_by("-id").first()
                if payment_type == ExpenseType.EXPENSE and status == Status.REJECTED.value:
                    subject += ", Reason: %s" % financial_activity_rc.dsc

                if payment_type == ExpenseType.EXPENSE:
                    for receiver_id in send_to_user_id_list:
                        send_expense_notify_to_inbox(operator_id, receiver_id, status, subject, hdr_rc.id, __is_add_notify_url(
                            status, claimer_id, receiver_id))
                elif payment_type == ExpenseType.CASH_ADVANCEMENT:
                    for receiver_id in send_to_user_id_list:
                        send_cash_notify_to_inbox(operator_id, receiver_id, status, subject, hdr_rc.id, __is_add_notify_url(
                            status, claimer_id, receiver_id))
            except Exception as e:
                traceback.print_exc()
                logger.error("ES send Inbox failure.", exc_info=True)

    except Exception as e:
        traceback.print_exc()
        logger.error(e, exc_info=True)


'''
    Approve / Confirm petty Notification
'''


def send_approve_confirm_petty_expense_notify(operator_id: int, expense_record: Expense) -> None:
    return __send_approve_confirm_petty_notify(operator_id, ExpenseType.EXPENSE, expense_record)


def send_approve_cash_advancement_notify(operator_id: int, cash_advancement_record: CashAdvancement) -> None:
    return __send_approve_confirm_petty_notify(operator_id, ExpenseType.CASH_ADVANCEMENT, cash_advancement_record)


def __send_approve_confirm_petty_notify(operator_id: int, payment_type: ExpenseType, hdr_rc: Expense | CashAdvancement) -> None:
    try:
        need_to_send_mail = is_enable_email_notification()
        need_to_send_inbox = is_enable_default_inbox_message()
        if not need_to_send_mail and not need_to_send_inbox:
            logger.info("ignore send email and inbox.")
            return

        # email
        operator_name = User.objects.filter(id=operator_id).first().usr_nm
        subject = None
        template_file = None
        error_msg_header = "Send notify email failed: "
        send_to_user_id_list = []
        parameters = {}

        # hdr normal
        sn = hdr_rc.sn
        office_rc = hdr_rc.office
        payee_id = hdr_rc.payee_id
        claimer_id = hdr_rc.claimer_id
        claimer_name = hdr_rc.claimer.usr_nm
        approver_id = hdr_rc.approver_id
        status = hdr_rc.sts
        claim_amt = hdr_rc.claim_amt
        is_petty_cash_expense = False
        is_petty_cash_expense_send_to_payer = False

        # 1. Expense
        if payment_type == ExpenseType.EXPENSE:
            dtl_rcs = ExpenseDetail.objects.filter(hdr=hdr_rc).order_by("file__seq")
            # payRc = hdr_rc.pay
            is_petty_cash_expense = hdr_rc.is_petty_expense
            is_petty_cash_expense_send_to_payer = True if is_petty_cash_expense and status == Status.APPROVED.value and isNotNullBlank(hdr_rc.petty_expense_activity) else False

            if status == Status.FIRST_APPROVED.value or status == Status.APPROVED.value:
                if is_petty_cash_expense:
                    if is_petty_cash_expense_send_to_payer:
                        subject = "%s confirm a petty cash expense to pay: %s" % (
                            UserManager.getUserName(hdr_rc.petty_expense_activity.operator_id), sn)
                    else:
                        subject = "%s %s a petty cash expense: %s" % (operator_name, status, sn)
                else:
                    if status == Status.FIRST_APPROVED.value:
                        subject = "%s %s an expense: %s (wait for 2nd approval)" % (operator_name, 'approved', sn)
                    else:
                        subject = "%s %s an expense: %s" % (operator_name, status, sn)
                template_file = "approve-expense.html"
            else:
                logger.error(error_msg_header + "UnSupport status: %s" % status)

            prior_balance_rcs = PriorBalance.objects.filter(expense=hdr_rc)
            prior_balance_payee_amt = 0
            for prior_balance_rc in prior_balance_rcs:
                prior_balance_payee_amt += prior_balance_rc.balance_amt if isNotNullBlank(prior_balance_rc.balance_amt) else 0

            parameters.update({"expense": hdr_rc})
            parameters.update({"priorBalancePayeeAmt": prior_balance_payee_amt if prior_balance_payee_amt > 0 else None})
            parameters.update({"settleByPriorBalance": const.getSettleByPriorBalanceDisplayValue(hdr_rc.use_prior_balance)})

        # 2. Cash Advancement
        elif payment_type == ExpenseType.CASH_ADVANCEMENT:
            if isNullBlank(hdr_rc):
                logger.info("Cash advancement ID: %s does not exist, send approve cash advancement failed." % hdr_rc.id)
                return

            template_file = "approve-cash-advancement.html"
            if status == Status.FIRST_APPROVED.value:
                subject = "%s %s an cash advancement: %s (wait for 2nd approval)" % (operator_name, 'approved', sn)
            elif status == Status.APPROVED.value:
                subject = "%s %s an cash advancement: %s" % (operator_name, status, sn)
            else:
                logger.error(error_msg_header + "UnSupport status: %s" % status)

            parameters.update({"ca": hdr_rc})
        parameters.update({"subject": subject})

        # add email receivers
        if status == Status.FIRST_APPROVED.value:  # first approve
            # second approver
            for second_approver in approver.get_second_approvers(office_rc, hdr_rc.approver, True):
                send_to_user_id_list.append(second_approver.second_approver.id)
        elif status == Status.APPROVED.value:  # approve
            if is_petty_cash_expense and not is_petty_cash_expense_send_to_payer:
                # petty admin
                petty_admin = get_petty_admin(office_rc)
                if isNotNullBlank(petty_admin):
                    send_to_user_id_list.append(petty_admin.id)
            else:
                # accounting(payer)
                for usr_id in get_accounting_user_ids(office_rc):
                    if usr_id != operator_id:
                        send_to_user_id_list.append(usr_id)
        send_to_user_id_list = list(set(send_to_user_id_list))

        # 1. send email
        if need_to_send_mail:
            try:
                _send_mail(subject, send_to_user_id_list, None, template_file, parameters)
            except Exception as e:
                traceback.print_exc()
                logger.error("ES send email failure.", exc_info=True)

        # 2. send inbox
        if need_to_send_inbox:
            try:
                if payment_type == ExpenseType.EXPENSE:
                    for receiver_id in send_to_user_id_list:
                        send_expense_notify_to_inbox(operator_id, receiver_id, status, subject, hdr_rc.id, __is_add_notify_url(
                            status, claimer_id, receiver_id))
                elif payment_type == ExpenseType.CASH_ADVANCEMENT:
                    for receiver_id in send_to_user_id_list:
                        send_cash_notify_to_inbox(operator_id, receiver_id, status, subject, hdr_rc.id, __is_add_notify_url(
                            status, claimer_id, receiver_id))
            except Exception as e:
                traceback.print_exc()
                logger.error("ES send Inbox failure.", exc_info=True)
    except Exception as e:
        traceback.print_exc()
        logger.error(e, exc_info=True)


def send_po_notify(operator_id: int, po_rc: Po) -> None:
    """ Submit/Approve/Reject notification for PO -- YL, 2025-04-15

    Args:
        operator_id (int): operator id
        po_rc (Po): Po Record
    """
    try:
        need_to_send_mail = is_enable_email_notification()
        need_to_send_inbox = is_enable_default_inbox_message()
        if not need_to_send_mail and not need_to_send_inbox:
            logger.info("ignore send email and inbox.")
            return

        if isNullBlank(po_rc):
            logger.info("po_rc is null, send submit or cancel or reject expense email failed.")
            return

        # email
        operator_name = User.objects.filter(id=operator_id).first().usr_nm
        subject = "PO Request."
        template_file = "po-notification.html"
        error_msg_header = "Send notify email failed: "
        send_to_user_id_list = []
        send_cc_user_id_list = []
        parameters = {}
        parameters.update({"sn": po_rc.sn})
        parameters.update({"action": po_rc.status})
        parameters.update({"approver": po_rc.assigned_approver.usr_nm})
        parameters.update({"submitter": po_rc.submitter.usr_nm})

        # add email receivers
        status = po_rc.status
        if status == Po.SUBMITTED_STATUS:
            send_to_user_id_list.append(po_rc.assigned_approver.id)
            # assistant approver
            for assistant_approver in approver.get_approver_assistants(po_rc.office, po_rc.assigned_approver, True):
                send_to_user_id_list.append(assistant_approver.id)
        elif status == Po.APPROVED_STATUS or status == Po.REJECTED_STATUS:
            parameters.update({"operator": po_rc.approver.usr_nm if po_rc.status == Po.APPROVED_STATUS else po_rc.rejecter.usr_nm})
            send_to_user_id_list.append(po_rc.submitter.id)
            if po_rc.assigned_approver.id != operator_id:
                send_cc_user_id_list.append(po_rc.assigned_approver.id)
            # assistant approver
            for assistant_approver in approver.get_approver_assistants(po_rc.office, po_rc.assigned_approver, True):
                if assistant_approver.id not in send_to_user_id_list:
                    send_cc_user_id_list.append(assistant_approver.id)
            send_cc_user_id_list.append(operator_id)
        send_to_user_id_list = list(set(send_to_user_id_list))
        send_cc_user_id_list = list(set(send_cc_user_id_list))

        # 1. send email
        if need_to_send_mail:
            try:
                _send_mail(subject, send_to_user_id_list, send_cc_user_id_list, template_file, parameters)
            except Exception as e:
                traceback.print_exc()
                logger.error("PO send email failure.", exc_info=True)

        # 2. send inbox
        if need_to_send_inbox:
            try:
                summary = "%s %s a purchase approval: %s" % (operator_name, status, po_rc.sn)
                all_user_ids = list(set(send_to_user_id_list + send_cc_user_id_list))
                for receiver_id in all_user_ids:
                    send_po_to_inbox(operator_id, receiver_id, status, summary, po_rc.id, __is_add_notify_url(
                        status, po_rc.submitter.id, receiver_id))
            except Exception as e:
                traceback.print_exc()
                logger.error("ES send Inbox failure.", exc_info=True)

    except Exception as e:
        traceback.print_exc()
        logger.error(e, exc_info=True)


def sendRequestCashAdvancementExchangeEmail(fxRc: ForeignExchange) -> None:
    # TODO:
    pass


def _send_mail(subject: str, to_usr_id_list: list[int], cc_usr_id_list: list[int], template_file: str, parameters: dict):
    """
    Send Email

    Args:
        subject (str): subject
        to_usr_id_list (list[int]): to user ID list
        cc_usr_id_list (list[int]): cc user ID list
        template_file (str): template file path
        parameters (dict): template file parameters
    """
    template_file_path = 'es/mail/%s' % template_file

    MailManager.send(sender="ES", subject=subject, template_file=template_file_path,
                     template_parameter=parameters, to=to_usr_id_list, cc=cc_usr_id_list)


def send_expense_notify_to_inbox(sender_id: int, receiver_id: int, status: str, summary: str, hdr_id: int, add_url: bool) -> Boolean2:
    menu_id = None
    if add_url:
        if status == Status.REJECTED.value:
            menu_id = MenuManager.getMenuIdByScreenName(const.MENU_ES004)
        else:
            menu_id = MenuManager.getMenuIdByScreenName(const.MENU_ES005)
    return _send_notify_to_inbox(sender_id, receiver_id, MessageCategory.CLAIM, status, summary, hdr_id, menu_id, add_url)


def send_cash_notify_to_inbox(sender_id: int, receiver_id: int, status: str, summary: str, cashID: int, add_url: bool) -> Boolean2:
    menu_id = None
    if add_url:
        menu_id = MenuManager.getMenuIdByScreenName(const.MENU_ES006)
    return _send_notify_to_inbox(sender_id, receiver_id, MessageCategory.ADVANCEMENT, status, summary, cashID, menu_id, add_url)


def send_po_to_inbox(sender_id: int, receiver_id: int, status: str, summary: str, po_id: int, add_url: bool) -> Boolean2:
    """ For PO -- YL, 2025-04-15
    """
    menu_id = None
    if add_url:
        menu_id = MenuManager.getMenuIdByScreenName(const.MENU_PO001)
    return _send_notify_to_inbox(sender_id, receiver_id, MessageCategory.PO, status, summary, po_id, menu_id, add_url)


def _send_notify_to_inbox(sender_id: int, receiver_id: int, category: MessageCategory, status: str, summary: str, id: int, menu_id: int, add_url: bool) -> Boolean2:
    """
    Send Inbox

    Args:
        sender_id (int): operator ID
        receiver_id (int): receiver ID
        category (MessageCategory): category
        status (str): status
        summary (str): summary
        id (int): object ID
        menu_id (int): menu ID
        add_url (bool): add url

    Returns:
        Boolean2: send success or not
    """
    params = {}
    if add_url:
        params.update({InboxManager.ACTION_COMMAND: menu_id})
        if isNotNullBlank(id) and int(id) > 0:
            params.update({"id": id})
    success_msgs = []
    failed_msgs = []
    try:
        InboxManager.send(senderID=sender_id, receiverIDs=receiver_id, module=category.value, summary=summary, linkParameters=params)
        success_msgs.append("success")
    except Exception as e:
        logger.error(e)
        failed_msgs.append(str(e))
    # use WCI2 inbox
    for notification_func in __NOTIFICATION_ADAPTERS:
        rst = notification_func(sender_id, receiver_id, category.value, status, summary, params)
        rst: Boolean2
        if rst.value:
            success_msgs.append(rst.dataStr)
        else:
            failed_msgs.append(rst.dataStr)
    if len(failed_msgs) == 0:
        return Boolean2.TRUE("success")
    return Boolean2.FALSE(failed_msgs)
