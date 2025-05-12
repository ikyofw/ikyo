from django.test import RequestFactory
from unittest.mock import MagicMock
from core.models import UserOffice
from .test_es_base import ESTestCase
from ..models import UserWorkOffice, PettyCashExpenseAdmin, Payee
from ..views.es001e_views import ES001E


class ES001DTestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES001E()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        mock_fg = MagicMock()
        mock_fg.configure_mock(name="pettyAdminFg", editable=True, visible=True, groupType="table")
        mock_screen.fieldGroups = [mock_fg]
        self.view._screen = mock_screen
        self.view.request = MagicMock()

        self.payee1 = Payee.objects.create(
            office=self.office_a, payee='test payee', bank_info='test info', rmk='test rmk'
        )

    def test_get_petty_admin(self):
        petty_admin_data = self.view.getPettyAdminRcs()
        self.assertEqual(list(petty_admin_data), [])

        mock_petty_cash_expense_admin_data = PettyCashExpenseAdmin(office=self.office_a, admin_id=self.admin_user.usr_nm,
                                                                   admin_payee_id=self.payee1.payee, max_amt=10, enable=True, rmk="test rmk")
        self.view._requestData = {'pettyAdminFg': [mock_petty_cash_expense_admin_data]}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])

        petty_admin_data = self.view.getPettyAdminRcs()
        self.assertEqual(petty_admin_data[0].office, self.office_a)
        self.assertEqual(petty_admin_data[0].admin_id, self.admin_user.usr_nm)
        self.assertEqual(petty_admin_data[0].admin_payee_id, self.payee1.payee)
        self.assertEqual(petty_admin_data[0].max_amt, 10)
        self.assertEqual(petty_admin_data[0].rmk, 'test rmk')

    def test_save(self):
        petty_admin_data = self.view.getPettyAdminRcs()
        self.assertEqual(list(petty_admin_data), [])

        mock_pett_data = PettyCashExpenseAdmin(office=self.office_a, admin_id=self.admin_user.usr_nm,
                                                                   admin_payee_id='error payee', max_amt=10, enable=True, rmk="test rmk")
        self.view._requestData = {'pettyAdminFg': [mock_pett_data]}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'error', 'message': 'Payee [error payee] doesn\'t exist. Please check office [Office A].'}])

        mock_pett_data = [PettyCashExpenseAdmin(office=self.office_a, admin_id=self.admin_user.usr_nm, admin_payee_id=self.payee1.payee, max_amt=10, enable=True, rmk="test rmk"),
                          PettyCashExpenseAdmin(office=self.office_a, admin_id=self.admin_user.usr_nm, admin_payee_id=self.payee1.payee, max_amt=10, enable=True, rmk="test rmk")]
        self.view._requestData = {'pettyAdminFg': mock_pett_data}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'error', 'message': 'Petty Admin is unique. Please check office [Office A], administrator [admin].'}])


    # def test_get_yes_no(self):
    #     """Test the getYesNo method to ensure it returns the correct Yes/No values."""
    #     yes_no_data = self.view.getYesNo()
    #     expected = [
    #         {'value': 'N', 'display': 'No'},
    #         {'value': 'Y', 'display': 'Yes'}
    #     ]
    #     self.assertEqual(yes_no_data, expected)

    # def test_is_administrator(self):
    #     """Test the isAdministrator method to verify user role detection."""
    #     # Mock as an admin user
    #     self.view.getCurrentUser = MagicMock(return_value=self.admin_user)
    #     self.assertTrue(self.view.isAdministrator())

    #     # Mock as a regular user
    #     self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
    #     self.assertFalse(self.view.isAdministrator())

    # def test_get_office_rcs_admin(self):
    #     """Test getOfficeRcs for admin user to ensure all offices are returned."""
    #     self.view.getCurrentUser = MagicMock(return_value=self.admin_user)
    #     office_list = self.view.getOfficeRcs()
    #     self.assertEqual(len(office_list), 4)

    # def test_get_office_rcs_regular_user(self):
    #     """Test getOfficeRcs for regular user to ensure only associated offices are returned."""
    #     self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
    #     office_list = self.view.getOfficeRcs()
    #     self.assertEqual(len(office_list), 2)
    #     self.assertEqual(office_list[0]['name'], "Office A")
    #     self.assertEqual(office_list[1]['name'], "Office B")

    # def test_set_current_office(self):
    #     """Test the _setCurrentOffice method to validate setting a valid or invalid office."""
    #     self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)

    #     # Test setting a valid office
    #     result = self.view._setCurrentOffice(self.office_a.id)
    #     self.assertTrue(result.value)

    #     # Test setting an invalid office
    #     result = self.view._setCurrentOffice(999)
    #     self.assertFalse(result.value)
    #     self.assertEqual(result.data, "Office doesn't exist.")

    # def test_get_current_office_id(self):
    #     """Test _getCurrentOfficeID method to ensure the correct office ID is returned."""
    #     self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
    #     UserWorkOffice.objects.create(usr=self.regular_user1, office=self.office_a)

    #     # Mock current office and test retrieval of office ID
    #     self.view._getCurrentOffice = MagicMock(return_value=self.office_a)
    #     office_id = self.view._getCurrentOfficeID()
    #     self.assertEqual(office_id, self.office_a.id)

    #     # Test case with no current office
    #     self.view._getCurrentOffice = MagicMock(return_value=None)
    #     office_id = self.view._getCurrentOfficeID()
    #     self.assertIsNone(office_id)

    # def test_get_current_office(self):
    #     """Test _getCurrentOffice method to validate current office retrieval logic."""
    #     self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
    #     current_office = self.view._getCurrentOffice()
    #     self.assertEqual(current_office, self.office_a)

    #     # Test scenario where no default office is available
    #     UserWorkOffice.objects.all().delete()
    #     UserOffice.objects.filter(usr=self.regular_user1, is_default='True').delete()
    #     current_office = self.view._getCurrentOffice()
    #     self.assertEqual(current_office, self.office_b)
