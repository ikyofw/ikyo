
"""ES101 - Expense Report

"""

import logging

from core.core.http import IkSccJsonResponse
from es.views.es_base_views import ESAPIView
import es.core.ESRpt as ESRpt
from ..core.office import get_user_offices

logger = logging.getLogger('ikyo')


class ES101(ESAPIView):
    '''
        ES101 - Expense Report
    '''

    def __init__(self) -> None:
        super().__init__()
        
    def getSchRc(self):
        data = self.getSessionParameter('sch_items')
        return IkSccJsonResponse(data=data)

    def getOffices(self) -> any:
        '''
            get offices' codes the current user can access to
        '''
        office_rcs = get_user_offices(self.getCurrentUser())
        return [{'id': r.id, 'name': '%s - %s' % (r.code, r.name)} for r in office_rcs]

    def download(self):
        '''
            export report file.
        '''
        sch_items = self.getRequestData().get('schFg')
        outputFile, incurrence_date_from, incurrence_date_to = ESRpt.generate_rpt(self.getCurrentUserId(), self.getLastTemplateRevisionFile(), sch_items)
        
        sch_items['schDateFrom'] = incurrence_date_from
        sch_items['schDateTo'] = incurrence_date_to
        self.setSessionParameters({'sch_items': sch_items})
        return self.downloadFile(outputFile)
