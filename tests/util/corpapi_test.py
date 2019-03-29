import mock
import unittest
import base64

from util.corpapi import get_employees
from util.corpapi import get_employee_photo


class CoprApiTest(unittest.TestCase):

    @mock.patch('util.corpapi.requests')
    @mock.patch('util.corpapi.get_secret')
    @mock.patch('util.corpapi.config')
    def test_get_employees(self, mock_config, mock_get_secret, mock_requests):
        mock_get_secret.return_value = 'foo_key'
        mock_config.CORPAPI_BASE_URL = 'https://api.com/v1'
        mock_requests.get.return_value.json.return_value = [{'email': 'me@email.com'}]
        res = get_employees()
        mock_get_secret.assert_called_once_with('API_KEY')
        mock_requests.get.assert_called_once_with(
            'https://api.com/v1/employees',
            headers={
                'X-API-Key': 'foo_key',
            }
        )
        assert res == [{'email': 'me@email.com'}]

    @mock.patch('util.corpapi.requests')
    @mock.patch('util.corpapi.get_secret')
    @mock.patch('util.corpapi.config')
    def test_get_employee_photo(self, mock_config, mock_get_secret, mock_requests):
        alias = 'foo'
        encoded_image = base64.b64encode(b'I am encoded')
        mock_get_secret.return_value = 'foo_key'
        mock_config.CORPAPI_BASE_URL = 'https://api.com/v1'
        mock_requests.get.return_value.json.return_value = {'imagebase64': encoded_image}
        res = get_employee_photo(alias)
        mock_get_secret.assert_called_once_with('API_KEY')
        mock_requests.get.assert_called_once_with(
            'https://api.com/v1/photos/{}'.format(alias),
            headers={
                'X-API-Key': 'foo_key',
            }
        )
        assert res == base64.decodestring(encoded_image)
