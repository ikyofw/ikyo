""" Cash Advancement View
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from django.templatetags.static import static

import core.ui.ui as ikui
import es.core.acl as acl
import es.core.status as status
from core.core.exception import IkValidateException
from core.core.http import IkErrJsonResponse, IkSccJsonResponse, responseFile
from core.core.lang import Boolean2
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.view.screenView import _OPEN_SCREEN_PARAM_KEY_NAME
from es.core import CA, ES, ESFile, activity
from es.models import *
from es.views.es_base_views import ESAPIView

from ..core import ESFile as ESFileManager
from ..core import const
from ..core.approver import get_office_first_approvers
from ..core.status import Status

logger = logging.getLogger('ikyo')


class ES006(ESAPIView):
    '''
        Expense System -> ES006 - Cash Advancement
    '''

    SESSION_KEY_FILE_ID = 'displayFileID'
    SESSION_KEY_CASH_ADVANCEMENT_ID = 'currentCashAdvID'
    NEW_CASH_ADVANCEMENT_ID = -1

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            userRc = self.getCurrentUser()
            isNew = self.__isNewCashAdvancement()
            curCashAdvId = self.__getCurrentCashAdvancementID()
            isMainScreen = isNullBlank(curCashAdvId) and not isNew
            isDetailScreen = not isMainScreen

            screen.setFieldGroupsVisible(('schFg', 'lineFg', 'toolbar1', 'listFg'), isMainScreen)
            screen.setFieldGroupsVisible(('pdfViewer', 'dtlFg', 'uploadFg', 'priorBalanceExpenseFg', 'toolbar2', "activityFg"), isDetailScreen)
            if isNew or not screen.getFieldGroup('pdfViewer').visible:
                screen.layoutParams = ""

            if isDetailScreen:
                caRc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=curCashAdvId).first() if not isNew else None
                submittable = isNew or caRc.claimer.id == userRc.id and (caRc.sts == Status.CANCELLED.value or caRc.sts == Status.REJECTED.value)
                cancelable = not isNew and acl.is_cancelable(caRc.sts, caRc.claimer, userRc) if caRc is not None else False
                approveable = not isNew and acl.is_approverable(userRc, caRc.sts, caRc.payee, caRc.claim_amt, caRc.approver) if caRc is not None else False
                rejectable = not isNew and acl.is_rejectable(userRc, caRc.sts, caRc.payee, caRc.claim_amt, caRc.approver) if caRc is not None else False
                settle_able = not isNew and acl.is_settlable(userRc, caRc.sts, caRc.payee, caRc.claim_amt, caRc.approver) if caRc is not None else False
                revertSettledPayment = not isNew and acl.can_revert_settled_payment(userRc, caRc.sts, caRc.office) if caRc is not None else False
                hasPaymentRecordFile = not isNew and caRc.payment_record_file is not None if caRc is not None else False

                # update the field's display setting: visible, editable
                screen.setFieldsEditable('dtlFg', 'payeeIDField', submittable)
                screen.setFieldsEditable('dtlFg', 'approverField', submittable)
                screen.setFieldsEditable('dtlFg', 'dscField', submittable)
                screen.setFieldsEditable('dtlFg', 'detailPoNoField', submittable)
                screen.setFieldsEditable('dtlFg', 'amountField', submittable)

                screen.setFieldsEditable('dtlFg', 'trnTypeField', settle_able)
                # screen.setFieldsVisible('dtlFg', 'trnTypeField', settle_able)
                screen.setFieldsEditable('dtlFg', 'trnNoField', settle_able)
                # screen.setFieldsVisible('dtlFg', 'trnNoField', settle_able)

                screen.setFieldsEditable('dtlFg', 'cancelRejectReasonField', cancelable or rejectable)
                screen.setFieldsVisible('dtlFg', 'cancelRejectReasonField', cancelable or rejectable or (caRc is not None and caRc.sts in [
                                        Status.CANCELLED.value, Status.REJECTED.value]))

                screen.setFieldsEditable('dtlFg', 'revertSettledPaymentReasonField', revertSettledPayment)
                screen.setFieldsVisible('dtlFg', 'revertSettledPaymentReasonField', revertSettledPayment)

                # update button's display setting: visible
                screen.setFieldsVisible('toolbar2', 'bttSubmit', submittable)
                # only allow claimer to cancel the request
                screen.setFieldsVisible('toolbar2', 'bttCancel', cancelable)
                screen.setFieldsVisible('toolbar2', 'bttApprove', approveable)
                screen.setFieldsVisible('toolbar2', 'bttReject', rejectable)
                screen.setFieldsVisible('toolbar2', 'bttDownloadPaymentRecord', hasPaymentRecordFile)
                screen.setFieldsVisible('toolbar2', 'bttDisplayPaymentRecord', hasPaymentRecordFile)
                screen.setFieldsVisible('toolbar2', 'bttSettle', settle_able)
                screen.setFieldsVisible('toolbar2', 'bttRevertSettledPayment', revertSettledPayment)

                screen.setFieldGroupsVisible(('uploadFg'), settle_able)
                screen.setFieldGroupsVisible(('priorBalanceExpenseFg'), caRc is not None and caRc.sts == Status.SETTLED.value)
        self.beforeDisplayAdapter = beforeDisplayAdapter

    # Search Fg
    def getSts(self):
        """Search field: Status"""
        return status.get_all_status()

    def getPaymentMethodRcs(self):
        return PaymentMethod.objects.exclude(tp__in=[PaymentMethod.PETTY_CASH, PaymentMethod.PRIOR_BALANCE])

    # override
    def getOfficeRcs(self):
        offices = super().getOfficeRcs()
        ca_rc = self.__getCurrentCashAdvancementRc()
        if ca_rc:
            ca_office_id = ca_rc.office.id
            if not any(office['id'] == ca_office_id for office in offices):
                offices.append({'id': ca_rc.office.id, 'name': ca_rc.office.name})
                offices.sort(key=lambda x: x['name'])
        return offices

    def getPayeeRcs(self):
        if self.__isNewCashAdvancement():
            return Payee.objects.filter(office=self._getCurrentOffice()).order_by('payee').values('id', 'payee')
        return Payee.objects.all().order_by('payee').values('id', 'payee')

    def getApproverRcs(self):
        """Approver combobox data"""
        ca_rc = self.__getCurrentCashAdvancementRc()
        office_rc = ca_rc.office if ca_rc is not None else self._getCurrentOffice()
        claimer_rc = ca_rc.claimer if ca_rc is not None else self.getCurrentUser()
        return [{'id': r.id, 'approver': r.usr_nm} for r in get_office_first_approvers(office_rc, claimer_rc)]

    def getCashAdvRcs(self):
        """Get the table data"""
        query_params = {}
        search_data = self.getSearchData(fieldGroupName='schFg')
        if isNotNullBlank(search_data):
            query_params['sn'] = search_data.get('schSNField', None)
            query_params['status'] = search_data.get('schStsField', None)
            query_params['claimer'] = search_data.get('schClaimerField', None)
            query_params['payee'] = search_data.get('schPayeeField', None)
            query_params['payment_record_filename'] = search_data.get('schPaymentRecordField', None)
            query_params['claim_date_from'] = search_data.get('schClaimDateFromField', None)
            query_params['claim_date_to'] = search_data.get('schClaimDateToField', None)
            query_params['approve_date_from'] = search_data.get('schApprovedDateFromField', None)
            query_params['approve_date_to'] = search_data.get('schApprovedDateToField', None)
            query_params['settle_date_from'] = search_data.get('schSettleDateFromField', None)
            query_params['settle_date_to'] = search_data.get('schSettleDateToField', None)
            query_params['description'] = search_data.get('schExpenseDscField', None)

        queryset = CashAdvancement.objects
        queryset = CA.query_cash_advancements(self.getCurrentUser(), self._getCurrentOffice(), queryset, query_params)
        queryset = queryset.order_by('-claim_dt')

        def format_res_func(results):
            for r in results:
                cash_rc = CashAdvancement.objects.filter(id=r['id']).first()
                normal_expenses, petty_expenses, fx_expenses, usages, _fxUsages = CA.getCashAdvancementUsage(cash_rc)
                normal_expense_summary = ''
                seq = 0
                for pbRc in normal_expenses:
                    seq += 1
                    if seq > 1:
                        normal_expense_summary += '\n'
                    normal_expense_summary += '%s. %s - %s' % (seq, pbRc.expense.sn, pbRc.balance_amt)

                petty_expense_summary = ''
                seq = 0
                for pbRc in petty_expenses:
                    seq += 1
                    if seq > 1:
                        petty_expense_summary += '\n'
                    petty_expense_summary += '%s. %s - %s' % (seq, pbRc.expense.sn, pbRc.balance_amt)

                fx_expense_summary = ''
                seq = 0
                for pbRc in fx_expenses:
                    seq += 1
                    if seq > 1:
                        fx_expense_summary += '\n'
                    fx_expense_summary += '%s. %s - %s (%s)' % (seq, pbRc.expense.sn, pbRc.fx_balance_amt, pbRc.fx.fx_ccy.code)

                queryUsage = ''
                seq = 0
                left_flag = False
                for (ccy_rc, _isFx, total, _used, left) in usages:
                    if int(left) > 0:
                        left_flag = True
                    seq += 1
                    if seq > 1:
                        queryUsage += '\n'
                    queryUsage += '%s. %s:  %s / %s' % (seq, ccy_rc.code, left, total)

                r['query_expenses'] = normal_expense_summary
                r['query_petty_expenses'] = petty_expense_summary
                r['query_fx_expenses'] = fx_expense_summary
                r['query_usage'] = queryUsage
                r['left_flag'] = left_flag
            return results

        def get_style_func(results) -> list:
            table_styles = []
            for r in results:
                table_styles.append({"row": r['id'], "class": "row_" + r['sts']})
                if r['left_flag']:
                    table_styles.append({"row": r['id'], "col": "listFg_query_usage", "class": "cell_left_ccy " + "row_" + r['sts']})
            return table_styles
        return self.getPagingResponse(table_name="listFg", table_data=queryset, format_res_func=format_res_func, get_style_func=get_style_func)

    def openCashAdvDetail(self):
        """Click open detail icon in the table's last column."""
        cashAdvId = self._getEditIndexField()
        # TODO: permission check
        self.setSessionParameter(self.SESSION_KEY_CASH_ADVANCEMENT_ID, cashAdvId)
        ca_rc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cashAdvId).first()
        if ca_rc is None:
            return Boolean2.FALSE("System error. Cash advancement ID doesn't exist.")
        default_display_file_id = ca_rc.payment_record_file.id if ca_rc.payment_record_file is not None else None
        self.setSessionParameter(self.SESSION_KEY_FILE_ID, default_display_file_id)
        self._deletePreviousScreenRequestData()

    def new(self):
        """Click [Create Cash Advancement] button to create a new record"""
        self.setSessionParameter(self.SESSION_KEY_CASH_ADVANCEMENT_ID, self.NEW_CASH_ADVANCEMENT_ID)
        self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)

    def getDtlRc(self):
        """ Get cash advancement data.
        """
        cash_id = self.__getCurrentCashAdvancementID()
        cash_rc = None
        if cash_id is not None:
            cash_rc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_id).first()
            if cash_rc is None:
                logger.error("Cash advancement doesn't exist. ID=%s" % cash_id)
                self.deleteSessionParameters(self.SESSION_KEY_CASH_ADVANCEMENT_ID)
                raise IkValidateException("Cash advancement doesn't exist.")
            # TODO: validate permission
            # cash_rc.payment_tp = cash_rc.pay.id
            # cash_rc.payment_number = cash_rc.pay.payment_number

            # display default file
            if isNullBlank(self.getSessionParameterInt(self.SESSION_KEY_FILE_ID)) and cash_rc.payment_record_file is not None:
                self.setSessionParameter(self.SESSION_KEY_FILE_ID, cash_rc.payment_record_file.id)
            cash_rc.po_sn = cash_rc.po.sn if isNotNullBlank(cash_rc.po) else None
        elif self.__isNewCashAdvancement():
            cash_rc = CashAdvancement()
            cash_rc.office = self._getCurrentOffice()
            cash_rc.claimer = self.getCurrentUser()
            cash_rc.ccy = cash_rc.office.ccy
            cash_rc.sts = Status.DRAFT.value
            cash_rc.claim_dt = datetime.now()
            # TODO:
            # if isNotNullBlank(payeeID):
            #     priorBalance = ES.getCashAdvancedPriorBalance(payeeID, currentTime)
            #     data.ccy = payeeOfficeCCY
            #     data.deduction_amt = priorBalance
            # message = None
        return cash_rc

    def getPdfViewer(self):
        """Get current file."""
        displayFileID = self.getSessionParameter(self.SESSION_KEY_FILE_ID)
        if isNotNullBlank(displayFileID):
            ef = ESFile.getESFile(displayFileID)
            if isNotNullBlank(ef):
                if os.path.isfile(ef.file):
                    return responseFile(filePath=ef.file, filename=ef.filename)
            filePath = ESFileManager.get_not_exist_file_template()
            return responseFile(filePath)
        return IkSccJsonResponse()

    def getPriorBalanceRcs(self):
        if self.__isNewCashAdvancement():
            return None
        cash_id = self.__getCurrentCashAdvancementID()
        if cash_id is None:
            return None
        caRc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_id).first()
        if caRc is None:
            return None
        rcs = PriorBalance.objects.filter(ca=caRc).exclude(expense__sts__in=(Status.DRAFT.value,
                                                                             Status.CANCELLED.value, Status.REJECTED.value)).order_by('expense__id')
        rcs = [r for r in rcs]
        for r in rcs:
            if r.expense.is_petty_expense:
                r.is_petty_expense = 'Yes'
            else:
                r.is_petty_expense = 'No'
        return rcs

    def getExchangeCCYRcs(self):
        cash_rc = self.__getCurrentCashAdvancementRc()
        if cash_rc is None:
            return None
        return Currency.objects.exclude(id=cash_rc.payee.office.ccy.id).order_by('seq', 'code').values('id', 'code')

    def back(self):
        """Click the [Back] button to show the list table."""
        # get po id if have
        cash_rc = self.__getCurrentCashAdvancementRc()
        po_id = cash_rc.po_id if isNotNullBlank(cash_rc) and isNotNullBlank(cash_rc.po) else None
        self.deleteSessionParameters([self.SESSION_KEY_CASH_ADVANCEMENT_ID, self.SESSION_KEY_FILE_ID])
        pre_screen_nm = self._getPreviousScreenName()
        if isNotNullBlank(pre_screen_nm):
            params = {'id': po_id, 'es_id': cash_rc.id} if pre_screen_nm == const.MENU_PO001 else None
            return self._openScreen(menuName=pre_screen_nm, parameters=params)

    def submit(self):
        """ Click the [Submit] button to submit the cash advancement.
        """
        cash_adv_rc = self._getRequestValue('dtlFg')
        is_new = self.__isNewCashAdvancement()

        cash_adv_id = None if is_new else cash_adv_rc.id
        ccy_rc = cash_adv_rc.ccy
        office_rc = cash_adv_rc.office
        payee_rc = cash_adv_rc.payee
        desc = cash_adv_rc.dsc
        po_sn = cash_adv_rc.po_sn
        claim_amt = cash_adv_rc.claim_amt
        approver_rc = cash_adv_rc.approver
        if self._getCurrentOfficeID() != office_rc.id:
            raise IkValidateException("The office [%s] is not the same as the current office [%s]. Please check." % (office_rc.name, self._getCurrentOffice().name))
        result = CA.submit_cash_advancement(self.getCurrentUserId(), cash_adv_id, office_rc, ccy_rc, payee_rc, desc, claim_amt, po_sn, approver_rc)
        if not result.value:
            return result
        cash_adv_id = result.data
        caRc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_adv_id).first()
        self.setSessionParameter(self.SESSION_KEY_CASH_ADVANCEMENT_ID, cash_adv_id)
        return IkSccJsonResponse(message="Cash advancement [%s] submitted." % caRc.sn)

    def cancel(self):
        """Click the [Cancel] button to cancel the cash advancement."""
        requestData = self.getRequestData()
        caRc = requestData.get('dtlFg')
        caRc: CashAdvancement
        return CA.cancel_cash_advancement(self.getCurrentUserId(), caRc.id, caRc.action_rmk)

    def reject(self):
        """Click the [Reject] button to cancel the cash advancement."""
        requestData = self.getRequestData()
        caRc = requestData.get('dtlFg')
        caRc: CashAdvancement
        return CA.reject_cash_advancement(self.getCurrentUserId(), caRc.id, caRc.action_rmk)

    def approve(self):
        requestData = self.getRequestData()
        caRc = requestData.get('dtlFg')
        caRc: CashAdvancement
        return CA.approve_cash_advancement(self.getCurrentUserId(), caRc.id)

    def downloadPaymentRecordFile(self):
        """Click the [Download Payment Record] button to download the uploaded payment record file."""
        cash_id = self.__getCurrentCashAdvancementID()
        if isNullBlank(cash_id):
            return Boolean2.FALSE("Please select a cash advancement first.")
        caRc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_id).first()
        if caRc is None:
            return Boolean2.FALSE("Please select a cash advancement first.")
        if caRc.payment_record_file is None:
            return Boolean2.FALSE("Payment record file doesn't exist. Please upload first.")
        f = ESFileManager.getESFile(caRc.payment_record_file)
        if f is None:
            return Boolean2.FALSE("Please upload the payment record first.")
        return self.downloadFile(f.file, "%s-CA-PR-%s" % (caRc.office.code, Path(f.file).name))

    def displayPaymentRecordFile(self):
        """Click the [Display Payment Record] button to display the uploaded payment record file."""
        # permission check
        self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        cash_id = self.__getCurrentCashAdvancementID()
        if isNotNullBlank(cash_id):
            caRc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_id).first()
            if caRc is None:
                return Boolean2.FALSE("Please select a cash advancement first.")
            if caRc.payment_record_file is not None:
                self.setSessionParameters({self.SESSION_KEY_FILE_ID: caRc.payment_record_file.id})

    def settle(self):
        """Click the [Settle] button to pay the current cash advancement."""
        uploadPageFile = None
        isSuccess = False
        try:
            cash_adv_id = self.__getCurrentCashAdvancementID()
            if isNullBlank(cash_adv_id):
                return Boolean2.FALSE("Please select an approved cash advancement first.")
            caRc = acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_adv_id).first()
            if caRc is None:
                logger.error("Cash Advancement doesn't exist.")
                return Boolean2.FALSE("Cash advancement doesn't exist.")

            requestData = self.getRequestData()
            caRc = requestData.get('dtlFg')
            caRc: CashAdvancement

            paymentType = caRc.payment_tp
            if paymentType is None:
                return Boolean2.FALSE("Please select a Transaction Type.")
            paymentNo = caRc.payment_number
            if isNullBlank(paymentNo):
                return Boolean2.FALSE("Please fill in the Transfer No. first.")
            paymentNo = str(paymentNo).strip()
            paymentRemarks = caRc.action_rmk  # TODO: add payment remarks to screen

            uploadFiles = self.getRequestData().getFiles('uploadFile')
            if uploadFiles is None or len(uploadFiles) == 0 or uploadFiles[0] is None:
                return IkErrJsonResponse(message="Please select a file to upload.")
            uploadPageFile = ESFileManager.save_uploaded_really_file(uploadFiles[0], self.__class__.__name__, self.getCurrentUserName())
            result = CA.settle_cash_advancement(self.getCurrentUserId(), caRc.id, paymentType, paymentNo, uploadPageFile, paymentRemarks)
            isSuccess = result.value
            if isSuccess:
                if caRc.payment_record_file is not None:
                    self.setSessionParameter(self.SESSION_KEY_FILE_ID, caRc.payment_record_file.id)
            return result
        finally:
            if not isSuccess and uploadPageFile is not None:
                ESFileManager.delete_really_file(uploadPageFile)

    def revertSettledPayment(self):
        """Click the [Revert Settled Payment] button to revert the current settled cash advancement."""
        request_data = self.getRequestData()
        ca_rc = request_data.get('dtlFg')
        ca_rc: CashAdvancement
        result = CA.revert_settled_cash_advancement(self.getCurrentUserId(), ca_rc.id, ca_rc.action_rmk)
        if result.value:
            self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        return result

    def getActivityRcs(self):
        data = None
        cash_adv_id = self.__getCurrentCashAdvancementID()
        if isNotNullBlank(cash_adv_id):
            data = Activity.objects.filter(transaction_id=cash_adv_id, tp=activity.ActivityType.CASH_ADVANCEMENT.value).order_by("operate_dt")
        return IkSccJsonResponse(data=data)

    def __isNewCashAdvancement(self) -> bool:
        id = self.getSessionParameter(self.SESSION_KEY_CASH_ADVANCEMENT_ID)
        return id == self.NEW_CASH_ADVANCEMENT_ID

    def __getCurrentCashAdvancementID(self) -> int:
        id = self.getSessionParameterInt(self.SESSION_KEY_CASH_ADVANCEMENT_ID)
        pre_screen_nm = self._getPreviousScreenName()
        if isNullBlank(id) and isNotNullBlank(pre_screen_nm) and pre_screen_nm != self._menuName:
            request_data = self._getPreviousScreenRequestData()
            id = request_data.pop("id", None) if request_data is not None else None
            self.setSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, value=request_data, isGlobal=True)
            self.setSessionParameter(self.SESSION_KEY_CASH_ADVANCEMENT_ID, id)
        return int(id) if id is not None and id != self.NEW_CASH_ADVANCEMENT_ID else None

    def __getCurrentCashAdvancementRc(self) -> CashAdvancement:
        cash_id = self.__getCurrentCashAdvancementID()
        if isNullBlank(cash_id):
            return None
        return acl.add_query_filter(CashAdvancement.objects, self.getCurrentUser()).filter(id=cash_id).first()
