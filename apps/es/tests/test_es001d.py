from django.test import RequestFactory
from unittest.mock import MagicMock
from core.models import UserOffice
from .test_es_base import ESTestCase
from ..models import UserWorkOffice, Approver
from ..views.es001d_views import ES001D


class ES001DTestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES001D()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        mock_fg = MagicMock()
        mock_fg.configure_mock(name="approverFg", editable=True, visible=True, groupType="table")
        mock_screen.fieldGroups = [mock_fg]
        self.view._screen = mock_screen
        self.view.request = MagicMock()

    def test_get_approver(self):
        approver_data = self.view.getApproverRcs()
        self.assertEqual(list(approver_data), [])

        mock_approver_data = Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant=self.regular_user1, rmk="test rmk")
        self.view._requestData = {'approverFg': [mock_approver_data]}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])

        approver_data = self.view.getApproverRcs()
        self.assertEqual(approver_data[0].office, self.office_a)
        self.assertEqual(approver_data[0].approver_id, self.admin_user.usr_nm)
        self.assertEqual(approver_data[0].approver_assistant_id, self.regular_user1.usr_nm)
        self.assertEqual(approver_data[0].rmk, 'test rmk')

    def test_save(self):
        approver_data = self.view.getApproverRcs()
        self.assertEqual(list(approver_data), [])

        mock_approver_data = [Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant=self.regular_user1, rmk="test rmk"),
                              Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant=self.regular_user1, rmk="test rmk")]
        self.view._requestData = {'approverFg': mock_approver_data}
        response = self.view._BIFSave()
        self.assertEqual(
            response.messages,
            [{'type': 'error', 'message': 'Approver is unique in an office. Plelse check office [Office A]. Approver [admin], approver group [].'}]
        )
        
        mock_approver_data = [Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant_id=self.admin_user.usr_nm, rmk="test rmk")]
        self.view._requestData = {'approverFg': mock_approver_data}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'error', 'message': 'Approver Assistant cannot the same as Approver. Plelse check approver [admin].'}])

        mock_approver_data = [Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant_id=self.regular_user1.usr_nm,
                                       approver2_id=self.admin_user.usr_nm, rmk="test rmk")]
        self.view._requestData = {'approverFg': mock_approver_data}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [{'type': 'error', 'message': 'The 2nd Approver [admin] Cannot be the same as the first approver. Please check.'}])

        mock_approver_data = [Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant_id=self.regular_user1.usr_nm,
                                       approver2_min_amount=-1, rmk="test rmk")]
        self.view._requestData = {'approverFg': mock_approver_data}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [
                         {'type': 'error', 'message': 'The second approver\'s minimum approved limit should be empty when the second approver is blank. Please check approver [admin] in office [Office A].'}])

        mock_approver_data = [Approver(office=self.office_a, approver_id=self.admin_user.usr_nm, approver_assistant_id=self.regular_user1.usr_nm,
                                       approver2_id=self.regular_user1.usr_nm, approver2_min_amount=-1, rmk="test rmk")]
        self.view._requestData = {'approverFg': mock_approver_data}
        response = self.view._BIFSave()
        self.assertEqual(response.messages, [
                         {'type': 'error', 'message': 'The second approver\'s minimum approved limit should be greater than 0. Please check the second approver [johndoe] in office [Office A].'}])

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
