from unittest.mock import MagicMock

from django.test import RequestFactory

from core.core.http import IkJsonResponse
from es.views.es003 import ES003

from ..models import PaymentMethod
from .test_es_base import ESTestCase


class ES003TestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES003()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        mock_fg = MagicMock()
        mock_fg.configure_mock(name="catFg", editable=True, visible=True, groupType="table")
        mock_screen.fieldGroups = [mock_fg]
        self.view._screen = mock_screen
        self.view.request = MagicMock()

    def test_get_model_data(self):
        fieldGroup = MagicMock()
        fieldGroup.configure_mock(name="catFg", recordSetName="catRcs", editable=True, visible=True, groupType="table")
        fieldGroup.isDetail = MagicMock(return_value=None)
        fieldGroup.parent.getFieldGroupLink = MagicMock(return_value=None)
        fieldGroup.parent.getRecordSet.return_value = MagicMock(
            distinct=False,
            modelNames="es.models.PaymentMethod",
            name="catRcs",
            queryFields="*",
            queryLimit=None,
            queryOrder="tp",
            queryWhere=None,
            rmk=None
        )
        mock_payment_method_data = PaymentMethod(tp='test payment thod', dsc='test remark')
        self.view._requestData = {'catFg': [mock_payment_method_data]}

        response = self.view.initScreenData(fieldGroup, None, 'catRcs', 'getCatRcs')
        self.assertEqual(response[0], True)
        self.assertEqual(response[1], [])

        response = self.view._BIFSave()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
        saved_payment_method = PaymentMethod.objects.filter(tp='test payment thod').first()
        self.assertIsNotNone(saved_payment_method)
        self.assertEqual(saved_payment_method.dsc, 'test remark')
        response = self.view.initScreenData(fieldGroup, None, 'catRcs', 'getCatRcs')
        self.assertEqual(response[0], True)
        self.assertEqual(response[1][0]['tp'], 'test payment thod')
        self.assertEqual(response[1][0]['dsc'], 'test remark')

    def test_save(self):
        mock_pm_data = PaymentMethod(tp='test payment thod', dsc='test remark')
        self.view._requestData = {'catFg': [mock_pm_data]}

        response = self.view._BIFSave()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
        saved_payment_method = PaymentMethod.objects.filter(tp='test payment thod').first()
        self.assertIsNotNone(saved_payment_method)
        self.assertEqual(saved_payment_method.dsc, 'test remark')

        # mock_error_payee_data = PaymentMethod(tp='test payment payment payment payment payment payment payment payment payment payment payment', dsc='test remark')
        # self.view._requestData = {'catFg': [mock_error_payee_data]}

        # response = self.view._BIFSave()
        # self.assertIsInstance(response, IkJsonResponse)
        # self.assertEqual(response.messages, [{'type': 'info', 'message': 'Saved.'}])
