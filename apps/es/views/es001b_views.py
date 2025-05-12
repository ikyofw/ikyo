import logging

from django.db.models import Q
from core.core.exception import IkValidateException
from core.utils.langUtils import isNullBlank
from .es_base_views import ESAPIView
from ..models import Payee

logger = logging.getLogger('ikyo')


class ES001B(ESAPIView):
    """ES001B - Payee
    """
    # TODO: each user belong to office, e.g. admin, others

    def getPayeeRcs(self):
        """Get payee records"""
        queryData = self.getSearchData(fieldGroupName='schFg')
        schOfficeID = queryData.get('schOffice', None) if queryData else None
        schContent = queryData.get('schContent', None) if queryData else None
        payeeFilter = Payee.objects
        if not isNullBlank(schOfficeID):
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            if int(schOfficeID) not in officeIDs:
                logger.error(
                    "You don't have permission to access to this office. ID=" % schOfficeID)
                raise IkValidateException(
                    "You don't have permission to access to this office.")
            payeeFilter = payeeFilter.filter(office=schOfficeID)
        elif not self.isAdministrator():
            # limit the office
            officeIDs = [item['id'] for item in self.getOfficeRcs()]
            payeeFilter = payeeFilter.filter(office__in=officeIDs)
        if not isNullBlank(schContent):
            payeeFilter = payeeFilter.filter(Q(payee__icontains=schContent)
                                             | Q(bank_info__icontains=schContent)
                                             | Q(rmk__icontains=schContent))
        return payeeFilter.order_by('office__name', 'payee')
