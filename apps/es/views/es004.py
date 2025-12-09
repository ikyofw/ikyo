import logging
import os

from django.db.models import Case, Exists, F, OuterRef, Sum, When

import core.ui.ui as ikui
from core.core.exception import IkValidateException
from core.core.http import IkErrJsonResponse, IkSccJsonResponse, responseFile
from core.utils.lang_utils import isNotNullBlank, isNullBlank

from ..core import acl, ca, const, es
from ..core import es_file as ESFileManager
from ..core import es_tools
from ..core.approver import get_office_first_approvers
from ..core.finance import round_currency
from ..core.office import get_office_by_id
from ..core.status import Status
from ..models import *
from .es_base import ESAPIView

logger = logging.getLogger('ikyo')


class ES004(ESAPIView):
    '''
        Expense System - New Expense Details
    '''

    SESSION_KEY_EXPENSE_HDR_ID = 'current_expense_hdr_id'
    SESSION_KEY_EXPENSE_ID = 'current_expense_id'
    SESSION_KEY_FILE_ID = 'uploaded_file_id'
    SESSION_KEY_PB_DATA = 'priori_balance_input_data'
    SESSION_KEY_PAYMENT_DATA = 'payment_input_data'

    def __init__(self) -> None:
        super().__init__()
        self._addStaticResource(self.get_last_static_revision_file('es004.css', 'es/css'))

        def beforeDisplayAdapter(screen: ikui.Screen):
            hdrRc = self.__getExpenseHdrRc()
            hasSupportingDoc = hdrRc is not None and hdrRc.supporting_doc is not None

            settleByPriorBalance = False
            paymentData = self.getSessionParameter(self.SESSION_KEY_PAYMENT_DATA)
            if paymentData is not None:
                settleByPriorBalance = (paymentData.get('settleByPriorBalance', None) == 'Y')
            else:
                settleByPriorBalance = hdrRc and hdrRc.use_prior_balance == True
            screen.setFieldsVisible('paymentFg', 'sn', isNotNullBlank(hdrRc) and hdrRc.sts != Status.DRAFT.value)
            screen.setFieldsEditable('paymentFg', 'settleByPettyCash', not settleByPriorBalance)
            screen.setFieldsEditable('paymentFg', 'settleByPriorBalanceCCY', settleByPriorBalance)
            screen.setFieldGroupsEnable('availablePriorBalanceFg', isEditable=settleByPriorBalance)

            screen.setFieldsVisible('submitBar', ['bttDisplaySD', 'bttDownloadSD', 'bttDeleteSD'], hasSupportingDoc)
        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getPdfViewer(self):
        fileID = self.getSessionParameter(self.SESSION_KEY_FILE_ID)
        if isNullBlank(fileID) or str(fileID) == '-1':
            filePath = ESFileManager.get_blank_page_file_template()
        else:
            fileRc = File.objects.filter(id=fileID).first()
            if isNullBlank(fileRc):
                filePath = ESFileManager.get_blank_page_file_template()
            else:
                filename = '%s.%s' % (fileRc.seq, fileRc.file_tp.lower())
                filePath = ESFileManager.getUploadFileAbsolutePath(fileRc.file_path, filename)
                if not os.path.isfile(filePath):
                    filePath = ESFileManager.get_not_exist_file_template()
        if isNotNullBlank(fileID) and str(fileID) != '-1':
            expense_id = self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID)
            if expense_id is not None:
                validateResult = es.checkExpenseFileAccessPermission(expense_id, fileID, self.getCurrentUser(), self._getCurrentOfficeID(), validateClaimerOnly=True)
                if not validateResult.value:
                    return IkErrJsonResponse(message=validateResult.data)
        return responseFile(filePath)

    def __getExpenseHdrRc(self) -> Expense:
        expenseHdrRc: Expense = None
        currentExpenseHdrID = None
        isFromOtherScreen = False
        pre_screen_nm = self._getPreviousScreenName()
        if isNotNullBlank(pre_screen_nm):
            isFromOtherScreen = True
            request_data = self._getPreviousScreenRequestData()
            currentExpenseHdrID = request_data.pop("id", None) if request_data is not None else None
        if isNullBlank(currentExpenseHdrID):
            currentExpenseHdrID = self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID)
        if currentExpenseHdrID is None:
            expenseHdrRc = es.get_last_draft_expense(self.getCurrentUser(), self._getCurrentOffice())
            currentExpenseHdrID = expenseHdrRc.id if expenseHdrRc else None
        else:
            expenseHdrRc = acl.add_query_filter(Expense.objects, self.getCurrentUser()).filter(id=currentExpenseHdrID).first()
            if expenseHdrRc is None:
                self.deleteSessionParameters([self.SESSION_KEY_EXPENSE_ID, self.SESSION_KEY_EXPENSE_HDR_ID])
                logger.error('Expense [%s] is not exists.' % currentExpenseHdrID)
                raise IkValidateException(message="Expense doesn't exists.")
            elif expenseHdrRc.claimer.id != self.getCurrentUserId():
                self.deleteSessionParameters([self.SESSION_KEY_EXPENSE_ID, self.SESSION_KEY_EXPENSE_HDR_ID])
                logger.error("Permission deny. User [%s] doesn't have permission to access to expense [%s] (created by [%s])."
                             % (self.getCurrentUserName(), expenseHdrRc.sn, expenseHdrRc.claimer.usr_nm))
                raise IkValidateException('Permission deny.')
        if isFromOtherScreen and expenseHdrRc is not None:
            self._setCurrentOffice(expenseHdrRc.office.id)
        self.setSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID, currentExpenseHdrID)
        return expenseHdrRc

    def getPageSeqRcs(self):
        return self.__getUploadedPages()

    def getFileRcs(self):
        """Data for [Page] table."""
        fileRcs = self.__getUploadedPages()
        currentFileID = self.getSessionParameter(self.SESSION_KEY_FILE_ID)
        if currentFileID is not None:
            for fileRc in fileRcs:
                if fileRc.id == currentFileID:
                    fileRc.ik_set_cursor(True)
                    break
        for fileRc in fileRcs:
            fileRc.amount = ExpenseDetail.objects.filter(file=fileRc).aggregate(total=Sum(Case(
                When(ex_rate__isnull=False, ex_rate__gt=0, then=F('amt') * F('ex_rate')),
                default=F('amt')
            )))['total']
        tableRowStyles = self._getFileStyle(fileRcs, currentFileID)
        return self.getSccJsonResponse(data=fileRcs, cssStyle=tableRowStyles)

    def __getUploadedPages(self) -> list[File]:
        """Data for [Pages] table."""
        fileRcs = []
        expenseHdrRc = self.__getExpenseHdrRc()
        currentExpenseHdrID = expenseHdrRc.id if expenseHdrRc else None
        fileIDs = []
        if currentExpenseHdrID is not None:
            fileIDs = ExpenseDetail.objects.filter(hdr=expenseHdrRc, file_id__isnull=False).values_list('file_id', flat=True).distinct()
            fileRcs = list(File.objects.filter(id__in=fileIDs).order_by('seq'))
        # add draft files which doesn't exists in other expenses
        subquery = ExpenseDetail.objects
        if expenseHdrRc is not None:
            subquery = subquery.exclude(hdr=expenseHdrRc)
        subquery = subquery.filter(file__id=OuterRef('file_id')).values('file_id')
        draftFileRcs = list(DraftFile.objects.filter(tp=DraftFile.EXPENSE, claimer=self.getCurrentUser(), office_id=self._getCurrentOfficeID())
                            .exclude(file__id__in=fileIDs).exclude(Exists(subquery)).order_by('id'))
        fileRcs.extend([r.file for r in draftFileRcs])
        fileRcs.sort(key=lambda x: x.seq)
        return fileRcs

    def getPayeeRcs(self):
        payee_rcs = Payee.objects.filter(office=self._getCurrentOffice()).order_by('payee')
        if len(payee_rcs) == 0:
            self._addWarnMessage("Please ask administrator to add payee.")
        return payee_rcs

    def getApproverRcs(self):
        expense_rc = self.__getExpenseHdrRc()
        office_rc = expense_rc.office if expense_rc is not None else self._getCurrentOffice()
        claimer_rc = expense_rc.claimer if expense_rc is not None else self.getCurrentUser()
        approver_rcs = get_office_first_approvers(office_rc, claimer_rc)
        if len(approver_rcs) == 0:
            self._addWarnMessage("Please ask administrator to add approver.")
        return [{'id': r.id, 'approver': r.usr_nm} for r in approver_rcs]

    def getHtmlCurrentExpenseNotes(self):
        officeID = self._getCurrentOfficeID()
        officeRc = get_office_by_id(officeID)
        expenseHdrRc = self.__getExpenseHdrRc()
        officeRc = get_office_by_id(self._getCurrentOfficeID())
        if officeRc is None:
            return IkErrJsonResponse(message="Please ask administrator to add your office first.")

        pageTitle = "<div id='pageTitleDiv'>"
        if expenseHdrRc is None or expenseHdrRc.sts == Status.DRAFT.value:
            pageTitle += "%s office new expense." % officeRc.name
        elif expenseHdrRc is not None:
            pageTitle += "%s office. Edit the %s expense %s." % (officeRc.name, expenseHdrRc.sts, expenseHdrRc.sn)
        pageTitle += "</div>"
        return IkSccJsonResponse(data=pageTitle)

    def getCategory(self):
        return ExpenseCategory.objects.values('id', 'cat').distinct().order_by('cat')

    def getCcy(self):
        return Currency.objects.filter().values('id', 'code').distinct().order_by('code')

    def getExpenseRcs(self):
        office_rc = self._getCurrentOffice()
        claimer_rc = self.getCurrentUser()
        expense_dtl_id = self.getSessionParameterInt(self.SESSION_KEY_EXPENSE_ID)
        hdrRc = self.__getExpenseHdrRc()
        payeeOfficeCCY = hdrRc.office.ccy if hdrRc is not None else self._getCurrentOffice().ccy
        inputAmount, inputMessage = self.__getTotalAmount(claimer_rc, hdrRc.id if hdrRc is not None else None, payeeOfficeCCY, office_rc)
        if isNotNullBlank(inputMessage):
            self._addInfoMessage(inputMessage)
        expenseRcs = ExpenseDetail.objects.filter(hdr=hdrRc).order_by('file__seq', 'incur_dt', 'cat__cat', 'seq') if hdrRc is not None else []
        currentFileID = None
        if len(expenseRcs) > 0 and isNullBlank(expense_dtl_id) and isNullBlank(self.getSessionParameter(self.SESSION_KEY_FILE_ID)):
            expense_dtl_id = expenseRcs[0].id
            self.setSessionParameter(self.SESSION_KEY_EXPENSE_ID, expense_dtl_id)

        for expenseRc in expenseRcs:
            if expenseRc.id == expense_dtl_id:
                expenseRc.ik_set_cursor()
                currentFileID = expenseRc.file.id if expenseRc.file is not None else None
                self.setSessionParameter(self.SESSION_KEY_FILE_ID, currentFileID)
        if isNotNullBlank(currentFileID):
            for expenseRc in expenseRcs:
                if expenseRc.file is not None and expenseRc.file.id == currentFileID:
                    expenseRc.ik_set_cursor()
        tableRowStyles = self._getExpenseStyle(expenseRcs, expense_dtl_id, currentFileID)
        return self.getSccJsonResponse(data=expenseRcs, cssStyle=tableRowStyles)

    def uploadPage(self):  # checked ok 2024-04-25
        """Upload files in expense table"""
        expenseID = self.getRequestData().get('id', None)
        return self.__uploadPages(int(expenseID))

    def uploadPages(self):
        return self.__uploadPages()

    def __uploadPages(self, expense_dtl_id: int = None):  # checked ok 2024-04-25
        """Click "Upload Page" button to upload expense page file.
        """
        uploadFiles = self.getRequestData().getFiles('uploadField')
        if uploadFiles is None or len(uploadFiles) == 0 or uploadFiles[0] is None:
            return IkErrJsonResponse(message="Please select a file to upload.")
        office_rc = self._getCurrentOffice()
        claimer_rc = self.getCurrentUser()
        expense_id = self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID)
        uploadPageFile = None
        try:
            uploadPageFile = ESFileManager.save_uploaded_really_file(uploadFiles[0], self.__class__.__name__, self.getCurrentUserName())
            fileID, fileSeq = es.upload_expense_file(claimer_rc, office_rc, uploadPageFile, False, expense_id, expense_dtl_id, None)
            uploadMessage = "If the invoice has a hard copy, please write the sequence number %s "\
                "on the top right corner of the page and give it to the accounts department!" % fileSeq
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, fileID)
            self.setSessionParameter(self.SESSION_KEY_EXPENSE_ID, expense_dtl_id)
            return IkSccJsonResponse(message=uploadMessage)
        finally:
            ESFileManager.delete_really_file(uploadPageFile)

    def downloadUploadedFile(self):
        fileID = self._getRequestValue('id')
        if isNullBlank(fileID):
            return IkErrJsonResponse(message='Please select a file to download.')
        expenseHdrRc = self.__getExpenseHdrRc()
        if expenseHdrRc is None:
            return IkErrJsonResponse(message="Expense doesn't exist.")
        validateResult = es.checkExpenseFileAccessPermission(expenseHdrRc.id, fileID, self.getCurrentUser(), self._getCurrentOfficeID(), validateClaimerOnly=True)
        if not validateResult.value:
            return IkErrJsonResponse(message=validateResult.data)
        f = ESFileManager.getESFile(int(fileID))
        return self.downloadFile(f.file)  # use file sequence instead

    def deleteUploadedFile(self):
        fileID = self._getRequestValue('id')
        if isNullBlank(fileID):
            return IkErrJsonResponse(message='Please select a file to delete.')
        fileID = int(fileID)
        result = es.delete_uploaded_expense_file(self.getCurrentUser(), self._getCurrentOffice(), fileID, self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID))
        if result.value:
            if self.getSessionParameterInt(self.SESSION_KEY_FILE_ID) == fileID:
                self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        return result

    def replaceUploadedFile(self):
        originalFileID = self._getRequestValue('id')
        if isNullBlank(originalFileID):
            return IkErrJsonResponse(message='Please select a file to replace.')
        uploadFiles = self.getRequestData().getFiles('uploadField')
        if uploadFiles is None or len(uploadFiles) == 0 or uploadFiles[0] is None:
            return IkErrJsonResponse(message="Please select a file to upload.")
        office_rc = self._getCurrentOffice()
        claimer_rc = self.getCurrentUser()
        expense_id = self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID)
        uploadPageFile = None
        try:
            uploadPageFile = ESFileManager.save_uploaded_really_file(uploadFiles[0], self.__class__.__name__, self.getCurrentUserName())
            fileID, fileSeq = es.upload_expense_file(claimer_rc, office_rc, uploadPageFile, False, expense_id, None, originalFileID)
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, fileID)
            uploadMessage = "If the invoice has a hard copy, please write the sequence number %s "\
                "on the top right corner of the page and give it to the accounts department!" % fileSeq
            return IkSccJsonResponse(message=uploadMessage)
        finally:
            ESFileManager.delete_really_file(uploadPageFile)

    def displayUploadedFile(self):  # click Pages table to display uploaded file
        fileID = self._getTableSelectedValue()
        self.setSessionParameter(self.SESSION_KEY_FILE_ID, fileID)
        dtl_rc = ExpenseDetail.objects.filter(file_id=fileID).first()
        self.setSessionParameter(self.SESSION_KEY_EXPENSE_ID, dtl_rc.id if isNotNullBlank(dtl_rc) else None)

    def displayUploadedFile2(self):  # click expense table to display uploaded file
        expenseID = self._getTableSelectedValue()
        self.__displayUploadedFile2(int(expenseID))

    def __displayUploadedFile2(self, expenseID: int) -> bool:  # click expense table to display uploaded file
        if expenseID is not None:
            first_expense_dtl_rc = ExpenseDetail.objects.filter(id=expenseID).first()
            first_expense_file_id = None
            if first_expense_dtl_rc is not None and first_expense_dtl_rc.file is not None:
                first_expense_file_id = first_expense_dtl_rc.file.id
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, first_expense_file_id)
            self.setSessionParameter(self.SESSION_KEY_EXPENSE_ID, expenseID)
        return True

    def saveExpense(self):
        """Click "Save" button to save the expense table."""
        expense_rc = self.__getExpenseHdrRc()
        expense_detail_rcs = self.getRequestData().get('expenseFg')
        result = es.save_expense_details(self.getCurrentUser(), self._getCurrentOffice(), expense_rc, expense_detail_rcs)
        if result.value:
            self.deleteSessionParameters(self.SESSION_KEY_EXPENSE_ID, self.SESSION_KEY_FILE_ID)
        return result.toIkJsonResponse1()

    def getPaymentRc(self):
        """Payment field group data.
        """
        sn = None
        sts = None
        poNo = None
        payeeID = None
        approverID = None
        settleByPriorBalance = None  # Y/N
        settleByPettyCash = None
        settleByPriorBalanceCCY = None  # currency id
        expenseDsc = None
        supportingDoc = None

        paymentData = self.getSessionParameter(self.SESSION_KEY_PAYMENT_DATA)
        if paymentData is not None:
            sn = paymentData.get('sn', None)
            sts = paymentData.get('sts', None)
            poNo = paymentData.get('poNo', None)
            payeeID = paymentData.get('payeeID', None)
            approverID = paymentData.get('approverID', None)
            settleByPriorBalance = paymentData.get('settleByPriorBalance', None)
            settleByPettyCash = paymentData.get('settleByPettyCash', None) == 'true'
            settleByPriorBalanceCCY = paymentData.get('settleByPriorBalanceCCY', None)
            expenseDsc = paymentData.get('expenseDsc', None)
            supportingDoc = paymentData.get('supportingDoc', None)
        else:
            hdrRc = self.__getExpenseHdrRc()
            if hdrRc is not None:
                sn = hdrRc.sn
                sts = hdrRc.sts
                poNo = hdrRc.po.sn if isNotNullBlank(hdrRc.po) else None
                payeeID = hdrRc.payee.id if hdrRc.payee is not None else None
                approverID = hdrRc.approver.id if hdrRc.approver is not None else None
                settleByPriorBalance = 'Y' if hdrRc.use_prior_balance is True else None
                settleByPettyCash = hdrRc.is_petty_expense
                settleByPriorBalanceCCY = hdrRc.fx_ccy.id if hdrRc.fx_ccy is not None else (hdrRc.office.ccy.id if hdrRc.office is not None else None)
                expenseDsc = hdrRc.dsc
                supportingDoc = es.getExpenseSupportingDocumentFilename(hdrRc.supporting_doc) if hdrRc.supporting_doc is not None else None

        officeRc = self._getCurrentOffice()
        if isNullBlank(payeeID) or isNullBlank(approverID):
            # use default or last data
            claimerRc = self.getCurrentUser()
            lastExpenseHdr = acl.add_query_filter(Expense.objects, claimerRc).filter(claimer=claimerRc, office=officeRc).exclude(sts=Status.DRAFT.value).order_by('-id').first()
            if lastExpenseHdr is not None:
                if isNullBlank(payeeID):
                    payeeID = lastExpenseHdr.payee.id
                if isNullBlank(approverID) and isNotNullBlank(lastExpenseHdr.approver):
                    approverID = lastExpenseHdr.approver.id

        if settleByPriorBalance == 'Y':
            settleByPettyCash = None
        if isNullBlank(settleByPriorBalanceCCY):
            # get current office's default currency.
            settleByPriorBalanceCCY = officeRc.ccy.id

        if paymentData is None:
            paymentData = {}
        paymentData['sn'] = sn
        paymentData['sts'] = sts
        paymentData['poNo'] = poNo
        paymentData['payeeID'] = payeeID
        paymentData['approverID'] = approverID
        paymentData['settleByPriorBalance'] = settleByPriorBalance
        paymentData['settleByPettyCash'] = settleByPettyCash
        paymentData['settleByPriorBalanceCCY'] = settleByPriorBalanceCCY
        paymentData['expenseDsc'] = expenseDsc
        paymentData['supportingDoc'] = supportingDoc

        self.setSessionParameter(self.SESSION_KEY_PAYMENT_DATA, paymentData)
        return paymentData

    def updatePaymentData(self):
        """Change the [Payee] combobox or [Settle by Prior Balance] combobox"""
        paymentData = self._getRequestValue("paymentFg", default=None)
        if paymentData.get('settleByPriorBalance', None) == 'Y':
            paymentData['settleByPettyCash'] = None  # reset
        self.deleteSessionParameters(self.SESSION_KEY_PB_DATA)
        self.setSessionParameter(self.SESSION_KEY_PAYMENT_DATA, paymentData)

    def getPriorBalanceCCYs(self):
        """Get settle by prior balance CCY.

            Return [{'id': 1, 'code': 'USD'}, {'id': 2, 'code': 'HKD (FX)'}]
        """
        ccyRcs = []
        paymentData = self.getSessionParameter(self.SESSION_KEY_PAYMENT_DATA)
        if paymentData is not None:
            payeeID = paymentData.get('payeeID', None)
            payeeRc = Payee.objects.filter(office=self._getCurrentOffice(), id=int(payeeID)).first() if isNotNullBlank(payeeID) else None
            if isNotNullBlank(payeeRc):
                ccyRcs = ca.getAvailablePriorBalanceCCYRcs(payeeRc, True)
        else:
            hdrRc = self.__getExpenseHdrRc()
            if isNotNullBlank(hdrRc):
                ccyRcs = [hdrRc.fx_ccy if hdrRc.fx_ccy is not None else (hdrRc.office.ccy if hdrRc.office is not None else None)]
        return [{'id': r.id, 'code': r.code} for r in ccyRcs]

    def getAvailablePriorBalanceRcs(self):
        """Get available prior balance records if the payee selected and it's settled by prior balance.
            return [AvailablePriorBalance]
        """
        officeRc = self._getCurrentOffice()
        payeeRc = None
        paymentData = self.getSessionParameter(self.SESSION_KEY_PAYMENT_DATA, default={})
        payeeID = paymentData.get('payeeID', None)
        settleByPriorBalance = paymentData.get('settleByPriorBalance', None)
        settleByPriorBalanceCCYID = paymentData.get('settleByPriorBalanceCCY', None)
        if isNullBlank(payeeID) or isNullBlank(settleByPriorBalanceCCYID):
            return None
        payeeID = int(payeeID)
        payeeRc = Payee.objects.filter(office=officeRc, id=payeeID).first()
        if payeeRc is None:
            logger.error("Payee doesn't exist. Office=%s, OfficeID=%s, PayeeID=%s" % (officeRc.code, officeRc.id, payeeID))
            return IkErrJsonResponse(message="Payee doesn't exist.")
        ccyRc = None
        if settleByPriorBalanceCCYID is not None:
            settleByPriorBalanceCCYID = int(settleByPriorBalanceCCYID)
            ccyRc = Currency.objects.filter(id=settleByPriorBalanceCCYID).first()
            if ccyRc is None:
                logger.error("Currency doesn't exist. Office=%s, OfficeID=%s, ccyID=%s" % (officeRc.code, officeRc.id, settleByPriorBalanceCCYID))
                return IkErrJsonResponse(message="Currency doesn't exist.")
        availableRcs = ca.getAvailablePriorBalanceRcs(payeeRc, ccyRc)
        if len(availableRcs) == 0:
            if settleByPriorBalance == 'Y':
                message = "No more cash advancement left for payee [%s]. Please set \"Settle by Prior Balance\" to [No]." % payeeRc.payee
                return IkErrJsonResponse(data=availableRcs, message=message)
            return IkSccJsonResponse(data=availableRcs)
        expense_id = self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID)
        if expense_id is not None:
            totalAmount, message = self.__getTotalAmount(self.getCurrentUser(), expense_id, payeeRc.office.ccy, officeRc, False)
            if message is not None:
                self._addWarnMessage(message)
            totalLeft = totalAmount
            if settleByPriorBalance == 'Y':
                for rc in availableRcs:
                    if totalLeft > 0 and settleByPriorBalance == 'Y':
                        cashLeft = rc.balance_amt
                        if cashLeft > 0:
                            thisAmount = cashLeft if totalLeft > cashLeft else totalLeft
                            rc.deduction_amt = float(thisAmount)
                            totalLeft = es_tools.sub(totalLeft, thisAmount)
                    if totalLeft <= 0:
                        break
                if totalLeft > 0:
                    self._addWarnMessage("No enough advanced left. Please check.")
            self.setSessionParameter(self.SESSION_KEY_PB_DATA, [[r.ca.id, r.ccy.id, r.fx.id if r.fx is not None else None, r.total_amt, r.balance_amt] for r in availableRcs])
        else:
            self.deleteSessionParameters(self.SESSION_KEY_PB_DATA)
        return availableRcs

    def submitExpense(self):
        """User click "Submit" button to submit the expenses"""
        expense_id = self.getSessionParameter(self.SESSION_KEY_EXPENSE_HDR_ID)

        paymentData = self._getRequestValue("paymentFg", default=None)
        self.setSessionParameter(self.SESSION_KEY_PAYMENT_DATA, paymentData)
        availablePriorBalanceRcs = self._getRequestValue('availablePriorBalanceFg', default=None)

        def validate(name: str, dataType: object) -> any:
            value = paymentData.get(name)
            if isNullBlank(value):
                value = None
            elif dataType is bool:
                return str(value).lower() == 'true'
            elif dataType is int:
                return int(value)
            else:
                value = dataType(str(value).strip())
            return value
        po_sn = validate('poNo', str)
        payeeID = validate('payeeID', int)
        approverID = validate('approverID', int)
        isSettleByPriorBalance = validate('settleByPriorBalance', str) == "Y"
        isSettleByPettyCash = validate('settleByPettyCash', bool)
        priorBalanceCCYID = validate('settleByPriorBalanceCCY', int)
        expenseDescription = validate('expenseDsc', str)

        priorBalanceRcs = None
        if availablePriorBalanceRcs is not None:
            priorBalanceRcs = []
            pbTableData = self.getSessionParameter(self.SESSION_KEY_PB_DATA)
            rowNo = -1
            for r in availablePriorBalanceRcs:
                rowNo += 1
                rowData = pbTableData[rowNo]
                r.ca = CashAdvancement.objects.filter(id=rowData[0]).first()
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
                        # priorBalanceData.append((r['id'], pb))
                        r.deduction_amt = pb
                        priorBalanceRcs.append(r)
        submittedExpenseHdrID = es.submitExpense(self.getCurrentUser(), self._getCurrentOffice(), expense_id, payeeID, approverID, expenseDescription,
                                                 isSettleByPriorBalance, priorBalanceRcs, priorBalanceCCYID, isSettleByPettyCash, po_sn)
        self.deleteSessionParameters(self.SESSION_KEY_EXPENSE_HDR_ID)
        return self._openScreen(menuName=const.MENU_ES005, parameters={'id': submittedExpenseHdrID})  # TODO:

    def _getFileStyle(self, dataRcs: list[File], selectedFileID: int) -> list:
        if dataRcs is None or len(dataRcs) == 0:
            return None
        if selectedFileID is None:
            return None
        rowStyles = []
        for rc in dataRcs:
            if rc is None:
                continue
            if isNullBlank(rc.amount):
                rowStyles.append({"row": rc.id, "class": 'draft'})
            if rc.id == selectedFileID:
                rowStyles.append({"row": rc.id, "class": 'row_select'})
        return rowStyles

    def _getExpenseStyle(self, dataRcs: list[ExpenseDetail], selectedExpenseID: int, selectedFileID: int) -> list:
        if dataRcs is None or len(dataRcs) == 0:
            return None
        rowStyles = []
        for rc in dataRcs:
            if rc is None:
                continue
            fileID = rc.file.id if rc.file is not None else None  # expenseRc
            if (isNotNullBlank(fileID) and fileID == selectedFileID) or rc.id == selectedExpenseID:
                rowStyles.append({"row": rc.id, "class": 'row_select'})
        return rowStyles

    def uploadSupportingDoc(self):
        """Click [Upload Supporting Document] button to upload supporting document."""
        office_rc = self._getCurrentOffice()
        if office_rc is None:
            return IkErrJsonResponse(message="Please select office first.")

        uploadFiles = self.getRequestData().getFiles('uploadField')
        if uploadFiles is None or len(uploadFiles) == 0 or uploadFiles[0] is None:
            return IkErrJsonResponse(message="Please select a file to upload.")
        hdrRc = self.__getExpenseHdrRc()
        uploadPageFile = None
        try:
            uploadPageFile = ESFileManager.save_uploaded_really_file(uploadFiles[0], self.__class__.__name__, self.getCurrentUserName())
            new_file_rc = es.uploadExpenseSupportingDocument(self.getCurrentUserId(), hdrRc, uploadPageFile)
            self.deleteSessionParameters(self.SESSION_KEY_EXPENSE_ID)
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, new_file_rc.id)
            paymentData = self.getSessionParameter(self.SESSION_KEY_PAYMENT_DATA)
            if isNotNullBlank(paymentData):
                paymentData['supportingDoc'] = es.getExpenseSupportingDocumentFilename(new_file_rc)
                self.setSessionParameter(self.SESSION_KEY_PAYMENT_DATA, paymentData)
            uploadMessage = "If the supporting document has a hard copy, please write the sequence number %s "\
                "on the top right corner of the page and give it to the accounts department!" % new_file_rc.seq
            return IkSccJsonResponse(message=uploadMessage)
        finally:
            ESFileManager.delete_really_file(uploadPageFile)

    def displaySupportingDoc(self):
        """Click [Display Supporting Document] button to display the supporting document."""
        ""
        self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
        hdrRc = self.__getExpenseHdrRc()
        if hdrRc is not None and hdrRc.supporting_doc is not None:
            self.deleteSessionParameters(self.SESSION_KEY_EXPENSE_ID)
            self.setSessionParameter(self.SESSION_KEY_FILE_ID, hdrRc.supporting_doc.id)
        else:
            return IkErrJsonResponse(message="Supporting document doesn't exist.")

    def downloadSupportingDoc(self):
        """Click [Download Supporting Document] button to download the supporting document."""
        hdrRc = self.__getExpenseHdrRc()
        if hdrRc is not None and hdrRc.supporting_doc is not None:
            f = ESFileManager.getESFile(hdrRc.supporting_doc.id)
            if not isNullBlank(f):
                return self.downloadFile(f.file, es.getExpenseSupportingDocumentFilename(hdrRc.supporting_doc))
        return IkErrJsonResponse(message="Supporting document doesn't exist.")

    def deleteSupportingDoc(self):
        """Click [Delete Supporting Document] button to delete the supporting document."""
        hdrRc = self.__getExpenseHdrRc()
        if hdrRc is not None:
            fileID = es.deleteExpenseSupportingDocument(self.getCurrentUserId(), hdrRc)
            if fileID is None:
                return IkErrJsonResponse(message="File doesn't exist.")
            if fileID == self.getSessionParameterInt(self.SESSION_KEY_FILE_ID):
                self.deleteSessionParameters(self.SESSION_KEY_FILE_ID)
            paymentData = self.getSessionParameter(self.SESSION_KEY_PAYMENT_DATA)
            if isNotNullBlank(paymentData):
                paymentData['supportingDoc'] = ''
                self.setSessionParameter(self.SESSION_KEY_PAYMENT_DATA, paymentData)
            return IkSccJsonResponse(message="Deleted supporting document.")
        return IkErrJsonResponse(message="Supporting document doesn't exist.")

    def __getTotalAmount(self, claimer_rc: User, expenseHdrID: int, currencyRc: Currency, office_rc: Office, isSettleByPriorForeignBalance: bool = False):
        """
        Compute the total amount for a claimer across multiple expense entries, 
        taking into consideration different currencies and exchange rates.

        Args:
            claimerID (int): The ID of the claimer.
            expenseHdrID (int): The ID of the current expense header.
            currencyRc (Currency): The currency for the total amount computation.
            isSettleByPriorForeignBalance (bool): 

        Returns:
            totalAmount (float): The total amount computed across the expenses.
            message (Optional[str]): A message indicating any inconsistencies in currency and exchange rate. 

        Notes:
            1. If an expense entry has the same currency as the provided currency, its amount is added to the total amount directly.
            2. If an expense entry has a different currency, but has a non-null exchange rate, its amount (converted using the exchange rate) is added to the total amount.
            3. If an expense entry has a different currency and a null exchange rate, its amount is added directly to the total amount and a message is generated.

        """
        claimerID = claimer_rc.id
        officeID = office_rc.id
        if expenseHdrID is None:
            draftHdrRc = es.get_last_draft_expense(claimer_rc, officeID)
            if draftHdrRc is None:
                return 0, None
            expenseHdrID = draftHdrRc.id
        detailRcs = ExpenseDetail.objects.filter(hdr_id=expenseHdrID, claimer_id=claimerID, office_id=officeID) \
            if expenseHdrID is not None else ExpenseDetail.objects.filter(hdr__isnull=True, claimer_id=claimerID, office_id=officeID)
        detailRcs = detailRcs.order_by('seq', 'incur_dt', 'id').values_list('ccy_id', 'ex_rate', 'amt')
        totalAmount = 0.0
        message1 = message2 = None
        for rc in detailRcs:
            ccyID, exRage, amount = rc[0], rc[1], rc[2]
            if ccyID == currencyRc.id:
                totalAmount = round_currency(es_tools.add(totalAmount, amount))
            else:
                if isSettleByPriorForeignBalance and (isNullBlank(exRage) or str(exRage) != '1'):
                    message1 = "The selected office's CCY is " + currencyRc.code + ". Please check the CCY and Ex. Rate. If the CCY is not " + currencyRc.code \
                        + ", then please fill in the Ex. Rate. If you're going to use other CCY to settle by prior balance, please set the rate to 1."
                if not isNullBlank(exRage):
                    totalAmount = round_currency(es_tools.add(totalAmount, es_tools.mul(amount, exRage)))
                else:
                    totalAmount = round_currency(es_tools.add(totalAmount, amount))
                    message2 = "The selected office's CCY is " + currencyRc.code + ". Please check the CCY and Ex. Rate. If the CCY is not " + currencyRc.code \
                        + ", then please fill in the Ex. Rate. For FX expense, please fill in 1.0."
        if isSettleByPriorForeignBalance and message1:
            message = message1
        elif message2:
            message = message2
        else:
            message = None
        return float(totalAmount), message
