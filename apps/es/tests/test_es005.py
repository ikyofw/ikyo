from pathlib import Path
from django.test import RequestFactory
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from core.core.http import IkJsonResponse
from core.core.lang import Boolean2
from es.views.es004_views import ES004
from es.views.es005_views import ES005
from es.core.status import Status
from .test_es_base import ESTestCase
from core.models import UserOffice, Currency
from ..models import ExpenseDetail, Expense, ExpenseCategory, DraftFile, File, Payee


class ES005TestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view1 = ES004()
        self.view2 = ES005()
        self.view1.getCurrentUser = MagicMock(return_value=self.admin_user)
        self.view2.getCurrentUser = MagicMock(return_value=self.admin_user)
        
        self.view2.request = MagicMock()
        
        mock_screen1 = MagicMock()
        mock_screen2 = MagicMock()
        mock_fg1 = MagicMock()
        mock_fg1.configure_mock(name="expenseFg", editable=True, visible=True, groupType="table")
        mock_fg2 = MagicMock()
        mock_fg2.configure_mock(name="hdrListFg", editable=True, visible=True, groupType="table")
        mock_screen1.fieldGroups = [mock_fg1]
        mock_screen2.fieldGroups = [mock_fg2]
        mock_screen2.getFieldGroup = MagicMock(return_value=SimpleNamespace(
            pageSize=5,
            fields=[SimpleNamespace(dataField='claimer.usr_nm'), SimpleNamespace(dataField='approver.usr_nm'),
                    SimpleNamespace(dataField='payee.office.code'), SimpleNamespace(dataField='payee.payee')]
        ))
        self.view1._screen = mock_screen1
        self.view1.request = MagicMock()
        self.view2._screen = mock_screen2
        self.view2.request = MagicMock()

        self.payee = Payee.objects.create(id=1, office=self.office_a, payee='test payee', bank_info='test info', rmk='test rmk')

        self.ec1 = ExpenseCategory.objects.create(id=1, cat='test category 1', dsc='test remark 2')
        self.ec2 = ExpenseCategory.objects.create(id=2, cat='test category 2', dsc='test remark 2')

        self.file1 = File.objects.create(id=1, tp='invoice', seq='1', file_size=100, file_tp='JPG', file_nm='1.jpg', file_path='1/', office=self.office_a)
        self.draft_file1 = DraftFile.objects.create(id=1, tp='expense', claimer=self.admin_user, file=self.file1, office=self.office_a)

    def test_get_expense_rcs(self):
        mock_expense_data = ExpenseDetail(incur_dt='2025-01-09', dsc='test remark', cat_id='1', ccy_id='1', amt=10, file=self.file1)
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
        self.view1._requestData = {'expenseFg': [mock_expense_data], 'paymentFg': payment_data}
        self.view2._requestData = {'EditIndexField': 1, 'PAGEABLE_hdrListFg_pageNum': 10, 'hdrFg': SimpleNamespace(id='1', action_rmk='cancel remark')}
        
        response = self.view1.saveExpense()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])

        # submit
        response = self.view1.submitExpense()
        self.assertIsInstance(response, IkJsonResponse)
        submit_expense = Expense.objects.filter(id=1).first()
        self.assertIsNotNone(submit_expense)
        self.assertEqual(submit_expense.sts, 'submitted')
        self.assertEqual(submit_expense.claimer.id, 1)
        self.assertEqual(submit_expense.claim_amt, 10)

        # ES005 main table
        response = self.view2.getHdrRcs()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.data['data'][0]['sts'], 'submitted')
        self.assertEqual(response.data['data'][0]['claimer_id'], 1)
        self.assertEqual(response.data['data'][0]['claim_amt'], 10)
        
    @patch('es.core.ES.cancel_expense')
    def test_cancel(self, mock_cancel_expense):
        # Mock CashAdvancement
        mock_hdr = MagicMock(
            id=1,
            action_rmk="Cancel remark",
        )

        # Mock `getRequestData` return
        self.view2.getRequestData = MagicMock(return_value={'EditIndexField': 1, 'PAGEABLE_hdrListFg_pageNum': 10, 'hdrFg': mock_hdr})
        self.view2.getCurrentUserId = MagicMock(return_value=self.admin_user.id)
        
        # Mock `cancel_cash_advancement` return
        mock_cancel_expense.return_value = Boolean2.TRUE("Expense [ES2025001] has been cancelled.")

        self.view2.cancel()

        # self.assertTrue(response.value)
        self.assertEqual(self.view2._messages[0][1], "Expense [ES2025001] has been cancelled.")

        # validate `cancel_cash_advancement` has been called
        mock_cancel_expense.assert_called_once_with(
            self.admin_user.id, mock_hdr.id, mock_hdr.action_rmk
        )
        
    @patch('es.core.ES.reject_expense')
    def test_reject(self, mock_reject_expense):
        # Mock CashAdvancement
        mock_hdr = MagicMock(
            id=1,
            action_rmk="Reject remark",
        )

        # Mock `getRequestData` return
        self.view2.getRequestData = MagicMock(return_value={'EditIndexField': 1, 'PAGEABLE_hdrListFg_pageNum': 10, 'hdrFg': mock_hdr})
        self.view2.getCurrentUserId = MagicMock(return_value=self.admin_user.id)
        
        # Mock `cancel_cash_advancement` return
        mock_reject_expense.return_value = Boolean2.TRUE("Expense [ES2025001] has been rejected.")

        self.view2.reject()

        # self.assertTrue(response.value)
        self.assertEqual(self.view2._messages[0][1], "Expense [ES2025001] has been rejected.")

        # validate `cancel_cash_advancement` has been called
        mock_reject_expense.assert_called_once_with(
            self.admin_user.id, mock_hdr.id, mock_hdr.action_rmk
        )
        
    @patch('es.core.ES.approve_expense')
    def test_approve(self, mock_approve_expense):
        # Mock CashAdvancement
        mock_hdr = MagicMock(
            id=1,
            dsc="Approve description",
        )

        # Mock `getRequestData` return
        self.view2.getRequestData = MagicMock(return_value={'EditIndexField': 1, 'PAGEABLE_hdrListFg_pageNum': 10, 'hdrFg': mock_hdr})
        self.view2.getCurrentUserId = MagicMock(return_value=self.admin_user.id)
        self.view2.getSessionParameterInt = MagicMock(return_value=mock_hdr.id)
        
        # Mock `cancel_cash_advancement` return
        mock_approve_expense.return_value = Boolean2.TRUE("Expense [ES2025001] has been approved.")

        response = self.view2.approve()

        # self.assertTrue(response.value)
        self.assertEqual(response.messages[0]['message'], "Expense [ES2025001] has been approved.")

        # validate `cancel_cash_advancement` has been called
        mock_approve_expense.assert_called_once_with(
            self.admin_user.id, mock_hdr.id, mock_hdr.dsc
        )
        
    @patch('es.core.ES.pay_expense')
    @patch('es.core.ESFile.save_uploaded_really_file')
    @patch('es.models.Expense.objects.filter')
    def test_paid_success(self, mock_filter, mock_save_file, mock_pay_cash_advancement):
        # Mock file path
        uploaded_file_path = Path("/path/to/uploaded/file")
        mock_save_file.return_value = uploaded_file_path

        # Mock CashAdvancement
        mock_hdr = MagicMock(
            id=1000,
            payment_tp="Bank Transfer",
            payment_number="123456",
            action_rmk="Payment remarks",
            payment_record_file=MagicMock(id=10)
        )
        mock_filter.return_value.first.return_value = mock_hdr

        # Mock upload file
        mock_file = MagicMock(name="uploaded_file")
        mock_request_data = MagicMock()
        mock_request_data.getFiles.return_value = [mock_file]
        mock_request_data.get.return_value = mock_hdr

        mock_pay_cash_advancement.return_value = Boolean2.TRUE("Cash advancement [ES2025001] has been paid")

        # Mock getSessionParameterInt return
        self.view2.getSessionParameterInt = MagicMock(return_value=1000)

        self.view2.getRequestData = MagicMock(return_value=mock_request_data)
        self.view2.getCurrentUserId = MagicMock(return_value=self.admin_user.id)
        self.view2.setSessionParameter = MagicMock()

        response = self.view2.paid()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Cash advancement [ES2025001] has been paid")

        mock_pay_cash_advancement.assert_called_once_with(
            self.admin_user.id,
            mock_hdr.id,
            mock_hdr.payment_tp,
            mock_hdr.payment_number,
            uploaded_file_path,
            mock_hdr.action_rmk
        )

        mock_save_file.assert_called_once_with(
            mock_file,
            self.view2.__class__.__name__,
            self.view2.getCurrentUserName()
        )

        self.view2.setSessionParameter.assert_called_once_with(
            self.view2.SESSION_KEY_FILE_ID,
            mock_hdr.payment_record_file.id
        )
        
    @patch('es.core.ES.revert_paid_expense')
    def test_revert_paid_payment_success(self, mock_revert_paid_expense):
        # Mock CashAdvancement
        mock_hdr = MagicMock(
            id=1000,
            sn="ES2025001",
            action_rmk="Revert reason"
        )

        # Mock getRequestData return
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_hdr
        self.view2.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user id
        self.view2.getCurrentUserId = MagicMock(return_value=123)

        # Mock revert_paid_cash_advancement
        mock_revert_paid_expense.return_value = Boolean2.TRUE("Reverted successfully")

        # Mock deleteSessionParameters
        self.view2.deleteSessionParameters = MagicMock()

        response = self.view2.revertPaidPayment()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Reverted successfully")

        # validate ES.revert_paid_cash_advancement has been called
        mock_revert_paid_expense.assert_called_once_with(123, 1000, "Revert reason")

        # validate deleteSessionParameters has been called
        self.view2.deleteSessionParameters.assert_called_once_with(self.view2.SESSION_KEY_FILE_ID)
        
    @patch('es.core.ES.settle_paid_expense')
    def test_settle_success(self, mock_settle_paid_expense):
        # Mock Expense
        mock_expense = MagicMock(
            id=1000
        )

        # Mock getRequestData return
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_expense
        self.view2.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user ID
        self.view2.getCurrentUserId = MagicMock(return_value=123)

        # Mock settle_paid_cash_advancement return
        mock_settle_paid_expense.return_value = Boolean2.TRUE("Settle successful")

        response = self.view2.settle()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Settle successful")

        # validate ES.settle_paid_cash_advancement has been called
        mock_settle_paid_expense.assert_called_once_with(123, 1000)
        
    @patch('es.core.ES.settle_paid_expense')
    def test_settle_failure(self, mock_settle_paid_expense):
        # Mock Expense
        mock_expense = MagicMock(
            id=1000
        )

        # Mock getRequestData
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_expense
        self.view2.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user ID
        self.view2.getCurrentUserId = MagicMock(return_value=123)

        # Mock settle_paid_cash_advancement return failure
        mock_settle_paid_expense.return_value = Boolean2.FALSE("Settle failed")

        response = self.view2.settle()

        self.assertFalse(response.value)
        self.assertEqual(response.dataStr, "Settle failed")

        # validate ES.settle_paid_cash_advancement has been called
        mock_settle_paid_expense.assert_called_once_with(123, 1000)