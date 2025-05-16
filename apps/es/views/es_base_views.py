import logging

from core.core.lang import Boolean2
from core.log.logger import logger
from core.models import UserOffice
from core.utils.langUtils import isNullBlank
from core.view.screenView import ScreenAPIView

from ..core import acl, const
from ..core.office import get_user_work_office, update_user_work_office
from ..models import Office


class ESAPIView(ScreenAPIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._addStaticResource('es/css/es-v1.css')

    def getYesNo(self):
        """Combox data"""
        return [{
            'value': const.SETTLE_BY_PRIOR_BALANCE_NO,
            'display': const.SETTLE_BY_PRIOR_BALANCE_NO_DISPLAY
        }, {
            'value': const.SETTLE_BY_PRIOR_BALANCE_YES,
            'display': const.SETTLE_BY_PRIOR_BALANCE_YES_DISPLAY
        }]

    def isAdministrator(self) -> bool:
        # TODO: remove this method
        return acl.is_es_admin(self.getCurrentUser(), self._getCurrentOffice())

    def getOfficeRcs(self):
        """
            return [{id: 111, name: 'office a'}, ...]
        """
        filter = Office.objects.all()
        if not self.isAdministrator():
            officeIDs = UserOffice.objects.filter(
                usr=self.getCurrentUser()).values_list('office_id', flat=True)
            filter = filter.filter(id__in=officeIDs)
        filter = filter.order_by('name').values('id', 'name')
        return list(filter)

    def search(self):
        return self.getRequestData()

    def getSchRc(self):
        return self.getSearchData(fieldGroupName='schFg')

    def _getOfficeName(self, officeID: int) -> str:
        rc = Office.objects.filter(id=officeID).first()
        return rc.name if rc is not None else None

    def _setCurrentOffice(self, office: int | Office) -> Boolean2:
        if isNullBlank(office):
            return Boolean2.FALSE('Please select an office.')
        officeRc = Office.objects.filter(id=office).first() if type(office) == int else office
        if officeRc is None:
            logger.error("Office doesn't exist. ID=%s" % office)
            return Boolean2.FALSE("Office doesn't exist.")
        return update_user_work_office(officeRc, self.getCurrentUser())

    def _getCurrentOfficeID(self) -> int:
        officeRc = self._getCurrentOffice()
        return officeRc.id if officeRc is not None else None

    def _getCurrentOffice(self) -> Office:
        return get_user_work_office(self.getCurrentUser())
