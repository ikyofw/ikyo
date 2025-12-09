
"""ES101 - Expense Report

"""

import logging

from core.core.http import IkSccJsonResponse

from ..core import es_report
from ..core.office import get_user_offices
from ..models import PaymentMethod
from .es_base import ESAPIView

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
        office_rcs = get_user_offices(self.getCurrentUser(), True)
        return [{'id': r.id, 'name': '%s - %s' % (r.code, r.name)} for r in office_rcs]

    def getPayMed(self) -> any:
        pay_med_rcs = PaymentMethod.objects.all().order_by('tp')
        data = [{'id': rc.id, 'tp': rc.tp} for rc in pay_med_rcs]
        data.append({'id': -1, 'tp': 'cash advancement(petty cash, prior balance)'})
        return IkSccJsonResponse(data=data)

    def download(self):
        '''
            export report file.
        '''
        sch_items = self.getRequestData().get('schFg')
        outputFile, incurrence_date_from, incurrence_date_to = es_report.generate_rpt(self.getCurrentUser(), self.getLastTemplateRevisionFile(), sch_items)

        sch_items['schDateFrom'] = incurrence_date_from
        sch_items['schDateTo'] = incurrence_date_to
        self.setSessionParameters({'sch_items': sch_items})
        return self.downloadFile(outputFile)
