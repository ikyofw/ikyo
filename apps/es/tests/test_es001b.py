from django.test import RequestFactory
from unittest.mock import MagicMock
from core.models import UserOffice
from .test_es_base import ESTestCase
from ..models import UserWorkOffice, Payee
from ..views.es001b_views import ES001B


class ES001BTestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES001B()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        mock_fg = MagicMock()
        mock_fg.configure_mock(name="payeeFg", editable=True, visible=True, groupType="table")
        mock_screen.fieldGroups = [mock_fg]
        self.view._screen = mock_screen
        self.view.request = MagicMock()

    def test_get_payee(self):
        payee_data = self.view.getPayeeRcs()
        self.assertEqual(list(payee_data), [])

        mock_payee_data = Payee(office=self.office_a, payee='test payee', bank_info='test info', rmk='test rmk')
        self.view._requestData = {'payeeFg': [mock_payee_data]}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])

        payee_data = self.view.getPayeeRcs()
        self.assertEqual(payee_data[0].office, self.office_a)
        self.assertEqual(payee_data[0].payee, 'test payee')
        self.assertEqual(payee_data[0].bank_info, 'test info')
        self.assertEqual(payee_data[0].rmk, 'test rmk')

    def test_get_yes_no(self):
        """Test the getYesNo method to ensure it returns the correct Yes/No values."""
        yes_no_data = self.view.getYesNo()
        expected = [
            {'value': 'N', 'display': 'No'},
            {'value': 'Y', 'display': 'Yes'}
        ]
        self.assertEqual(yes_no_data, expected)

    def test_is_administrator(self):
        """Test the isAdministrator method to verify user role detection."""
        # Mock as an admin user
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)
        self.assertTrue(self.view.isAdministrator())

        # Mock as a regular user
        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
        self.assertFalse(self.view.isAdministrator())

    def test_get_office_rcs_admin(self):
        """Test getOfficeRcs for admin user to ensure all offices are returned."""
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)
        office_list = self.view.getOfficeRcs()
        self.assertEqual(len(office_list), 4)

    def test_get_office_rcs_regular_user(self):
        """Test getOfficeRcs for regular user to ensure only associated offices are returned."""
        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
        office_list = self.view.getOfficeRcs()
        self.assertEqual(len(office_list), 2)
        self.assertEqual(office_list[0]['name'], "Office A")
        self.assertEqual(office_list[1]['name'], "Office B")

    def test_set_current_office(self):
        """Test the _setCurrentOffice method to validate setting a valid or invalid office."""
        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)

        # Test setting a valid office
        result = self.view._setCurrentOffice(self.office_a.id)
        self.assertTrue(result.value)

        # Test setting an invalid office
        result = self.view._setCurrentOffice(999)
        self.assertFalse(result.value)
        self.assertEqual(result.data, "Office doesn't exist.")

    def test_get_current_office_id(self):
        """Test _getCurrentOfficeID method to ensure the correct office ID is returned."""
        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
        UserWorkOffice.objects.create(usr=self.regular_user1, office=self.office_a)

        # Mock current office and test retrieval of office ID
        self.view._getCurrentOffice = MagicMock(return_value=self.office_a)
        office_id = self.view._getCurrentOfficeID()
        self.assertEqual(office_id, self.office_a.id)

        # Test case with no current office
        self.view._getCurrentOffice = MagicMock(return_value=None)
        office_id = self.view._getCurrentOfficeID()
        self.assertIsNone(office_id)

    def test_get_current_office(self):
        """Test _getCurrentOffice method to validate current office retrieval logic."""
        self.view.getCurrentUser = MagicMock(return_value=self.regular_user1)
        current_office = self.view._getCurrentOffice()
        self.assertEqual(current_office, self.office_a)

        # Test scenario where no default office is available
        UserWorkOffice.objects.all().delete()
        UserOffice.objects.filter(usr=self.regular_user1, is_default='True').delete()
        current_office = self.view._getCurrentOffice()
        self.assertEqual(current_office, self.office_b)
