import logging

from django.db.models import Q
from core.core.http import IkErrJsonResponse
from core.core.exception import IkValidateException
from core.utils.langUtils import isNotNullBlank
from .es_base_views import ESAPIView
from ..models import User,  Accounting

logger = logging.getLogger('ikyo')


class ES001C(ESAPIView):
    """ES001C - Finance Personnel
    """

    def getFpRcs(self):
        """Get Finance Personnel records"""
        queryData = self.getSearchData(fieldGroupName='schFg')
        schOfficeID = queryData.get('schOffice', None) if queryData else None
        schDefault = queryData.get('schDefault', None) if queryData else None
        schContent = queryData.get('schContent', None) if queryData else None
        fpFilter = Accounting.objects
        if isNotNullBlank(schOfficeID):
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            if int(schOfficeID) not in officeIDs:
                logger.error(
                    "You don't have permission to access to this office. ID=" % schOfficeID)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            fpFilter = fpFilter.filter(office=schOfficeID)
        elif not self.isAdministrator():
            # limit office
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            fpFilter = fpFilter.filter(office__in=officeIDs)
        if isNotNullBlank(schDefault) and bool(schDefault):
            fpFilter = fpFilter.filter(is_default=True)
        if isNotNullBlank(schContent):
            fpFilter = fpFilter.filter(Q(usr__usr_nm__icontains=schContent)
                                       | Q(rmk__icontains=schContent))
        # update the display fields, please reference to screen definination.
        fpRcs = fpFilter.order_by('office__name', 'usr__usr_nm')
        for rc in fpRcs:
            rc.usr_id = rc.usr.usr_nm
        return fpRcs

    # overwrite
    def _BIFSave(self):
        fpRcs = self.getRequestData().get('fpFg')
        defaultFPs = {}
        for rc in fpRcs:
            rc: Accounting

            if rc.ik_is_status_delete():
                continue
            
            if isNotNullBlank(rc.usr_id):
                userRc = User.objects.filter(
                    usr_nm=str(rc.usr_id).strip()).first()
                if not userRc:
                    return IkErrJsonResponse(message="User [%s] doesn't exist. Please check." % rc.usr_id)
                rc.usr = userRc

            if rc.is_default:
                if rc.office.id in defaultFPs.keys():
                    return IkErrJsonResponse(message="Each office only allow has one default finance person. Please check the office [%s]." % rc.office.name)
                defaultFPs[rc.office.id] = rc.usr.id
        return super()._BIFSave()
