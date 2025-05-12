from django.test import RequestFactory
from unittest.mock import MagicMock
from core.models import UserOffice
from core.core.http import IkJsonResponse
from .test_es_base import ESTestCase
from ..models import UserWorkOffice, PaymentMethod
from ..views.es001a_views import ES001A


class ES001ATestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES001A()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        mock_fg = MagicMock()
        mock_fg.configure_mock(name="pmTable", editable=True, visible=True, groupType="table")
        mock_screen.fieldGroups = [mock_fg]
        self.view._screen = mock_screen
        self.view.request = MagicMock()

    def test_get_model_data(self):
        fieldGroup = MagicMock()
        fieldGroup.configure_mock(name="pmTable", recordSetName="pmRcs", editable=True, visible=True, groupType="table")
        fieldGroup.isDetail = MagicMock(return_value=None)
        fieldGroup.parent.getFieldGroupLink = MagicMock(return_value=None)
        fieldGroup.parent.getRecordSet.return_value = MagicMock(
            distinct=False,
            modelNames="es.models.PaymentMethod",
            name="pmRcs",
            queryFields="*",
            queryLimit=None,
            queryOrder="tp",
            queryWhere=None,
            rmk=None
        )
        mock_payment_method_data = PaymentMethod(tp='test payment thod', dsc='test remark')
        self.view._requestData = {'pmTable': [mock_payment_method_data]}

        response = self.view.initScreenData(fieldGroup, None, 'pmRcs', 'getPmRcs')
        self.assertEqual(response[0], True)
        self.assertEqual(response[1], [])

        response = self.view._BIFSave()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
        saved_payment_method = PaymentMethod.objects.filter(tp='test payment thod').first()
        self.assertIsNotNone(saved_payment_method)
        self.assertEqual(saved_payment_method.dsc, 'test remark')
        response = self.view.initScreenData(fieldGroup, None, 'pmRcs', 'getPmRcs')
        self.assertEqual(response[0], True)
        self.assertEqual(response[1][0]['tp'], 'test payment thod')
        self.assertEqual(response[1][0]['dsc'], 'test remark')

    def test_save(self):
        mock_pm_data = PaymentMethod(tp='test payment thod', dsc='test remark')
        self.view._requestData = {'pmTable': [mock_pm_data]}

        response = self.view._BIFSave()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
        saved_payment_method = PaymentMethod.objects.filter(tp='test payment thod').first()
        self.assertIsNotNone(saved_payment_method)
        self.assertEqual(saved_payment_method.dsc, 'test remark')

        # mock_error_payee_data = PaymentMethod(tp='test payment payment payment payment payment payment payment payment payment payment payment', dsc='test remark')
        # self.view._requestData = {'pmTable': [mock_error_payee_data]}

        # response = self.view._BIFSave()
        # self.assertIsInstance(response, IkJsonResponse)
        # self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])

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
