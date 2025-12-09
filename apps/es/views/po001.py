'''
Description: PO001
version: 
Author: YL
Date: 2025-04-11 15:23:32
'''
import logging

from django.db.models import Q

import core.ui.ui as ikui
from core.core.http import *
from core.user import user_manager
from core.utils import template_utils
from core.utils.lang_utils import isNotNullBlank, isNullBlank
from core.view.screen_view import _OPEN_SCREEN_PARAM_KEY_NAME

from ..core import approver, const, es_file
from ..core import po as po_manager
from ..models import CashAdvancement, Expense, Po, PoQuotation
from .es_base import ESAPIView

logger = logging.getLogger('ikyo')


class PO001(ESAPIView):

    SESSION_KEY_FILE_ID = 'display_file_ID'
    SESSION_KEY_PO_ID = 'po_ID'
    SESSION_KEY_PO_QUO_ID = 'po_quo_ID'
    SESSION_KEY_IS_NEW = 'is_new'
    SESSION_KEY_SHOW_EXPENSE = 'show_expense'
    SESSION_KEY_SHOW_CASH = 'show_cash'

    def __init__(self) -> None:
        super().__init__()
        self._addStaticResource(self.get_last_static_revision_file('po.css', 'es/css'))

        def beforeDisplayAdapter(screen: ikui.Screen):
            user = self.getCurrentUser()
            is_admin = self.isAdministrator()
            po_rc = self.__getCurrentPoRc()
            is_new = self.getSessionParameter(self.SESSION_KEY_IS_NEW) if isNotNullBlank(self.getSessionParameter(self.SESSION_KEY_IS_NEW)) else False

            screen.setFieldGroupsVisible(fieldGroupNames=('schFg', 'legend', 'newToolbar', 'poListFg'), visible=not is_new)
            screen.setFieldGroupsVisible(fieldGroupNames=('poDtlFg', 'quotationListFg', 'poDtl2Fg', 'toolbar'), visible=isNotNullBlank(po_rc) or is_new)
            screen.setFieldGroupsVisible(fieldGroupNames=('uploadFg', 'uploadToolbar'), visible=isNotNullBlank(po_rc))
            screen.setFieldGroupsVisible(fieldGroupNames='expenseFg', visible=self.getSessionParameterBool(self.SESSION_KEY_SHOW_EXPENSE))
            screen.setFieldGroupsVisible(fieldGroupNames='cashFg', visible=self.getSessionParameterBool(self.SESSION_KEY_SHOW_CASH))

            if isNotNullBlank(po_rc):
                status = po_rc.status
                assigned_approver = po_rc.assigned_approver

                form_editable = status == Po.SAVED_STATUS or (status == Po.SUBMITTED_STATUS and (
                    is_admin or assigned_approver.id == user.id)) or status == Po.REJECTED_STATUS
                screen.setFieldGroupsEnable(fieldGroupNames=('poDtlFg', 'quotationListFg', 'poDtl2Fg'),
                                            isEditable=form_editable, isInsertable=form_editable, isDeletable=form_editable)

                screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttSave', visible=po_manager.is_saveable(user, po_rc, is_admin))
                screen.setFieldsEditable(fieldGroupName='toolbar', fieldNames='bttSave', editable=po_manager.is_saveable(user, po_rc, is_admin))

                screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttSubmit', visible=po_manager.is_submittable(user, po_rc))
                screen.setFieldsEditable(fieldGroupName='toolbar', fieldNames='bttSubmit', editable=po_manager.is_submittable(user, po_rc))

                screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttApprove', visible=po_manager.is_approvable(user, po_rc, is_admin))
                screen.setFieldsEditable(fieldGroupName='toolbar', fieldNames='bttApprove', editable=po_manager.is_approvable(user, po_rc, is_admin))

                screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttReject', visible=po_manager.is_rejectable(user, po_rc, is_admin))
                screen.setFieldsEditable(fieldGroupName='toolbar', fieldNames='bttReject', editable=po_manager.is_rejectable(user, po_rc, is_admin))
                screen.setFieldsEditable(fieldGroupName='poDtl2Fg', fieldNames='rmkField', editable=po_manager.is_rejectable(user, po_rc, is_admin))

                screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames='bttDelete', visible=po_manager.is_deletable(user, po_rc))
                screen.setFieldsEditable(fieldGroupName='toolbar', fieldNames='bttDelete', editable=po_manager.is_deletable(user, po_rc))

                screen.setFieldGroupsVisible(fieldGroupNames=('uploadFg', 'uploadToolbar'), visible=po_rc.status == Po.APPROVED_STATUS)
                screen.setFieldGroupsEnable(fieldGroupNames=('uploadFg', 'uploadToolbar'), isEditable=po_rc.status == Po.APPROVED_STATUS)
            else:
                screen.setFieldsVisible(fieldGroupName='toolbar', fieldNames=('bttApprove', 'bttReject', 'bttDelete'), visible=False)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getSts(self):
        data = [Po.SAVED_STATUS, Po.SUBMITTED_STATUS, Po.APPROVED_STATUS, Po.REJECTED_STATUS]
        return IkSccJsonResponse(data=data)

    def getOfficeRcs(self):
        offices = super().getOfficeRcs()
        po_rc = self.__getCurrentPoRc()
        if po_rc:
            po_office_id = po_rc.office.id
            if not any(office['id'] == po_office_id for office in offices):
                offices.append({'id': po_rc.office.id, 'name': po_rc.office.name})
                offices.sort(key=lambda x: x['name'])
        return offices

    def getSubmitter(self):
        data = []
        for rc in Po.objects.all().order_by('submitter', 'submitter__usr_nm').distinct('submitter'):
            if isNotNullBlank(rc.submitter):
                data.append({'id': rc.submitter.id, 'usr_nm': rc.submitter.usr_nm})
        return IkSccJsonResponse(data=data)

    def getApprover(self):
        data = approver.get_office_first_approvers(self._getCurrentOffice(), self.getCurrentUser())
        return IkSccJsonResponse(data=data)

    def getSchRc(self):
        sch_item = self.getSessionParameter('sch_item')
        return IkSccJsonResponse(data=sch_item)

    def search(self):
        self.__clear_all_session()
        sch_item = self.getRequestData().get('schFg', None)
        if all(v in [None, '', [], {}] for v in sch_item.values()):
            sch_item = None
        return self.setSessionParameters({'sch_item': sch_item})

    def getHtmlLegend(self):
        html = template_utils.loadTemplateFile('po001/legend.html')
        return IkSccJsonResponse(data=html)

    def getPoRcs(self):
        user_rc = self.getCurrentUser()
        data = Po.objects.filter(deleter__isnull=True).exclude(Q(status=Po.SAVED_STATUS) & ~Q(cre_usr=user_rc))
        if not self.isAdministrator():
            data = data.filter(Q(cre_usr_id=user_rc.id) | Q(submitter_id=user_rc.id) | Q(assigned_approver_id=user_rc.id))

        # search
        sch_item = self.getSessionParameter('sch_item')
        if isNotNullBlank(sch_item):
            no = sch_item.get('schPono')
            purchase_item = sch_item.get('schPurchaseItem')
            office = sch_item.get('schOffice')
            status = sch_item.get('schStatus')
            submit_dt_from = sch_item.get('schSubmitDtFrom')
            submit_dt_to = sch_item.get('schSubmitDtTo')
            operate_dt_from = sch_item.get('schARDtFrom')
            operate_dt_to = sch_item.get('schARDtTo')
            submitter = sch_item.get('schSubmitter')
            approver = sch_item.get('schApprover')

            if no:
                data = data.filter(sn__icontains=no)
            if purchase_item:
                data = data.filter(purchase_item__icontains=purchase_item)
            if office:
                data = data.filter(office=office)
            if status:
                data = data.filter(status=status)
            if submit_dt_from:
                data = data.filter(submit_dt__gte=submit_dt_from)
            if submit_dt_to:
                data = data.filter(submit_dt__lte=submit_dt_to)
            if operate_dt_from:
                data = data.filter(Q(approve_dt__gte=operate_dt_from) | Q(reject_dt__gte=operate_dt_from))
            if operate_dt_to:
                data = data.filter(Q(approve_dt__lte=operate_dt_to) | Q(reject_dt__lte=operate_dt_to))
            if submitter:
                data = data.filter(submitter_id=submitter)
            if approver:
                data = data.filter(assigned_approver_id=approver)
        data = data.order_by('-id')

        po_id = self.__getCurrentPoID()

        def get_style_func(result) -> list:
            style = []
            for r in result:
                if isNotNullBlank(po_id) and str(r['id']) == str(po_id):
                    r['__CRR_'] = True

                if r['status'] == Po.APPROVED_STATUS:
                    r['operator.usr_nm'] = user_manager.getUserName(r['approver_id'])
                    r['operate_dt'] = r['approve_dt']
                elif r['status'] == Po.REJECTED_STATUS:
                    r['operator.usr_nm'] = user_manager.getUserName(r['rejecter_id'])
                    r['operate_dt'] = r['reject_dt']
                else:
                    r['operator.usr_nm'] = user_manager.getUserName(r['assigned_approver_id'])
                r['show_file'] = True if isNotNullBlank(r['file_id']) else False

                style.append({"row": r['id'], "class": "row_" + r['status']})
            return style
        return self.getPagingResponse(table_name="poListFg", table_data=data, get_style_func=get_style_func)

    def poListFg_EditIndexField_Click(self):
        return self.setSessionParameter(self.SESSION_KEY_PO_ID, self._getEditIndexField())

    def getPoRc(self):
        po_rc = self.__getCurrentPoRc()
        is_new = self.getSessionParameter(self.SESSION_KEY_IS_NEW)
        data = None
        if isNotNullBlank(po_rc):  # detail
            data = po_rc
        elif is_new:  # new
            data = Po()
            data.office = self._getCurrentOffice()
        return IkSccJsonResponse(data=data)

    def getPoRc2(self):
        po_rc = self.__getCurrentPoRc()
        is_new = self.getSessionParameter(self.SESSION_KEY_IS_NEW)
        data = None
        if isNotNullBlank(po_rc):  # detail
            data = po_rc
        elif is_new:  # new
            data = Po()
            data.office = self._getCurrentOffice()
        return IkSccJsonResponse(data=data)

    def getQuotationRcs(self):
        po_id = self.__getCurrentPoID()
        data = None
        if po_id:
            data = PoQuotation.objects.filter(po_id=po_id).order_by('id')
            for d in data:
                d.have_file = isNotNullBlank(d.file)
        return data

    def getExpenseRcs(self):
        po_rc = self.__getCurrentPoRc()
        data = None
        have_expense = False
        if po_rc:
            data = Expense.objects.filter(po=po_rc).order_by('id')
            have_expense = data.count() > 0
        self.setSessionParameter(self.SESSION_KEY_SHOW_EXPENSE, have_expense)

        def get_style_func(result) -> list:
            style = []
            for r in result:
                style.append({"row": r['id'], "class": "row_" + r['sts']})
            return style
        return self.getPagingResponse(table_name="expenseFg", table_data=data, get_style_func=get_style_func)

    def getCashRcs(self):
        po_rc = self.__getCurrentPoRc()
        data = None
        have_cash = False
        if po_rc:
            data = CashAdvancement.objects.filter(po=po_rc).order_by('id')
            have_cash = data.count() > 0
        self.setSessionParameter(self.SESSION_KEY_SHOW_CASH, have_cash)

        def get_style_func(result) -> list:
            style = []
            for r in result:
                style.append({"row": r['id'], "class": "row_" + r['sts']})
            return style
        return self.getPagingResponse(table_name="cashFg", table_data=data, get_style_func=get_style_func)

    def new(self):
        self.__clear_all_session()
        self.setSessionParameter(self.SESSION_KEY_IS_NEW, True)

    def back(self):
        # get es id if have
        self.__clear_all_session()
        pre_screen_nm = self._getPreviousScreenName()
        if isNotNullBlank(pre_screen_nm):
            request_data = self._getPreviousScreenRequestData()
            es_id = request_data.pop("es_id", None) if request_data is not None else None
            self.setSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, value=request_data, isGlobal=True)
            params = {'id': es_id}
            return self._openScreen(menuName=pre_screen_nm, parameters=params)

    def showPOFile(self):
        """ Display PO File
        """
        po_id = self.getRequestData().get('id')
        file_id = Po.objects.filter(id=po_id).first().file_id
        return self.setSessionParameter(self.SESSION_KEY_FILE_ID, file_id)

    def getQuoId(self):
        """ Get Po quotation id for upload file
        """
        po_quo_id = self.getRequestData().get('id')
        return self.setSessionParameter(self.SESSION_KEY_PO_QUO_ID, po_quo_id)

    def uploadPoQuoFile(self):
        """ Upload Quotation File
        """
        quo_id = self.getSessionParameter(self.SESSION_KEY_PO_QUO_ID)
        if isNullBlank(quo_id):
            return IkSysErrJsonResponse()
        result = po_manager.upload_quotation_file(self.getCurrentUser(), self.__class__.__name__, quo_id, self.getRequestData().getFiles('uploadField'))
        if result.value:
            return IkSccJsonResponse(message="Uploaded.")
        return result.toIkJsonResponse1()

    def showPoQuoFile(self):
        """ Download Quotation File
        """
        quo_id = self.getRequestData().get('id')
        if isNotNullBlank(quo_id):
            quo_rc = PoQuotation.objects.filter(id=quo_id).first()
            return self.setSessionParameter(self.SESSION_KEY_FILE_ID, quo_rc.file_id)
        return IkSysErrJsonResponse()

    def uploadPoFile(self):
        """ Sign PO File
        """
        po_id = self.__getCurrentPoID()
        if isNullBlank(po_id):
            return IkSysErrJsonResponse()
        rmk = self.getRequestData().get('file_rmk')
        upload_file = self.getRequestData().getFile()
        result = po_manager.upload_po_file(self.getCurrentUser(), self.__class__.__name__, po_id, rmk, upload_file)
        if result.value:
            return IkSccJsonResponse(message="Uploaded.")
        return result.toIkJsonResponse1()

    def save(self):
        """ Save Po detail
        """
        request_date = self.getRequestData()
        po_rc1 = request_date.get('poDtlFg')
        po_quo_rcs = request_date.get('quotationListFg')
        po_rc2 = request_date.get('poDtl2Fg')
        result = po_manager.save_or_submit_po_detail(self.getCurrentUser(), self.isAdministrator(), self._getCurrentOffice(), po_rc1, po_quo_rcs, po_rc2, Po.SAVED_STATUS)
        if result.value:
            self.setSessionParameter(self.SESSION_KEY_PO_ID, result.data)
            return IkSccJsonResponse(message="Saved.")
        return result.toIkJsonResponse1()

    def submit(self):
        """ Submit Po
        """
        request_date = self.getRequestData()
        po_rc1 = request_date.get('poDtlFg')
        po_quo_rcs = request_date.get('quotationListFg')
        po_rc2 = request_date.get('poDtl2Fg')
        result = po_manager.save_or_submit_po_detail(self.getCurrentUser(), self.isAdministrator(), self._getCurrentOffice(), po_rc1, po_quo_rcs, po_rc2, Po.SUBMITTED_STATUS)
        if result.value:
            return IkSccJsonResponse(message="Submitted.")
        return result.toIkJsonResponse1()

    def getApproveConfirmMessage(self):
        message = "Are you sure to approve this purchase?"
        po_rc = Po.objects.filter(id=self.__getCurrentPoID()).first()
        if po_rc and po_rc.assigned_approver != self.getCurrentUser():
            message = "You are not the approver of the purchase, Are you sure to approve this purchase?"
        return ikui.DialogMessage.getSuccessResponse(message=message)

    def approve(self):
        """ Approve Po
        """
        rmk = self.getRequestData().get('poDtl2Fg').rmk
        result = po_manager.approve_or_reject(self.getCurrentUser(), self.isAdministrator(), self.__getCurrentPoID(), rmk, Po.APPROVED_STATUS)
        if result.value:
            return IkSccJsonResponse(message="Approved.")
        return result.toIkJsonResponse1()

    def getRejectConfirmMessage(self):
        message = "Are you sure to reject this purchase?"
        po_rc = Po.objects.filter(id=self.__getCurrentPoID()).first()
        if po_rc and po_rc.assigned_approver != self.getCurrentUser():
            message = "You are not the approver of the purchase, Are you sure to reject this purchase?"
        return ikui.DialogMessage.getSuccessResponse(message=message)

    def reject(self):
        """ Reject Po
        """
        rmk = self.getRequestData().get('poDtl2Fg').rmk
        result = po_manager.approve_or_reject(self.getCurrentUser(), self.isAdministrator(), self.__getCurrentPoID(), rmk, Po.REJECTED_STATUS)
        if result.value:
            return IkSccJsonResponse(message="Rejected.")
        return result.toIkJsonResponse1()

    def getDeleteConfirmMessage(self):
        message = "Are you sure to delete this purchase?"
        po_rc = Po.objects.filter(id=self.__getCurrentPoID()).first()
        if po_rc and po_rc.submitter != self.getCurrentUser():
            message = "You are not the submitter of the purchase, Are you sure to delete this purchase?"
        return ikui.DialogMessage.getSuccessResponse(message=message)

    def delete(self):
        """ Delete Po
        """
        result = po_manager.delete(self.getCurrentUser(), self.__getCurrentPoID(), Po.DELETED_STATUS)
        if result.value:
            self.__clear_all_session()
        return result.toIkJsonResponse1()

    def openES005(self):
        expense_id = self.getRequestData().get('id')
        return self._openScreen(menuName=const.MENU_ES005, parameters={'id': expense_id})

    def openES006(self):
        cash_id = self.getRequestData().get('id')
        return self._openScreen(menuName=const.MENU_ES006, parameters={'id': cash_id})

    def getPdfViewer(self):
        """ Display File
        """
        file_id = self.getSessionParameter(self.SESSION_KEY_FILE_ID)
        if isNotNullBlank(file_id):
            ef = es_file.getESFile(file_id)
            if isNotNullBlank(ef):
                if os.path.isfile(ef.file):
                    return responseFile(filePath=ef.file, filename=ef.filename)
        filePath = es_file.get_not_exist_file_template()
        return responseFile(filePath)

    def __getCurrentPoID(self) -> int:
        id = self.getSessionParameter(self.SESSION_KEY_PO_ID)
        pre_screen_nm = self._getPreviousScreenName()
        if isNullBlank(id) and isNotNullBlank(pre_screen_nm) and pre_screen_nm != self._menuName:
            request_data = self._getPreviousScreenRequestData()
            id = request_data.pop("id", None) if request_data is not None else None
            self.setSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, value=request_data, isGlobal=True)
            self.setSessionParameter(self.SESSION_KEY_PO_ID, id)
        return int(id) if id is not None else None

    def __getCurrentPoRc(self) -> Po | None:
        po_id = self.__getCurrentPoID()
        if isNullBlank(po_id):
            return None
        return Po.objects.filter(id=po_id).first()

    def __clear_all_session(self):
        self.deleteSessionParameters(nameFilters=[self.SESSION_KEY_PO_ID, self.SESSION_KEY_FILE_ID,
                                     self.SESSION_KEY_IS_NEW, self.SESSION_KEY_PO_QUO_ID, self.SESSION_KEY_SHOW_EXPENSE, self.SESSION_KEY_SHOW_CASH])
