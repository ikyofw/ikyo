import logging
from core.core.http import IkErrJsonResponse
from core.utils.langUtils import isNullBlank
from core.models import Office, UserOffice
from ..core.office import get_user_offices
from ..views.es_base_views import ESAPIView
                

logger = logging.getLogger('ikyo')


class ES002(ESAPIView):
    """ES002 - Select Office
    """

    def getOfficeRcs(self):
        office_rcs = get_user_offices(self.getCurrentUser())
        return [{'id': r.id, 'name': '%s - %s' % (r.code, r.name)} for r in office_rcs]

    def getCurrentOfficeRc(self):
        selected_office_id = self._getCurrentOfficeID()
        if selected_office_id is None:
            return None
        return {'id': selected_office_id}

    def save(self):
        office_rc = self._getRequestValue('officeFg')  # type: Office
        if isNullBlank(office_rc.id):
            return IkErrJsonResponse(message='Please select an office.')
        return self._setCurrentOffice(office_rc.id)
