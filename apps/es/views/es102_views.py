"""
ES102 - Cash Advancement Report

"""

import logging
import os
from datetime import date, datetime
from pathlib import Path

import core.core.fs as ikfs
from core.core.http import IkSccJsonResponse
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.utils.modelUtils import redcordsets2List
from core.utils.spreadsheet import SpreadsheetWriter

from ..core import CA, status
from ..core.office import get_user_offices
from ..views.es_base_views import ESAPIView
from ..models import CashAdvancement

logger = logging.getLogger('ikyo')


class ES102(ESAPIView):
    '''
        ES102 - Cash Advancement Report
    '''

    def __init__(self) -> None:
        super().__init__()

    def getSts(self):
        """Search field: Status"""
        return status.get_all_status()

    def getSchRc(self):
        data = self.getSessionParameter('sch_items')
        return IkSccJsonResponse(data=data)

    def getOffices(self) -> any:
        '''
            get offices' codes the current user can access to
        '''
        office_rcs = get_user_offices(self.getCurrentUser(), True)
        return [{'id': r.id, 'name': '%s - %s' % (r.code, r.name)} for r in office_rcs]

    def download(self):
        user_rc = self.getCurrentUser()
        office_rc = self._getCurrentOffice()
        query_params = {}
        search_data = self.getRequestData().get('schFg')
        if isNotNullBlank(search_data):
            query_params['sn'] = search_data.get('schSNField', None)
            query_params['status'] = search_data.get('schStsField', None)
            query_params['claimer'] = search_data.get('schClaimerField', None)
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

        for cash_rc in queryset:
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

            query_usage = ''
            seq = 0
            left_flag = False
            if len(usages) == 1:
                query_usage = usages[0][4]
            else:
                for (ccy_rc, _isFx, total, _used, left) in usages:
                    if int(left) > 0:
                        left_flag = True
                    seq += 1
                    if seq > 1:
                        query_usage += '\n'
                    query_usage += '%s. %s:  %s / %s' % (seq, ccy_rc.code, left, total)

            cash_rc.query_expenses = normal_expense_summary
            cash_rc.query_petty_expenses = petty_expense_summary
            cash_rc.query_usage = query_usage
            cash_rc.left_flag = left_flag

        rptDate = datetime.now()
        data = {}
        # sheet 1
        data['reporter'] = user_rc.usr_nm
        data['reportDate'] = rptDate
        data['queryFilterTable'] = [[
            query_params['sn'], query_params['claimer'], query_params['status'], query_params['payment_record_filename'],
            query_params['claim_date_from'], query_params['claim_date_to'], query_params['approve_date_from'], query_params['approve_date_to'],
            query_params['settle_date_from'], query_params['settle_date_to'], query_params['description'],
        ]]

        # sheet 2
        data['cashAdvancementTable'] = redcordsets2List(queryset, ["office.code", "sn", "claimer.usr_nm", "claim_dt", "payee.payee", "po.sn", "dsc", "ccy.code", "claim_amt", "sts", 
                                                                  "approver.usr_nm", "approve_activity.operate_dt", "query_petty_expenses", "query_petty_expenses", "query_usage", 
                                                                  "payment_activity.operate_dt", "payment_tp.tp", "payment_number", "payment_record_file.file_original_nm"])

        template_file = self.getLastTemplateRevisionFile()
        filename = 'ES102-%s-%s.%s' % (office_rc.code, rptDate.strftime('%Y%m%d%H%M%S'), ikfs.getFileExtension(template_file))
        output_file = Path(os.path.join(ikfs.getVarTempFolder(subPath='ES'), filename))
        sw = SpreadsheetWriter(parameters=data, templateFile=template_file, outputFile=output_file)
        b = sw.write()
        if not b.value:
            return b.toIkJsonResponse1()
        return self.downloadFile(output_file)






