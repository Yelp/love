# -*- coding: utf-8 -*-
import mock

from testing.factories.employee import create_employee
from testing.factories.love import create_love
from testing.util import LoggedInAdminBaseTest


class EmailLoveTestCase(LoggedInAdminBaseTest):

    def setUp(self):
        self.sender = create_employee(username='john')
        self.recipient = create_employee(username='jenny')
        self.love = create_love(
            sender_key=self.sender.key,
            recipient_key=self.recipient.key,
            message='Love!'
        )

    def tearDown(self):
        self.love.key.delete()
        self.recipient.key.delete()
        self.sender.key.delete()

    @mock.patch('logic.love.send_love_email', autospec=True)
    def test_send_love_email(self, mock_send_email):  # noqa
        response = self.app.post(
            '/tasks/love/email',
            {'id': self.love.key.id()},
        )

        assert response.status_int == 200
        mock_send_email.assert_called_once_with(self.love)


class LoadEmployeesTestCase(LoggedInAdminBaseTest):

    @mock.patch('google.appengine.api.taskqueue.add', autospec=True)
    @mock.patch('logic.employee.load_employees', autospec=True)
    def test_load_employees_from_s3(self, mock_load_employees, mock_taskqueue_add):  # noqa
        response = self.app.get('/tasks/employees/load/s3')

        assert response.status_int == 200
        assert mock_load_employees.call_count == 1
        mock_taskqueue_add.assert_called_once_with(url='/tasks/love_count/rebuild')

    @mock.patch('google.appengine.api.taskqueue.add', autospec=True)
    @mock.patch('logic.employee.load_employees_from_csv', autospec=True)
    def test_load_employees_from_csv(self, mock_load_employees_from_csv, mock_taskqueue_add):  # noqa
        response = self.app.post('/tasks/employees/load/csv')

        assert response.status_int == 200
        assert mock_load_employees_from_csv.call_count == 1
        mock_taskqueue_add.assert_called_once_with(url='/tasks/love_count/rebuild')
