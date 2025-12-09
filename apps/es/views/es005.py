import logging
import os
import traceback

import core.ui.ui as ikui
from core.core.exception import IkValidateException
from core.core.http import (IkErrJsonResponse, IkSccJsonResponse,
                            IkSysErrJsonResponse, responseFile)
from core.core.lang import Boolean2
from core.utils.lang_utils import isNotNullBlank, isNullBlank
from core.view.screen_view import _OPEN_SCREEN_PARAM_KEY_NAME

from ..core import acl, activity, ca, const, es, es_file, es_tools, status
from ..core.status import Status
from ..models import (Activity, CashAdvancement, Currency, Expense,
                      ExpenseDetail, ForeignExchange, PaymentMethod,
                      PettyCashExpenseAdmin, PriorBalance)
from .es_base import ESAPIView

logger = logging.getLogger('ikyo')

rateFormatter = "{:.7f}".format


class ES005(ESAPIView):
    '''
        Expense System -> ES005 - Expense Enquiry
    '''

    SESSION_KEY_FILE_ID = 'displayFileID'
    SESSION_KEY_EXPENSE_HDR_ID = 'currentExpenseID'
    SESSION_KEY_PB_DATA = 'priori_balance_input_data'

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            currentHdrID = self.__getCurrentExpenseHdrID()
            hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=currentHdrID).first() if currentHdrID is not None else None
            if hdrRc is None and isNotNullBlank(currentHdrID):
                currentHdrID = None
                self.deleteSessionParameters([self.SESSION_KEY_EXPENSE_HDR_ID, self.SESSION_KEY_FILE_ID])

            isDetailPage = hdrRc is not None
            screen.setFieldGroupsVisible(fieldGroupNames=['schFg', 'lineFg', 'hdrListFg'], visible=not isDetailPage)
            screen.setFieldGroupsVisible(fieldGroupNames=[
                "pdfViewer", "dtlFg", "hdrFg", "uploadFg", "priorBalanceExpenseFg", "pettyExpensePriorBalanceExpenseFg",
                "settleByPriorBalanceDetailFg", "sdToolbar", "toolbar", "activityFg"
            ], visible=isDetailPage)
            if not screen.getFieldGroup('pdfViewer').visible:
                screen.layoutParams = ""
                self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)

            if not isDetailPage:
                self.deleteSessionParameters(self.SESSION_KEY_EXPENSE_HDR_ID)

            if isDetailPage:
                operatorRc = self.getCurrentUser()
                cancelable = acl.is_cancelable(hdrRc.sts, hdrRc.claimer, operatorRc)
                editable = (hdrRc.sts == Status.CANCELLED.value or hdrRc.sts == Status.REJECTED.value) \
                    and operatorRc.id == hdrRc.claimer.id
                approveable = acl.is_approverable(operatorRc, hdrRc.sts, hdrRc.payee, hdrRc.claim_amt, hdrRc.approver)
                rejectable = acl.is_rejectable(operatorRc, hdrRc.sts, hdrRc.payee, hdrRc.claim_amt, hdrRc.approver,
                                               hdrRc.is_petty_expense, (hdrRc.petty_expense_activity is not None))
                settle_able = acl.is_settlable(operatorRc, hdrRc.sts, hdrRc.payee, hdrRc.claim_amt, hdrRc.approver,
                                               hdrRc.is_petty_expense, (hdrRc.petty_expense_activity is not None))
                revertSettledPayment = acl.can_revert_settled_payment(operatorRc, hdrRc.sts, hdrRc.payee.office)
                hasPaymentRecordFile = hdrRc.payment_record_file is not None
                isPettyExpense = hdrRc.is_petty_expense
                isSettleByPrioriBalance = hdrRc.use_prior_balance

                pettyCashExpenseAdminRc = PettyCashExpenseAdmin.objects.filter(office=hdrRc.office, admin=operatorRc).first() if isPettyExpense else None
                isPettyCashExpenseOfficeAdministrator = pettyCashExpenseAdminRc is not None

                isWait4SubmitPettyCashExpense = hdrRc.sts == Status.APPROVED.value and isPettyExpense and isNullBlank(hdrRc.petty_expense_activity)
                isSettleByPriorBalanceDetailFgVisible = isPettyExpense and isWait4SubmitPettyCashExpense and isPettyCashExpenseOfficeAdministrator
                isPettyExpensePriorBalanceExpenseFgVisible = isPettyExpense and not isWait4SubmitPettyCashExpense \
                    and (self.isAdministrator() or hdrRc.last_activity is not None and operatorRc.id == hdrRc.last_activity.operator_id)

                hasSupportingDoc = hdrRc is not None and hdrRc.supporting_doc is not None

                if isPettyExpense:
                    dtlFgCaption = "Petty Cash Expense Detail"
                    if isWait4SubmitPettyCashExpense:
                        dtlFgCaption += " - Wait for office administrator to confirm"
                    screen.setFieldGroupCaption("dtlFg", dtlFgCaption)

                screen.setFieldGroupsVisible('priorBalanceExpenseFg', isSettleByPrioriBalance)
                screen.setFieldGroupsVisible('settleByPriorBalanceDetailFg', isSettleByPriorBalanceDetailFgVisible)
                screen.setFieldGroupsVisible('pettyExpensePriorBalanceExpenseFg', isPettyExpensePriorBalanceExpenseFgVisible)

                screen.setFieldsEditable('hdrFg', 'trnTpField', settle_able)
                screen.setFieldsEditable('hdrFg', 'trnNoField', settle_able and not isPettyExpense and not (
                    isSettleByPrioriBalance and (isNullBlank(hdrRc.pay_amt) or hdrRc.pay_amt == 0)))
                screen.setFieldGroupsVisible(('uploadFg'), settle_able)
                screen.setFieldsEditable('hdrFg', 'cancelRejectReasonField', cancelable or rejectable)
                screen.setFieldsVisible('hdrFg', 'cancelRejectReasonField', cancelable or rejectable)
                reason_caption = "Cancel / Reject Reason" if cancelable and rejectable else "Cancel Reason" if cancelable else "Reject Reason" if rejectable else ""
                screen.setFieldCaption(fieldGroupName='hdrFg', fieldName='cancelRejectReasonField', value=reason_caption)

                screen.setFieldsEditable('hdrFg', 'revertSettledPaymentReasonField', revertSettledPayment)
                screen.setFieldsVisible('hdrFg', 'revertSettledPaymentReasonField', revertSettledPayment)

                screen.setFieldsVisible('toolbar', 'bttEdit', editable)
                screen.setFieldsVisible('toolbar', 'bttCancel', cancelable)

                screen.setFieldsVisible('sdToolbar', 'bttUploadSD', approveable)
                screen.setFieldsVisible('sdToolbar', ['bttDisplaySD', 'bttDownloadSD'], hasSupportingDoc and hdrRc.claimer != self.getCurrentUser())
                screen.setFieldsVisible('sdToolbar', 'bttDeleteSD', hasSupportingDoc and approveable)

                screen.setFieldsVisible('toolbar', 'bttApprove', approveable)
                screen.setFieldsVisible('toolbar', 'bttSettlePettyExpense', isWait4SubmitPettyCashExpense and isPettyCashExpenseOfficeAdministrator)
                screen.setFieldsVisible('toolbar', 'bttReject', rejectable)
                screen.setFieldsVisible('toolbar', 'bttSettle', settle_able)
                screen.setFieldsVisible('toolbar', 'bttRevertSettledPayment', revertSettledPayment)
                screen.setFieldsVisible('toolbar', ['bttDisplayPaymentRecord', 'bttDownloadPaymentRecord'], hasPaymentRecordFile)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getSts(self):
        return status.get_all_status()

    def getPaymentMethodRcs(self):
        expense_rc = self.__getCurrentExpenseHdr()
        if isNotNullBlank(expense_rc):
            if expense_rc.is_petty_expense:
                return PaymentMethod.objects.filter(tp=PaymentMethod.PETTY_CASH)
            elif expense_rc.use_prior_balance and (isNullBlank(expense_rc.pay_amt) or expense_rc.pay_amt == 0):
                return PaymentMethod.objects.filter(tp=PaymentMethod.PRIOR_BALANCE)
        return PaymentMethod.objects.exclude(tp__in=[PaymentMethod.PETTY_CASH, PaymentMethod.PRIOR_BALANCE])

    def getHdrRcs(self):
        """Get expense record the current user can access to."""
        query_params = {}
        search_data = self.getSearchData(fieldGroupName='schFg')
        if isNotNullBlank(search_data):
            query_params['sn'] = search_data.get('schSNField', None)
            query_params['claimer'] = search_data.get('schClaimerField', None)
            query_params['status'] = search_data.get('schStsField', None)
            query_params['payee'] = search_data.get('schPayeeField', None)
            query_params['pay_transfer_no'] = search_data.get('schPayTransferNoField', None)
            query_params['expense_page_no'] = search_data.get('schExpensePageNoField', None)
            query_params['support_document_page_no'] = search_data.get('schSupportDocumentPageNo', None)
            query_params['payment_record_page_no'] = search_data.get('schPaymentRecordPageNoField', None)
            query_params['payment_record_filename'] = search_data.get('schPaymentRecordField', None)
            query_params['claim_date_from'] = search_data.get('schClaimDateFromField', None)
            query_params['claim_date_to'] = search_data.get('schClaimDateToField', None)
            query_params['approve_date_from'] = search_data.get('schApprovedDateFromField', None)
            query_params['approve_date_to'] = search_data.get('schApprovedDateToField', None)
            query_params['settle_date_from'] = search_data.get('schSettleDateFromField', None)
            query_params['settle_date_to'] = search_data.get('schSettleDateToField', None)
            query_params['cat'] = search_data.get('schExpenseCtgField', None)
            query_params['prj_nm'] = search_data.get('schExpensePrjField', None)
            query_params['description'] = search_data.get('schExpenseDscField', None)

        query_result = Expense.objects
        query_result = es.query_expenses(self.getCurrentUser(), self._getCurrentOffice(), query_result, query_params)
        query_result = query_result.exclude(sts=Status.DRAFT.value).order_by('-submit_dt')

        def get_style_func(dataRcs) -> list:
            style = []
            for r in dataRcs:
                style.append({"row": r['id'], "class": "row_" + r['sts']})
            return style
        return self.getPagingResponse(table_name="hdrListFg", table_data=query_result, get_style_func=get_style_func)

    def hdrListFg_EditIndexField_Click(self):
        """Click open detail icon in the table's last column."""
        expense_id = self._getEditIndexField()
        # TODO: permission check
        expense_rc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=expense_id).first()
        if expense_rc is None:
            return Boolean2.FALSE("Expense doesn't exist.")
        self.setSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID, expense_id)
        default_display_file_id = ExpenseDetail.objects.filter(hdr=expense_rc).order_by('seq').first().file.id
        self.setSessionParameter(self.SESSION_KEY_FILE_ID, default_display_file_id)
        self._deletePreviousScreenRequestData()

    def getHdrRc(self):
        expense_id = self.__getCurrentExpenseHdrID()
        if isNullBlank(expense_id):
            return
        hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=expense_id).first()
        if hdrRc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_id)
            raise IkValidateException("Expense doesn't exist.")
        # TODO: permission check
        # calculate pay amount
        if hdrRc.sts == Status.SUBMITTED.value:
            totalClaimAmount = hdrRc.claim_amt
            thisPayAmount = 0.0
            if not hdrRc.use_prior_balance:
                thisPayAmount = totalClaimAmount
            else:
                priorBalanceAmount = es.getExpensePriorBalanceAmount(expense_id)
                thisPayAmount = float(es_tools.round2(es_tools.sub(totalClaimAmount, priorBalanceAmount)))
                if thisPayAmount < 0:
                    thisPayAmount = 0  # no need to pay
            hdrRc.pay_amt = thisPayAmount
        # Update display fields
        hdrRc.trn_tp_id = hdrRc.payment_tp.id if hdrRc.payment_tp is not None else None
        hdrRc.trn_no = hdrRc.payment_number
        return hdrRc

    # Detail page
    def getDtlRcs(self):
        """Return expense detail list"""
        # from Inbox part
        expense_id = self.__getCurrentExpenseHdrID()
        if isNullBlank(expense_id):
            return
        hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=expense_id).first()
        if hdrRc is None:
            logger.error("Expense doesn't exist. ID=%s" % expense_id)
            raise IkValidateException("Expense doesn't exist.")
        rcs = ExpenseDetail.objects.filter(hdr=hdrRc).order_by("file__seq", "incur_dt", 'seq')
        displayFileID = self.getSessionParameter(self.SESSION_KEY_FILE_ID)
        for rc in rcs:
            rc.is_current = False  # used for display
            if isNotNullBlank(displayFileID) and rc.file and rc.file.id == displayFileID:
                rc.ik_set_cursor()
                rc.is_current = True
        return rcs

    def displayExpenseFile(self):
        """Click the [Expense Details] table to display the selected record's file."""
        currentHdrID = self.__getCurrentExpenseHdrID()
        displayFileID = None
        if isNotNullBlank(currentHdrID):
            # TODO: permission check
            hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=currentHdrID).first()
            if hdrRc is None:
                logger.error("Expense doesn't exist. ID=%s" % currentHdrID)
                raise IkValidateException("Expense doesn't exist.")
            requestData = self.getRequestData()
            expenseID = requestData.get('id')
            if isNotNullBlank(expenseID):
                expenseID = int(expenseID)
                expenseDtlRc = ExpenseDetail.objects.filter(hdr=hdrRc, id=expenseID).first()
                if expenseDtlRc is not None:
                    displayFileID = expenseDtlRc.file.id
        self.setSessionParameter(self.SESSION_KEY_FILE_ID, displayFileID)

    def downloadExpenseFile(self):
        """Click the [Expense Details] table to download the selected record's file."""
        requestData = self.getRequestData()
        fileID = requestData.get('row', {}).get('file_id', None)
        if fileID is None:
            return IkErrJsonResponse(message="File is not found.")
        f = es_file.getESFile(int(fileID))
        if f is None:
            return IkErrJsonResponse(message="File is not found.")
        else:
            return responseFile(filePath=f.file, filename=f.filename)

    def displayPaymentRecordFile(self):
        hdrFg = self.getRequestData().get('hdrFg')
        if isNotNullBlank(hdrFg):
            self.setSessionParameters({"displayFileID": hdrFg.e_cheque_file_id, "isOpenEChequeFile": True})
            return IkSccJsonResponse()

    # combobox
    def getSettleByPriorBalances(self):
        data = [{
            "value": const.SETTLE_BY_PRIOR_BALANCE_NO,
            "display": const.SETTLE_BY_PRIOR_BALANCE_NO_DISPLAY
        }, {
            "value": const.SETTLE_BY_PRIOR_BALANCE_YES,
            "display": const.SETTLE_BY_PRIOR_BALANCE_YES_DISPLAY
        }]
        return data

    # combobox
    def getTrnTypes(self):
        qs = PaymentMethod.objects.all().order_by("tp")
        data = [{"trn_tp_id": r.id, "tp": r.tp} for r in qs]
        return data

    # pdf viewer
    def getPdfViewer(self):
        displayFileID = self.getSessionParameter(self.SESSION_KEY_FILE_ID)
        if isNotNullBlank(displayFileID):
            ef = es_file.getESFile(displayFileID)
            if isNotNullBlank(ef):
                if os.path.isfile(ef.file):
                    return responseFile(filePath=ef.file, filename=ef.filename)
            expense_sn = self.__getCurrentExpenseHdr().sn
            logger.error("es File is not found. SN=%s, FileID=%s, Path=%s" % (expense_sn, displayFileID, ef.file.resolve()))
            filePath = es_file.get_not_exist_file_template()
            return responseFile(filePath)
        return IkSccJsonResponse()

    def getPriorBalanceRcs(self):
        currentHdrRc = self.__getCurrentExpenseHdr()
        if currentHdrRc is None:
            return
        return ca.getPriorBalanceInfo(currentHdrRc)

    def getPettyCashPriorBalanceRcs(self):
        data = None
        hdrRc = self.__getCurrentExpenseHdr()
        if hdrRc is not None:
            data = []
            for rc in PriorBalance.objects.filter(expense=hdrRc).order_by('ca_id'):
                amount = rc.fx_balance_amt if rc.fx_balance_amt is not None else rc.claim_amt
                ccy = "%s (FX)" % rc.fx.fx_ccy.code if rc.fx is not None else rc.expense.office.ccy.code
                data.append({'cash_payee': rc.ca.payee.payee, 'cash_sn': rc.ca.sn, 'ccy': ccy, 'balance_amt': amount})
        return data

    def getAvailablePriorBalanceCashPaymentRcs(self):
        availableRcs = None
        currentHdrID = self.__getCurrentExpenseHdrID()
        if isNotNullBlank(currentHdrID):
            self.deleteSessionParameters(self.SESSION_KEY_PB_DATA)
            hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=currentHdrID).first()
            if hdrRc.is_petty_expense is True:
                paRc = PettyCashExpenseAdmin.objects.filter(office=hdrRc.office, admin=self.getCurrentUser(), enable=True).first()
                if paRc is not None and paRc.admin_payee is not None:
                    availableRcs = ca.getAvailablePriorBalanceRcs(paRc.admin_payee, hdrRc.office.ccy)
                    if len(availableRcs) == 0:
                        return IkErrJsonResponse(message="No more cash advancement left for payee [%s]." % paRc.admin_payee.payee)
                    else:
                        totalAmount = hdrRc.pay_amt
                        totalLeft = totalAmount
                        for rc in availableRcs:
                            if totalLeft > 0:
                                cashLeft = rc.balance_amt
                                if cashLeft > 0:
                                    thisAmount = cashLeft if totalLeft > cashLeft else totalLeft
                                    rc.deduction_amt = float(thisAmount)
                                    totalLeft = es_tools.sub(totalLeft, thisAmount)
                            if totalLeft <= 0:
                                break
                        if totalLeft > 0:
                            self._addWarnMessage("No enough advanced left. Please check.")
                        self.setSessionParameter(self.SESSION_KEY_PB_DATA, [
                                                 [r.ca.id, r.ccy.id, r.fx.id if r.fx is not None else None, r.total_amt, r.balance_amt] for r in availableRcs])
        return availableRcs

    # button events

    def back(self):
        # get po id if have
        expense_rc = self.__getCurrentExpenseHdr()
        po_id = None
        po_id = expense_rc.po_id if isNotNullBlank(expense_rc) and isNotNullBlank(expense_rc.po) else None
        self.deleteSessionParameters([self.SESSION_KEY_EXPENSE_HDR_ID, self.SESSION_KEY_FILE_ID, self.SESSION_KEY_PB_DATA])
        pre_screen_nm = self._getPreviousScreenName()
        if isNotNullBlank(pre_screen_nm):
            params = {'id': po_id, 'es_id': expense_rc.id} if pre_screen_nm == const.MENU_PO001 else None
            return self._openScreen(menuName=pre_screen_nm, parameters=params)

    def editExpense(self):
        """Click the [Edit] button to edit the cancelled/rejected expense."""
        expense_id = self.__getCurrentExpenseHdrID()
        if expense_id is not None:
            hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=expense_id).first()
            if hdrRc is not None:
                if hdrRc.sts != Status.CANCELLED.value and hdrRc.sts != Status.REJECTED.value:
                    return IkErrJsonResponse(message="Only [Cancelled] and [Rejected] expenses can be edit.")
                if hdrRc.claimer.id != self.getCurrentUserId():
                    return IkErrJsonResponse(message="Permission deny. Only claimer can edit this expense.")
                # open expense submit screen
                return self._openScreen(const.MENU_ES004, parameters={'id': hdrRc.id})

    def cancel(self):
        """Click the [Cancel] button to cancel the expense."""
        expense_rc = self.getRequestData().get('hdrFg', None)
        if isNullBlank(expense_rc):
            return IkSysErrJsonResponse()
        expense_rc: Expense
        result = es.cancel_expense(self.getCurrentUserId(), expense_rc.id, expense_rc.action_rmk)
        if not result.value:
            return result.toIkJsonResponse1()
        self._addInfoMessage(result.dataStr)
        return self._openScreen(const.MENU_ES004, parameters={'id': expense_rc.id})

    def reject(self):
        """Click the [Reject] button to cancel the expense."""
        expense_rc = self.getRequestData().get('hdrFg', None)
        if isNullBlank(expense_rc):
            return IkSysErrJsonResponse()
        expense_rc: Expense
        result = es.reject_expense(self.getCurrentUserId(), expense_rc.id, expense_rc.action_rmk)
        return result.toIkJsonResponse1()

    def approve(self):
        """Click the [Approve] button to cancel the expense."""
        expense_rc = self.getRequestData().get('hdrFg', None)
        if isNullBlank(expense_rc):
            return IkSysErrJsonResponse()
        expense_rc: Expense
        result = es.approve_expense(self.getCurrentUserId(), expense_rc.id)
        return result.toIkJsonResponse1()

    def submitPettyCashExpense(self):
        try:
            expense_id = self.__getCurrentExpenseHdrID()
            if isNullBlank(expense_id):
                return IkValidateException("Please select an expense first.")
            availablePriorBalanceRcs = self._getRequestValue('settleByPriorBalanceDetailFg', default=None)
            priorBalanceRcs = None
            if availablePriorBalanceRcs is not None:
                priorBalanceRcs = []
                pbTableData = self.getSessionParameter(self.SESSION_KEY_PB_DATA)
                rowNo = -1
                for r in availablePriorBalanceRcs:
                    rowNo += 1
                    rowData = pbTableData[rowNo]
                    r.ca = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=rowData[0]).first()
                    r.ccy = Currency.objects.filter(id=rowData[1]).first()
                    r.fx = ForeignExchange.objects.filter(id=rowData[2]).first() if isNotNullBlank(rowData[2]) else None
                    r.total_amt = rowData[3]
                    r.balance_amt = rowData[4]

                    pb = r.deduction_amt
                    if isNotNullBlank(pb):
                        try:
                            pb = float(str(pb).strip())
                        except:
                            raise IkValidateException('The [This Claim] column should be a numeric greater than 0. Please check.')
                        if pb < 0:
                            raise IkValidateException('The [This Claim] column should be a numeric greater than 0. Please check.')
                        if pb > 0:
                            r.deduction_amt = pb
                            priorBalanceRcs.append(r)

            boo = es.confirm_petty_cash_expense(self.getCurrentUserId(), expense_id, priorBalanceRcs)
            if not boo.value:
                return IkErrJsonResponse(message=boo.dataStr)
            else:
                self.back()
                return IkSccJsonResponse(message="Petty Cash Expense submitted!")
        except Exception as e:
            traceback.print_exc()
            logger.error(str(e))
            return IkErrJsonResponse(message=str(e))

    def settle(self):
        """Click [Settle] button to pay the expense."""
        upload_page_file = None
        is_success = False
        try:
            expense_hdr_id = self.__getCurrentExpenseHdrID()
            if isNullBlank(expense_hdr_id):
                return IkErrJsonResponse(message="Please select an approved cash advancement first.")
            hdr_rc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=expense_hdr_id).first()
            if hdr_rc is None:
                logger.error("Expense doesn't exist.")
                return IkErrJsonResponse(message="Expense doesn't exist.")

            hdr_rc = self.getRequestData().get('hdrFg')
            hdr_rc: Expense

            payment_type = hdr_rc.payment_tp
            payment_no = hdr_rc.payment_number
            if isNullBlank(payment_type):
                return IkErrJsonResponse(message="Please select a Transaction Type.")
            if isNullBlank(payment_no) and payment_type.tp != PaymentMethod.PETTY_CASH and not (payment_type.tp == PaymentMethod.PRIOR_BALANCE and (isNullBlank(hdr_rc.pay_amt) or hdr_rc.pay_amt == 0)):
                return IkErrJsonResponse(message="Please fill in the Transfer No. first.")
            payment_no = str(payment_no).strip() if isNotNullBlank(payment_no) else None
            payment_rmk = hdr_rc.action_rmk  # add payment remarks to screen

            uploadFiles = self.getRequestData().getFiles('uploadFile')
            if uploadFiles is None or len(uploadFiles) == 0 or uploadFiles[0] is None:
                if payment_type.tp != PaymentMethod.BANK_TRANSFER and payment_type.tp != PaymentMethod.PETTY_CASH and not (payment_type.tp == PaymentMethod.PRIOR_BALANCE and (isNullBlank(hdr_rc.pay_amt) or hdr_rc.pay_amt == 0)):
                    return IkErrJsonResponse(message="Please select a file to upload.")
            else:
                upload_page_file = es_file.save_uploaded_really_file(uploadFiles[0], self.__class__.__name__, self.getCurrentUserName())
            result = es.settle_expense(self.getCurrentUserId(), hdr_rc.id, payment_type, payment_no, upload_page_file, payment_rmk)
            is_success = result.value
            if is_success:
                if hdr_rc.payment_record_file is not None:
                    self.setSessionParameter(self.SESSION_KEY_FILE_ID, hdr_rc.payment_record_file.id)
            return result
        finally:
            if not is_success and upload_page_file is not None:
                es_file.delete_really_file(upload_page_file)

    def revertSettledPayment(self):
        expense_rc = self.getRequestData().get('hdrFg')
        if isNullBlank(expense_rc):
            return IkSysErrJsonResponse()
        expense_rc: Expense
        result = es.revert_settled_expense(self.getCurrentUserId(), expense_rc.id, expense_rc.action_rmk)
        if result.value:
            self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        return result

    def displayPaymentRecordFile(self):
        """Click [Display Payment Record] button to display the payment record."""
        ""
        self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        hdr_rc = self.__getCurrentExpenseHdr()
        if isNotNullBlank(hdr_rc) and isNotNullBlank(hdr_rc.payment_record_file):
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, hdr_rc.payment_record_file.id)
        else:
            return IkErrJsonResponse(message="No payment record file found.")

    def downloadPaymentRecordFile(self):
        """Click the [Download Payment Record] button to upload payment file."""
        hdr_rc = self.__getCurrentExpenseHdr()
        if isNullBlank(hdr_rc.payment_record_file):
            return IkErrJsonResponse(message="No payment record file found.")
        f = es_file.getESFile(hdr_rc.payment_record_file)
        if f is None:
            return IkErrJsonResponse(message="Payment record file doesn't exist.")
        else:
            return responseFile(filePath=f.file, filename="%s-PaymentRecord-%s" % (hdr_rc.sn, f.filename))

    def uploadSupportingDoc(self):
        """Click [Upload Supporting Document] button to upload supporting document."""
        office_rc = self._getCurrentOffice()
        if office_rc is None:
            return IkErrJsonResponse(message="Please select office first.")

        uploadFiles = self.getRequestData().getFiles('uploadField')
        if uploadFiles is None or len(uploadFiles) == 0 or uploadFiles[0] is None:
            return IkErrJsonResponse(message="Please select a file to upload.")
        hdrRc = self.__getCurrentExpenseHdr()
        uploadPageFile = None
        try:
            uploadPageFile = es_file.save_uploaded_really_file(uploadFiles[0], self.__class__.__name__, self.getCurrentUserName())
            new_file_rc = es.uploadExpenseSupportingDocument(self.getCurrentUserId(), hdrRc, uploadPageFile)
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, new_file_rc.id)
            uploadMessage = "If the supporting document has a hard copy, please write the sequence number %s "\
                "on the top right corner of the page and give it to the accounts department!" % new_file_rc.seq
            return IkSccJsonResponse(message=uploadMessage)
        finally:
            es_file.delete_really_file(uploadPageFile)

    def displaySupportingDoc(self):
        """Click [Display Supporting Document] button to display the supporting document."""
        ""
        self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        hdrRc = self.__getCurrentExpenseHdr()
        if hdrRc is not None and hdrRc.supporting_doc is not None:
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, hdrRc.supporting_doc.id)
        else:
            return IkErrJsonResponse(message="Supporting document doesn't exist.")

    def downloadSupportingDoc(self):
        """Click [Download Supporting Document] button to download the supporting document."""
        hdrRc = self.__getCurrentExpenseHdr()
        if hdrRc is not None and hdrRc.supporting_doc is not None:
            f = es_file.getESFile(hdrRc.supporting_doc.id)
            if not isNullBlank(f):
                return self.downloadFile(f.file, es.getExpenseSupportingDocumentFilename(hdrRc.supporting_doc))
        return IkErrJsonResponse(message="Supporting document doesn't exist.")

    def deleteSupportingDoc(self):
        """Click [Delete Supporting Document] button to delete the supporting document."""
        hdrRc = self.__getCurrentExpenseHdr()
        if hdrRc is not None:
            fileID = es.deleteExpenseSupportingDocument(self.getCurrentUserId(), hdrRc)
            if fileID is None:
                return IkErrJsonResponse(message="File doesn't exist.")
            if fileID == self.getSessionParameterInt(self.SESSION_KEY_FILE_ID):
                self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
            return IkSccJsonResponse(message="Deleted supporting document.")
        return IkErrJsonResponse(message="Supporting document doesn't exist.")

    def getActivityRcs(self):
        hdr_id = self.__getCurrentExpenseHdrID()
        data = Activity.objects.filter(transaction_id=hdr_id, tp=activity.ActivityType.EXPENSE.value).order_by("operate_dt")
        return IkSccJsonResponse(data=data)

    def __getCurrentExpenseHdrID(self) -> int:
        id = self.getSessionParameterInt(self.SESSION_KEY_EXPENSE_HDR_ID)
        pre_screen_nm = self._getPreviousScreenName()
        if isNullBlank(id) and isNotNullBlank(pre_screen_nm) and pre_screen_nm != self._menuName:
            request_data = self._getPreviousScreenRequestData()
            id = request_data.pop("id", None) if request_data is not None else None
            self.setSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, value=request_data, isGlobal=True)
            self.setSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID, id)
        return int(id) if id is not None else None

    def __getCurrentExpenseHdr(self) -> Expense:
        id = self.__getCurrentExpenseHdrID()
        hdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=id).first() if isNotNullBlank(id) else None
        if hdrRc is None:
            self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        elif isNullBlank(self.getSessionParameterInt(self.SESSION_KEY_FILE_ID)):
            # display default file
            dtlRc = ExpenseDetail.objects.filter(hdr=hdrRc, file__isnull=False).order_by('seq').first()
            if dtlRc is not None:
                self.setSessionParameter(self.SESSION_KEY_FILE_ID, dtlRc.file.id if dtlRc.file is not None else None)
        # TODO: validate permission
        return hdrRc
