from django.test import RequestFactory
from unittest.mock import MagicMock

from core.core.http import IkJsonResponse
from es.views.es002_views import ES002
from .test_es_base import ESTestCase
from core.models import Office, UserOffice
from ..models import UserWorkOffice


class ES002TestCase(ESTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.view = ES002()
        self.view.getCurrentUser = MagicMock(return_value=self.admin_user)

        mock_screen = MagicMock()
        self.view._screen = mock_screen
        self.view.request = MagicMock()

    def test_get_office_rcs(self):
        office_list = self.view.getOfficeRcs()
        self.assertEqual(len(office_list), 3)

    def test_save_method(self):
        mock_office_data = Office(id=1, name="test name")
        self.view._requestData = {'officeFg': mock_office_data}
        response = self.view.save()
        self.assertTrue(response)

        mock_office_data = Office()
        self.view._requestData = {'officeFg': mock_office_data}
        response = self.view.save()
        self.assertIsInstance(response, IkJsonResponse)
        self.assertEqual(response.messages, [{'type': 'error', 'message': 'Please select an office.'}])