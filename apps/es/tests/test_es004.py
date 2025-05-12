from django.test import RequestFactory
from unittest.mock import MagicMock

from core.core.http import IkJsonResponse
from core.view.screenView import _OPEN_SCREEN_PARAM_KEY_NAME
from es.views.es004_views import ES004
from .test_es_base import ESTestCase
from core.models import UserOffice, Currency
from ..models import ExpenseDetail, Expense, ExpenseCategory, DraftFile, File, Payee


class ES004TestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES004()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        mock_fg = MagicMock()
        mock_fg.configure_mock(name="expenseFg", editable=True, visible=True, groupType="table")
        mock_screen.fieldGroups = [mock_fg]
        self.view._screen = mock_screen
        self.view.request = MagicMock()
        
        self.payee = Payee.objects.create(id=1, office=self.office_a, payee='test payee', bank_info='test info', rmk='test rmk')

        self.ec1 = ExpenseCategory.objects.create(id=1, cat='test category 1', dsc='test remark 2')
        self.ec2 = ExpenseCategory.objects.create(id=2, cat='test category 2', dsc='test remark 2')

        self.file1 = File.objects.create(id=1, tp='invoice', seq='1', file_size=100, file_tp='JPG', file_nm='1.jpg', file_path='1/', office=self.office_a)
        self.draft_file1 = DraftFile.objects.create(id=1, tp='expense', claimer=self.admin_user, file=self.file1, office=self.office_a)

    def test_get_expense_rcs(self):
        fieldGroup = MagicMock()
        fieldGroup.configure_mock(name="expenseFg", recordSetName="expenseRcs", editable=True, visible=True, groupType="table")
        fieldGroup.isDetail = MagicMock(return_value=None)
        fieldGroup.parent.getFieldGroupLink = MagicMock(return_value=None)
        fieldGroup.parent.getRecordSet.return_value = MagicMock(
            distinct=False,
            modelNames="es.models.ExpenseDetail",
            name="expenseRcs",
            queryFields="*",
            queryLimit=None,
            queryOrder=None,
            queryWhere=None,
            rmk=None
        )
        mock_expense_data = ExpenseDetail(incur_dt='2025-01-09', dsc='test remark', cat_id='1', ccy_id='1', amt=10, file=self.file1)
        self.view._requestData = {'expenseFg': [mock_expense_data]}

        response = self.view.initScreenData(fieldGroup, None, 'expenseRcs', 'getExpenseRcs')
        self.assertEqual(response[0], True)
        self.assertEqual(response[1], {'data': [], 'cssStyle': None, 'paginatorDataAmount': None})

        response = self.view.saveExpense()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
        saved_expense = ExpenseDetail.objects.filter(incur_dt='2025-01-09', cat_id='1', ccy_id='1').first()
        self.assertIsNotNone(saved_expense)
        self.assertEqual(saved_expense.dsc, 'test remark')
        response = self.view.initScreenData(fieldGroup, None, 'catRcs', 'getCatRcs')
        self.assertEqual(response[0], True)
        self.assertEqual(response[1][0]['incur_dt'], '2025-01-09')
        self.assertEqual(response[1][0]['dsc'], 'test remark')
        self.assertEqual(response[1][0]['file_id'], 1)

    def test_submit(self):
        mock_expense_data = ExpenseDetail(incur_dt='2025-01-09', dsc='test remark', cat_id='1', ccy_id='1', amt=10, file=self.file1)
        self.view._requestData = {'expenseFg': [mock_expense_data]}
        response = self.view.saveExpense()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
        
        payment_data = {
            "id": "",
            "sts": "",
            "poNo": "test po",
            "payeeID": "1",
            "approverID": "1",
            "settleByPriorBalance": "N",
            "settleByPettyCash": "false",
            "settleByPriorBalanceCCY": "",
            "expenseDsc": "test dscription",
            "supportingDoc": ""
        }
        self.view._requestData = {'paymentFg': payment_data}

        response = self.view.submitExpense()
        self.assertIsInstance(response, IkJsonResponse)

        saved_expense = Expense.objects.filter(id=2).first()
        self.assertIsNotNone(saved_expense)
        self.assertEqual(saved_expense.sts, 'submitted')
        self.assertEqual(saved_expense.claim_amt, 10)
        self.assertEqual(saved_expense.claimer_id, self.admin_user.id)

        # mock_error_payee_data = PaymentMethod(tp='test payment payment payment payment payment payment payment payment payment payment payment', dsc='test remark')
        # self.view._requestData = {'catFg': [mock_error_payee_data]}

        # response = self.view._BIFSave()
        # self.assertIsInstance(response, IkJsonResponse)
        # self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
