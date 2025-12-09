import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import RequestFactory

from core.core.exception import IkValidateException
from core.core.lang import Boolean2
from core.models import User
from es.core.status import Status
from es.models import *

from ..views.es006 import ES006
from .test_es_base import ESTestCase


class TestES006Views(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES006()

        mock_screen = MagicMock()
        # self.view._screen = mock_screen
        self.view.request = MagicMock()

        self.status = Status
        self.claimer_rc = User.objects.create(id=100, usr_nm="Claimer 1")
        self.approver_rc = User.objects.create(id=101, usr_nm="Approver 1")
        self.ccy_rc = self.currency_usd
        self.office_rc = self.office_a
        self.claimer_office_rc = UserOffice.objects.create(usr=self.claimer_rc, office=self.office_rc, seq=1, is_default=True)

    @patch('es.core.CA.submit_cash_advancement')  # Mock `submit_cash_advancement`
    @patch('es.models.CashAdvancement.objects.filter')  # Mock filter
    def test_submit_success(self, mock_filter, mock_submit_cash_advancement):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc
        )

        # Mock `filter` return
        mock_filter.return_value.first.return_value = mock_cash_adv

        # Mock `submit_cash_advancement` return
        mock_submit_cash_advancement.return_value = MagicMock(value=True, data=1000)

        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
        self.view._getRequestValue = MagicMock(return_value=mock_cash_adv)
        self.view._getCurrentOfficeID = MagicMock(return_value=self.office_rc.id)
        self.view._getCurrentOffice = MagicMock(return_value=self.office_rc)
        self.view.getCurrentUserId = MagicMock(return_value=self.claimer_rc.id)

        response = json.loads(self.view.submit().content)

        self.assertEqual(response['code'], 1)
        self.assertEqual(response['messages'][0]['message'], "Cash advancement [CA2025001] submitted.")

        # validate `submit_cash_advancement` has been called
        mock_submit_cash_advancement.assert_called_once_with(
            self.claimer_rc.id, mock_cash_adv.id, mock_cash_adv.office, mock_cash_adv.ccy, mock_cash_adv.payee,
            mock_cash_adv.dsc, mock_cash_adv.claim_amt, mock_cash_adv.po_no, mock_cash_adv.approver
        )

        # validate `filter`
        mock_filter.assert_called_once_with(id=1000)

    @patch('es.core.CA.submit_cash_advancement')  # Mock submit
    @patch('es.models.CashAdvancement.objects.filter')
    def test_submit_invalid_office(self, mock_filter, mock_submit_cash_advancement):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_b,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc
        )

        # Mock getRequestValue return
        self.view._getRequestValue = MagicMock(return_value=mock_cash_adv)

        # Mock current Office is office_a，different with mock_cash_adv.office
        self.view._getCurrentOfficeID = MagicMock(return_value=self.office_rc.id)
        self.view._getCurrentOffice = MagicMock(return_value=self.office_rc)

        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
        self.view._getRequestValue = MagicMock(return_value=mock_cash_adv)
        self.view.getCurrentUserId = MagicMock(return_value=self.claimer_rc.id)

        with self.assertRaises(IkValidateException) as context:
            self.view.submit()

        # validate except
        expected_message = "The office [Office B] is not the same as the current office [Office A]. Please check."
        self.assertIn(expected_message, str(context.exception))

        mock_submit_cash_advancement.assert_not_called()
        mock_filter.assert_not_called()

    @patch('es.core.CA.cancel_cash_advancement')  # Mock `cancel_cash_advancement`
    def test_cancel(self, mock_cancel_cash_advancement):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc,
            sts=self.status.SUBMITTED.value,
            action_rmk="Cancel reason",
        )

        # Mock `getRequestData` return
        self.view.getRequestData = MagicMock(return_value={'dtlFg': mock_cash_adv})
        self.view.getCurrentUserId = MagicMock(return_value=self.claimer_rc.id)

        # Mock `cancel_cash_advancement` return
        mock_cancel_cash_advancement.return_value = Boolean2.TRUE("Cash advancement [CA2025001] has been cancelled.")

        response = self.view.cancel()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Cash advancement [CA2025001] has been cancelled.")

        # validate `cancel_cash_advancement` has been called
        mock_cancel_cash_advancement.assert_called_once_with(
            self.claimer_rc.id, mock_cash_adv.id, mock_cash_adv.action_rmk
        )

    @patch('es.core.CA.reject_cash_advancement')  # Mock `reject_cash_advancement`
    def test_reject(self, mock_reject_cash_advancement):
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc,
            sts=self.status.SUBMITTED.value,
            action_rmk="Reject reason"
        )

        # Mock `getRequestData` return
        self.view.getRequestData = MagicMock(return_value={'dtlFg': mock_cash_adv})
        self.view.getCurrentUserId = MagicMock(return_value=self.approver_rc.id)

        mock_reject_cash_advancement.return_value = Boolean2.TRUE("Cash advancement [CA2025001] has been rejected.")

        response = self.view.reject()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Cash advancement [CA2025001] has been rejected.")

        # validate `reject_cash_advancement` has been called
        mock_reject_cash_advancement.assert_called_once_with(
            self.approver_rc.id, mock_cash_adv.id, mock_cash_adv.action_rmk
        )

    @patch('es.core.CA.approve_cash_advancement')  # Mock `approve_cash_advancement`
    def test_approve(self, mock_approve_cash_advancement):
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc,
            sts=self.status.REJECTED.value)

        # Mock `getRequestData` return
        self.view.getRequestData = MagicMock(return_value={'dtlFg': mock_cash_adv})
        self.view.getCurrentUserId = MagicMock(return_value=self.approver_rc.id)

        # Mock `approve_cash_advancement` return
        mock_approve_cash_advancement.return_value = Boolean2.TRUE("Cash advancement [CA2025001] has been approved.")

        response = self.view.approve()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Cash advancement [CA2025001] has been approved.")

        # validate `approve_cash_advancement` has been called
        mock_approve_cash_advancement.assert_called_once_with(
            self.approver_rc.id, mock_cash_adv.id
        )

    @patch('es.core.CA.pay_cash_advancement')
    @patch('es.core.ESFile.save_uploaded_really_file')
    @patch('es.models.CashAdvancement.objects.filter')
    def test_paid_success(self, mock_filter, mock_save_file, mock_pay_cash_advancement):
        # Mock file path
        uploaded_file_path = Path("/path/to/uploaded/file")
        mock_save_file.return_value = uploaded_file_path

        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc,
            sts=self.status.APPROVED.value,
            payment_tp="Bank Transfer",
            payment_number="123456",
            action_rmk="Payment remarks",
            payment_record_file=MagicMock(id=10)
        )
        mock_filter.return_value.first.return_value = mock_cash_adv

        # Mock upload file
        mock_file = MagicMock(name="uploaded_file")
        mock_request_data = MagicMock()
        mock_request_data.getFiles.return_value = [mock_file]
        mock_request_data.get.return_value = mock_cash_adv

        mock_pay_cash_advancement.return_value = Boolean2.TRUE("Cash advancement [CA2025001] has been paid")

        # Mock getSessionParameterInt return
        self.view.getSessionParameterInt = MagicMock(return_value=1000)

        self.view.getRequestData = MagicMock(return_value=mock_request_data)
        self.view.getCurrentUserId = MagicMock(return_value=123)
        self.view.setSessionParameter = MagicMock()

        response = self.view.paid()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Cash advancement [CA2025001] has been paid")

        mock_pay_cash_advancement.assert_called_once_with(
            123,
            mock_cash_adv.id,
            mock_cash_adv.payment_tp,
            mock_cash_adv.payment_number,
            uploaded_file_path,
            mock_cash_adv.action_rmk
        )

        mock_save_file.assert_called_once_with(
            mock_file,
            self.view.__class__.__name__,
            self.view.getCurrentUserName()
        )

        self.view.setSessionParameter.assert_called_once_with(
            self.view.SESSION_KEY_FILE_ID,
            mock_cash_adv.payment_record_file.id
        )

    @patch('es.models.CashAdvancement.objects.filter')  # Mock filter
    def test_paid_no_file_uploaded(self, mock_filter):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc,
            sts=self.status.APPROVED.value,
            payment_tp="Bank Transfer",
            payment_number="123456",
            action_rmk="Payment remarks",
            payment_record_file=MagicMock(id=10)
        )
        mock_filter.return_value.first.return_value = mock_cash_adv

        # Mock upload file is null
        mock_request_data = MagicMock()
        mock_request_data.getFiles.return_value = None
        mock_request_data.get.return_value = mock_cash_adv

        # Mock getRequestData
        self.view.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock getSessionParameterInt return
        self.view.getSessionParameterInt = MagicMock(return_value=1000)

        response = json.loads(self.view.paid().content)

        self.assertEqual(response['code'], 0)
        self.assertEqual(response['messages'][0]['message'], "Please select a file to upload.")

        # validate CashAdvancement has been called
        mock_filter.assert_called_once_with(id=1000)

    @patch('es.models.CashAdvancement.objects.filter')  # Mock filter
    def test_paid_invalid_payment_type(self, mock_filter):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            ccy=self.ccy_rc,
            office=self.office_rc,
            payee=MagicMock(name="Payee A"),
            dsc="Test Description",
            po_no="PO12345",
            claim_amt=100.0,
            approver=self.approver_rc,
            sts=self.status.APPROVED.value,
            payment_tp=None,  # Invalid payment type
            payment_number="123456",
            action_rmk="Payment remarks",
            payment_record_file=MagicMock(id=10)
        )
        mock_filter.return_value.first.return_value = mock_cash_adv

        # Mock upload file
        mock_file = MagicMock()
        mock_request_data = MagicMock()
        mock_request_data.getFiles.return_value = [mock_file]
        mock_request_data.get.return_value = mock_cash_adv

        # Mock getRequestData
        self.view.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock getSessionParameterInt return
        self.view.getSessionParameterInt = MagicMock(return_value=1000)

        response = self.view.paid()

        self.assertFalse(response.value)
        self.assertEqual(response.dataStr, "Please select a Transaction Type.")

        # validate CashAdvancement has been called
        mock_filter.assert_called_once_with(id=1000)

    @patch('es.core.CA.revert_paid_cash_advancement')
    def test_revert_paid_payment_success(self, mock_revert_paid_cash_advancement):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            action_rmk="Revert reason"
        )

        # Mock getRequestData return
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_cash_adv
        self.view.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user id
        self.view.getCurrentUserId = MagicMock(return_value=123)

        # Mock revert_paid_cash_advancement
        mock_revert_paid_cash_advancement.return_value = Boolean2.TRUE("Reverted successfully")

        # Mock deleteSessionParameters
        self.view.deleteSessionParameters = MagicMock()

        response = self.view.revertPaidPayment()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Reverted successfully")

        # validate CA.revert_paid_cash_advancement has been called
        mock_revert_paid_cash_advancement.assert_called_once_with(123, 1000, "Revert reason")

        # validate deleteSessionParameters has been called
        self.view.deleteSessionParameters.assert_called_once_with(self.view.SESSION_KEY_FILE_ID)

    @patch('es.core.CA.revert_paid_cash_advancement')
    def test_revert_paid_payment_failure(self, mock_revert_paid_cash_advancement):
        # Mock CashAdvancement
        mock_cash_adv = MagicMock(
            id=1000,
            sn="CA2025001",
            action_rmk="Revert reason"
        )

        # Mock getRequestData return
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_cash_adv
        self.view.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user ID
        self.view.getCurrentUserId = MagicMock(return_value=123)

        # Mock revert_paid_cash_advancement return failure
        mock_revert_paid_cash_advancement.return_value = Boolean2.FALSE("Revert failed")

        # Mock deleteSessionParameters
        self.view.deleteSessionParameters = MagicMock()

        response = self.view.revertPaidPayment()

        self.assertFalse(response.value)
        self.assertEqual(response.dataStr, "Revert failed")

        # validate CA.revert_paid_cash_advancement has been called
        mock_revert_paid_cash_advancement.assert_called_once_with(123, 1000, "Revert reason")

        # validate deleteSessionParameters has been called
        self.view.deleteSessionParameters.assert_not_called()

    @patch('es.core.CA.settle_paid_cash_advancement')
    def test_settle_success(self, mock_settle_paid_cash_advancement):
        # Mock Expense
        mock_expense = MagicMock(
            id=1000
        )

        # Mock getRequestData return
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_expense
        self.view.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user ID
        self.view.getCurrentUserId = MagicMock(return_value=123)

        # Mock settle_paid_cash_advancement return
        mock_settle_paid_cash_advancement.return_value = Boolean2.TRUE("Settle successful")

        response = self.view.settle()

        self.assertTrue(response.value)
        self.assertEqual(response.dataStr, "Settle successful")

        # validate CA.settle_paid_cash_advancement has been called
        mock_settle_paid_cash_advancement.assert_called_once_with(123, 1000)

    @patch('es.core.CA.settle_paid_cash_advancement')
    def test_settle_failure(self, mock_settle_paid_cash_advancement):
        # Mock Expense
        mock_expense = MagicMock(
            id=1000
        )

        # Mock getRequestData
        mock_request_data = MagicMock()
        mock_request_data.get.return_value = mock_expense
        self.view.getRequestData = MagicMock(return_value=mock_request_data)

        # Mock current user ID
        self.view.getCurrentUserId = MagicMock(return_value=123)

        # Mock settle_paid_cash_advancement return failure
        mock_settle_paid_cash_advancement.return_value = Boolean2.FALSE("Settle failed")

        response = self.view.settle()

        self.assertFalse(response.value)
        self.assertEqual(response.dataStr, "Settle failed")

        # validate CA.settle_paid_cash_advancement has been called
        mock_settle_paid_cash_advancement.assert_called_once_with(123, 1000)
