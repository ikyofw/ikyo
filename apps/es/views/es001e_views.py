import logging

from django.db.models import Q

from core.core.exception import IkValidateException
from core.core.http import IkErrJsonResponse
from core.utils.langUtils import isNotNullBlank

from ..models import Payee, PettyCashExpenseAdmin, User
from .es_base_views import ESAPIView

logger = logging.getLogger('ikyo')


class ES001E(ESAPIView):
    """ES001E - Petty Expense
        # TODO: validate the admin is belong to selected office or not
    """

    def getPettyAdminRcs(self):
        """Get Approver records"""
        query_data = self.getSearchData(fieldGroupName='schFg')
        sch_office_id = query_data.get(
            'schOffice', None) if query_data else None
        sch_content = query_data.get(
            'schContent', None) if query_data else None
        fp_filter = PettyCashExpenseAdmin.objects
        if isNotNullBlank(sch_office_id):
            office_ids = [item['id'] for item in self.getOfficeRcs()]
            if int(sch_office_id) not in office_ids:
                logger.error(
                    "You don't have permission to access to this office. ID=" % sch_office_id)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            fp_filter = fp_filter.filter(office=sch_office_id)
        elif not self.isAdministrator():
            # limit office
            office_ids = [item['id'] for item in self.getOfficeRcs()]
            fp_filter = fp_filter.filter(office__in=office_ids)
        if isNotNullBlank(sch_content):
            fp_filter = fp_filter.filter(Q(admin__usr_nm__icontains=sch_content)
                                         | Q(admin_payee__payee__icontains=sch_content)
                                         | Q(rmk__icontains=sch_content))
        # update the display fields, please reference to screen definination.
        fpRcs = fp_filter.order_by('office__name', 'admin__usr_nm')
        for rc in fpRcs:
            rc.admin_id = rc.admin.usr_nm
            rc.admin_payee_id = rc.admin_payee.payee
        return fpRcs

    # overwrite
    def _BIFSave(self):
        petty_admin_rcs = self.getRequestData().get('pettyAdminFg')
        office_petty_admin_ids = {}
        for rc in petty_admin_rcs:
            rc: PettyCashExpenseAdmin

            if rc.ik_is_status_delete():
                continue

            if PettyCashExpenseAdmin(rc.admin_id):
                user_rc = User.objects.filter(
                    usr_nm=str(rc.admin_id).strip()).first()
                if not user_rc:
                    return IkErrJsonResponse(message="Admin [%s] doesn't exist. Please check." % rc.admin_id)
                rc.admin = user_rc
            if PettyCashExpenseAdmin(rc.admin_payee_id):
                payee_rc = Payee.objects.filter(
                    office=rc.office, payee=str(rc.admin_payee_id).strip()).first()
                if not payee_rc:
                    return IkErrJsonResponse(message="Payee [%s] doesn't exist. Please check office [%s]." % (rc.admin_payee_id, rc.office.name))
                rc.admin_payee = payee_rc

            admin_ids = office_petty_admin_ids.get(rc.office.id, [])
            if rc.admin_payee.id in admin_ids:
                return IkErrJsonResponse(message="Petty Admin is unique. Please check office [%s], administrator [%s]." % (rc.office.name, rc.admin.usr_nm))
            admin_ids.append(rc.admin_payee.id)
            office_petty_admin_ids[rc.office.id] = admin_ids

        return super()._BIFSave()
