from datetime import datetime, date
import logging
import os
from pathlib import Path
from django.db.models import Case, When, Value, CharField, F, FloatField

from core.utils.langUtils import isNullBlank, isNotNullBlank
from core.utils.spreadsheet import SpreadsheetWriter
from core.core.exception import IkValidateException
from core.utils.modelUtils import redcordsets2List
import core.core.fs as ikfs
import core.user.userManager as UserManager
import es.core.ESFile as ESFile
from .status import Status

from ..models import Office, ExpenseDetail, Expense, CashAdvancement, PriorBalance

logger = logging.getLogger('ikyo')


def generate_rpt(operator_id: int, template_file: Path, sch_items: dict) -> Path:
    """Generate expense report (ES101).

    Args:
        operator_id (int): Report generator's ID.
        template_file (:obj:'pathlib.Path'): Report template file. E.g. var\templates\wci\ES\ES101\ES101-v4.xlsx
        sch_items (dict): Office code and date range.

    Returns:
        obj:'pathlib.Path': Export file. E.g. tmp\ES\es101-rpt1\HK-20230527123024.xlsx

    Raises:
        IkValidateException: If validate failed, then raise IkValidateException.

    """
    office = sch_items.get('schOffice', None)
    incurrence_date_from = sch_items.get("schDateFrom", None)
    incurrence_date_to = sch_items.get('schDateTo', None)

    if isNullBlank(office):
        raise IkValidateException("Please select an office.")
    office_rc = Office.objects.filter(id=office).first()
    # check permission
    # TODO: 2024-12-26, is_office_admin
    if isNotNullBlank(incurrence_date_from) and isNotNullBlank(incurrence_date_to) and incurrence_date_from > incurrence_date_to:
        # switch date range
        d = incurrence_date_to
        incurrence_date_to = incurrence_date_from
        incurrence_date_from = d
    if template_file is None:
        raise IkValidateException('Parameter [template_file] is mandatory.')
    elif not template_file.is_file():
        logger.error('Template file [%s] does not exist.' % template_file.absolute())
        raise IkValidateException('System error: template file does not exist.')

    queryset = ExpenseDetail.objects.filter(
        hdr__payee__office=office_rc,
        hdr__sts=Status.SETTLED.value
    )
    if isNotNullBlank(incurrence_date_from):
        queryset = queryset.filter(incur_dt__gte=incurrence_date_from)  # d.incur_dt>=%s
    if isNotNullBlank(incurrence_date_to):
        queryset = queryset.filter(incur_dt__lte=incurrence_date_to)    # d.incur_dt<=%s

    queryset = queryset.annotate(
        amt_calculated=Case(
            When(ex_rate__isnull=False, then=F('amt') * F('ex_rate')),
            default=F('amt'),
            output_field=FloatField()
        ),
        trn_ref=Case(
            When(hdr__payment_tp__tp='e-cheque', then=F('hdr__payment_record_file__file_original_nm')),
            When(hdr__payment_tp__tp='bank transfer', then=F('hdr__payment_number')),
            default=Value(None),
            output_field=CharField()
        ),
        claimer_nm=F('hdr__claimer__usr_nm')
    ).values(
        'incur_dt', 'dsc', 'cat__cat', 'ccy__code', 'amt', 'ex_rate',
        'amt_calculated', 'prj_nm', 'hdr__payment_tp__tp', 'trn_ref',
        'claimer_nm', 'hdr__sn', 'file__seq'
    )

    queryset = queryset.order_by('incur_dt', 'dsc', 'cat')
    expense_table = list(queryset)

    # Part 1: e-Cheque for Expense
    expense_queryset = ExpenseDetail.objects.filter(
        hdr__payee__office=office_rc,
        hdr__sts=Status.SETTLED.value,
        hdr__payment_record_file__file_original_nm__isnull=False,
    )
    if isNotNullBlank(incurrence_date_from):
        expense_queryset = expense_queryset.filter(incur_dt__gte=incurrence_date_from)
    if isNotNullBlank(incurrence_date_to):
        expense_queryset = expense_queryset.filter(incur_dt__lte=incurrence_date_to)

    expense_list, repeat_flag = [], []
    for es_rc in expense_queryset:
        sn = es_rc.hdr.sn
        if sn not in repeat_flag:
            expense_list.append({
                'sn': es_rc.hdr.sn,
                'echeque_file_nm': es_rc.hdr.payment_record_file.file_original_nm if es_rc.hdr.payment_record_file else None,
                'type': 'Expense',
                'ref_expense_no': None,
                'incur_dt': __to_datetime(es_rc.incur_dt),
            })
            repeat_flag.append(sn)

    # Part 2: e-Cheque for Cash Advancement
    cash_queryset = CashAdvancement.objects.select_related(
        'payment_activity', 'payment_record_file', 'payee'
    ).filter(
        payee__office=office_rc,
        sts=Status.SETTLED.value,
        payment_record_file__file_original_nm__isnull=False,
    )
    if isNotNullBlank(incurrence_date_from):
        cash_queryset = cash_queryset.filter(payment_activity__operate_dt__gte=incurrence_date_from)
    if isNotNullBlank(incurrence_date_to):
        cash_queryset = cash_queryset.filter(payment_activity__operate_dt__lte=incurrence_date_to)

    cash_list = []
    for ca_rc in cash_queryset.select_related('payment_activity', 'payment_record_file').order_by('sn'):
        related_expenses = PriorBalance.objects.filter(ca=ca_rc).select_related('expense')

        expense_sns = related_expenses.order_by('expense__sn').values_list('expense__sn', flat=True)
        ref_expense_no = ','.join(expense_sns)

        cash_list.append({
            'sn': ca_rc.sn,
            'echeque_file_nm': ca_rc.payment_record_file.file_original_nm if ca_rc.payment_record_file else None,
            'type': 'Cash Advancement',
            'ref_expense_no': ref_expense_no,
            'incur_dt': __to_datetime(ca_rc.payment_activity.operate_dt),
        })

    e_cheque_table = expense_list + cash_list
    e_cheque_table.sort(key=lambda x: (x['sn'], x['echeque_file_nm'] or ''))
    for idx, row in enumerate(e_cheque_table, start=1):
        row['row_no'] = idx

    rptDate = datetime.now()
    data = {}
    # sheet 1
    data['office'] = office_rc.name
    data['ccy'] = office_rc.ccy.code
    data['dateFrom'] = '-' if isNullBlank(incurrence_date_from) else incurrence_date_from
    data['dateTo'] = '-' if isNullBlank(incurrence_date_to) else incurrence_date_to
    data['reporter'] = UserManager.getUser(operator_id).usr_nm
    data['reportDate'] = rptDate
    data['expenseTable'] = redcordsets2List(expense_table,
                                            ["incur_dt", "dsc", "cat__cat", "ccy__code", "amt", "ex_rate", "amt_calculated", "prj_nm", "hdr__payment_tp__tp", "trn_ref", "claimer_nm", "hdr__sn", "file__seq"])
    # sheet 2
    data['echequeFileListTable'] = redcordsets2List(e_cheque_table, ["row_no", "sn", "echeque_file_nm", "type", "ref_expense_no"])

    filename = 'ES101-%s-%s.%s' % (office_rc.code, rptDate.strftime('%Y%m%d%H%M%S'), ikfs.getFileExtension(template_file))
    exportFolder = ESFile.getTempFolder('es101-rpt1')
    outputFile = Path(os.path.join(exportFolder, filename))
    sw = SpreadsheetWriter(parameters=data, templateFile=template_file, outputFile=outputFile)
    b = sw.write()
    if not b.value:
        logger.error(b.dataStr)
        raise IkValidateException(b.dataStr)

    e_cheque_table.sort(key=lambda x: x['incur_dt'])
    if isNullBlank(incurrence_date_from):
        date_from_list = []
        date_from_list.append(__to_datetime(expense_table[0]['incur_dt'])) if len(expense_table) > 0 else None
        date_from_list.append(e_cheque_table[0]['incur_dt']) if len(e_cheque_table) > 0 else None
        incurrence_date_from = min(date_from_list).strftime("%Y-%m-%d")
    if isNullBlank(incurrence_date_to):
        date_to_list = []
        date_to_list.append(__to_datetime(expense_table[0]['incur_dt'])) if len(expense_table) > 0 else None
        date_to_list.append(e_cheque_table[-1]['incur_dt']) if len(e_cheque_table) > 0 else None
        incurrence_date_to = max(date_to_list).strftime("%Y-%m-%d")
    return outputFile, incurrence_date_from, incurrence_date_to


def __to_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"String '{value}' is not a recognized datetime format")
    raise TypeError(f"Unsupported type for datetime conversion: {type(value)}")
