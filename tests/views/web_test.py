# -*- coding: utf-8 -*-
import mock

from webtest.app import AppError

import config
import logic
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee
from testing.factories import create_love
from testing.factories import create_subscription
from testing.util import LoggedInAdminBaseTest
from testing.util import LoggedInUserBaseTest
from testing.util import YelpLoveTestCase


class LoggedOutTest(YelpLoveTestCase):
    """
    Testing access to pages when no user is logged in.
    """
    nosegae_user = True
    nosegae_user_kwargs = dict(USER_EMAIL='')

    def test_homepage(self):
        self.assertRequiresLogin(self.app.get('/'))

    def test_me(self):
        self.assertRequiresLogin(self.app.get('/me'))

    def test_explore(self):
        self.assertRequiresLogin(self.app.get('/explore'))

    def test_user_shortcut(self):
        self.assertRequiresLogin(self.app.get('/johnd'))

    def test_leaderboard(self):
        self.assertRequiresLogin(self.app.get('/leaderboard'))

    def test_keys(self):
        self.assertRequiresLogin(self.app.get('/keys'))

    def test_autocomplete(self):
        self.assertRequiresLogin(self.app.get('/user/autocomplete'))

    def test_sent(self):
        self.assertRequiresLogin(self.app.get('/sent'))

    def test_create_key(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/keys/create',
                dict(
                    description='My API Key',
                    _csrf_token=csrf_token,
                ),
            ),
        )

    def test_post_love(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/love',
                dict(
                    recipients='jenny',
                    message='Love',
                    _csrf_token=csrf_token,
                ),
            ),
        )

    def test_subscriptions(self):
        self.assertRequiresLogin(self.app.get('/subscriptions'))

    def test_create_subscription(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/subscriptions/create',
                dict(
                    request_url='http://localhost.com/foo',
                    event='lovesent',
                    active='true',
                    secret='mysecret',
                    _csrf_token=csrf_token,
                ),
            ),
        )

    def test_delete_subscription(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/subscriptions/1/delete',
                dict(_csrf_token=csrf_token),
            ),
        )

    def test_listing_aliases(self):
        self.assertRequiresLogin(self.app.get('/aliases'))

    def test_create_alias(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/aliases',
                dict(
                    alias='johnny',
                    username='john',
                    _csrf_token=csrf_token,
                ),
            ),
        )

    def test_delete_alias(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/aliases/1/delete',
                dict(_csrf_token=csrf_token),
            ),
        )

    def test_employees(self):
        self.assertRequiresLogin(self.app.get('/employees'))

    def test_import_employees_form(self):
        self.assertRequiresLogin(self.app.get('/employees/import'))

    def test_import_employees(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresLogin(
            self.app.post(
                '/employees/import',
                dict(_csrf_token=csrf_token),
            )
        )


class AdminResourcesTest(LoggedInUserBaseTest):
    # Managing API Keys

    def test_keys(self):
        self.assertRequiresAdmin(
            self.app.get('/keys', expect_errors=True),
        )

    def test_create_key(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresAdmin(
            self.app.post(
                '/keys/create',
                dict(
                    description='My API Key',
                    _csrf_token=csrf_token,
                ),
                expect_errors=True,
            ),
        )

    # Managing Webhook Subscriptions
    def test_subscriptions(self):
        self.assertRequiresAdmin(
            self.app.get('/subscriptions', expect_errors=True),
        )

    def test_create_subscription(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresAdmin(
            self.app.post(
                '/subscriptions/create',
                dict(
                    request_url='http://localhost.com/foo',
                    event='lovesent',
                    active='true',
                    secret='mysecret',
                    _csrf_token=csrf_token,
                ),
                expect_errors=True,
            ),
        )

    def test_delete_subscription(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresAdmin(
            self.app.post(
                '/subscriptions/1/delete',
                dict(_csrf_token=csrf_token),
                expect_errors=True,
            ),
        )

    # Managing Aliases
    def test_aliases(self):
        self.assertRequiresAdmin(
            self.app.get('/aliases', expect_errors=True),
        )

    def test_create_alias(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresAdmin(
            self.app.post(
                '/aliases',
                dict(
                    alias='johnny',
                    username='john',
                    _csrf_token=csrf_token,
                ),
                expect_errors=True,
            ),
        )

    def test_delete_alias(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresAdmin(
            self.app.post(
                '/aliases/1/delete',
                dict(_csrf_token=csrf_token),
                expect_errors=True,
            ),
        )

    def test_employees(self):
        self.assertRequiresAdmin(
            self.app.get('/employees', expect_errors=True)
        )

    def test_import_employees_form(self):
        self.assertRequiresAdmin(
            self.app.get('/employees/import', expect_errors=True)
        )

    def test_import_employees(self):
        csrf_token = self.addCsrfTokenToSession()
        self.assertRequiresAdmin(
            self.app.post(
                '/employees/import',
                dict(_csrf_token=csrf_token),
                expect_errors=True,
            )
        )


class HomepageTest(LoggedInUserBaseTest):
    """
    Testing the homepage
    """

    def test_index(self):
        response = self.app.get('/')

        self.assertEqual(response.status_int, 200)
        self.assertIn('home.html', response.template)

        self.assertIsNotNone(response.context['current_time'])
        self.assertEqual(response.context['current_user'], self.current_user)
        self.assertIsNone(response.context['recipients'])
        self.assertHasCsrf(response.forms['send-love-form'], response.session)

    def test_index_with_recipient_and_message(self):
        response = self.app.get('/', dict(recipients='janedoe', message='hi'))

        self.assertEqual(response.context['recipients'], 'janedoe')
        self.assertEqual(
            response.forms['send-love-form'].get('recipients').value,
            'janedoe',
        )
        self.assertEqual(
            response.forms['send-love-form'].get('message').value,
            'hi',
        )
        self.assertHasCsrf(response.forms['send-love-form'], response.session)


class SentTest(LoggedInUserBaseTest):
    """
    Testing the sent page
    """

    def setUp(self):
        super(SentTest, self).setUp()
        self.recipient = create_employee(username='janedoe')

    def tearDown(self):
        self.recipient.key.delete()
        super(SentTest, self).tearDown()

    def test_missing_args_is_redirect(self):
        response = self.app.get('/sent')

        self.assertEqual(response.status_int, 302)

    def test_sent_with_args(self):
        response = self.app.get('/sent', dict(recipients='janedoe', message='hi', link_id='cn23sx'))
        self.assertIsNotNone(response.context['current_time'])
        self.assertEqual(response.context['current_user'], self.current_user)
        self.assertIsNotNone(response.context['loved'])
        self.assertEqual(response.context['url'], config.APP_BASE_URL + 'l/cn23sx')


class SendLoveTest(LoggedInUserBaseTest):

    def setUp(self):
        super(SendLoveTest, self).setUp()
        self.recipient = create_employee(username='jenny')

    def tearDown(self):
        self.recipient.key.delete()
        super(SendLoveTest, self).tearDown()

    @mock.patch('logic.love.send_loves', autospec=True)
    def test_send_love_without_csrf(self, mock_send_loves):
        response = self.app.post('/love', {'recipients': 'jenny', 'message': 'Love'}, expect_errors=True)

        self.assertEqual(response.status_int, 403)
        self.assertFalse(mock_send_loves.called)

    @mock.patch('logic.love.send_loves', autospec=True)
    def test_send_love(self, mock_send_loves):
        csrf_token = self.addCsrfTokenToSession()
        response = self.app.post('/love', {'recipients': 'jenny', 'message': 'Love', '_csrf_token': csrf_token})

        self.assertEqual(response.status_int, 302)
        mock_send_loves.assert_called_once_with(set([u'jenny']), u'Love', secret=False)


class MeTest(LoggedInUserBaseTest):
    """
    Testing /me
    """

    def test_me(self):
        response = self.app.get('/me')

        self.assertEqual(response.status_int, 200)
        self.assertIn('me.html', response.template)

        self.assertIsNotNone(response.context['current_time'])
        self.assertEqual(response.context['current_user'], self.current_user)
        self.assertEqual(response.context['sent_loves'], [])
        self.assertIn('Give and ye shall receive!', response.body)
        self.assertEqual(response.context['received_loves'], [])
        self.assertIn('You haven\'t sent any love yet.', response.body)

    def test_me_with_loves(self):
        dude = create_employee(username='dude')
        sent_love = create_love(
            sender_key=self.current_user.key,
            recipient_key=dude.key,
            message='Well done.'
        )
        received_love = create_love(
            sender_key=dude.key,
            recipient_key=self.current_user.key,
            message='Awesome work.'
        )
        response = self.app.get('/me')

        self.assertEqual(response.context['sent_loves'], [sent_love])
        self.assertIn('Well done.', response.body)
        self.assertEqual(response.context['received_loves'], [received_love])
        self.assertIn('Awesome work.', response.body)

        dude.key.delete()


class SubscriptionsTestCase(LoggedInAdminBaseTest):
    """
    Testing /subscriptions
    """

    def test_subscriptions(self):
        response = self.app.get('/subscriptions')

        self.assertEqual(response.status_int, 200)
        self.assertIn('subscriptions.html', response.template)

    @mock.patch('views.web.Subscription', autospec=True)
    def test_create_subscription(self, mock_model_subscription):
        csrf_token = self.addCsrfTokenToSession()
        response = self.app.post(
            '/subscriptions/create',
            dict(
                request_url='http://example.org',
                event='lovesent',
                active='true',
                secret='secret-sauce',
                _csrf_token=csrf_token,
            )
        )

        self.assertEqual(response.status_int, 302)
        mock_model_subscription.create_from_dict.assert_called_once_with(
            dict(
                request_url='http://example.org',
                event='lovesent',
                active=True,
                secret='secret-sauce',
            )
        )

    @mock.patch('views.web.logic.subscription', autospec=True)
    def test_deleting_alias(self, mock_logic_subscription):
        csrf_token = self.addCsrfTokenToSession()
        subscription = create_subscription()
        response = self.app.post(
            '/subscriptions/{id}/delete'.format(id=subscription.key.id()),
            dict(_csrf_token=csrf_token),
        )

        self.assertEqual(response.status_int, 302)
        mock_logic_subscription.delete_subscription.assert_called_once_with(subscription.key.id())


class AliasesTestCase(LoggedInAdminBaseTest):
    """
    Testing /aliases
    """

    def test_listing_aliases(self):
        response = self.app.get('/aliases')

        self.assertEqual(response.status_int, 200)
        self.assertIn('aliases.html', response.template)
        self.assertHasCsrf(response.forms['alias-form'], response.session)

    @mock.patch('views.web.logic.alias', autospec=True)
    def test_saving_alias(self, mock_logic_alias):
        create_employee(username='dude')
        csrf_token = self.addCsrfTokenToSession()

        response = self.app.post(
            '/aliases',
            {'alias': 'duden', 'username': 'dude', '_csrf_token': csrf_token},
        )

        self.assertEqual(response.status_int, 302)
        mock_logic_alias.save_alias.assert_called_once_with(
            'duden',
            'dude',
        )

    def test_saving_alias_all_empty(self):
        csrf_token = self.addCsrfTokenToSession()

        response = self.app.post(
            '/aliases',
            {'alias': '', 'username': '', '_csrf_token': csrf_token},
        )

        self.assertEqual(response.status_int, 302)
        self.assertIsNone(logic.alias.get_alias('foo'))

    @mock.patch('views.web.logic.alias', autospec=True)
    def test_deleting_alias(self, mock_logic_alias):
        create_employee(username='man')
        csrf_token = self.addCsrfTokenToSession()

        alias = create_alias_with_employee_username(name='mano', username='man')
        response = self.app.post(
            '/aliases/{id}/delete'.format(id=alias.key.id()),
            {'_csrf_token': csrf_token},
        )

        self.assertEqual(response.status_int, 302)
        mock_logic_alias.delete_alias.assert_called_once_with(alias.key.id())


class MeOrExploreTest(LoggedInUserBaseTest):
    """
    Testing redirect to /me or /explore?user=johnd
    """

    def test_no_such_employee(self):
        with self.assertRaises(AppError) as caught:
            self.app.get('/panda')

        self.assert_(
            caught.exception.message.startswith('Bad response: 404'),
            'Expected request for unknown employee to return 404',
        )

    def test_redirect_to_me(self):
        response = self.app.get('/{username}'.format(username=self.current_user.username))

        self.assertEqual(response.status_int, 302)
        self.assertIn('/me', response.location)

    def test_redirect_to_explore(self):
        create_employee(username='buddy')
        response = self.app.get('/buddy')

        self.assertEqual(response.status_int, 302)
        self.assertIn('/explore?user=buddy', response.location)

    def test_with_alias(self):
        create_employee(username='buddy')
        create_alias_with_employee_username(name='buddyalias', username='buddy')
        response = self.app.get('/buddyalias')

        self.assertEqual(response.status_int, 302)
        self.assertIn('/explore?user=buddy', response.location)


class LeaderboardTest(LoggedInUserBaseTest):
    """
    Testing /leaderboard
    """

    def test_leaderboard(self):
        response = self.app.get('/leaderboard')

        self.assertEqual(response.status_int, 200)
        self.assertIn('leaderboard.html', response.template)
        self.assertIsNotNone(response.context['top_loved'])
        self.assertIsNotNone(response.context['top_lovers'])
        self.assertIsNotNone(response.context['departments'])
        self.assertIsNotNone(response.context['sub_departments'])
        self.assertIsNone(response.context['selected_dept'])
        self.assertIsNotNone(response.context['selected_timespan'])


class ExploreTest(LoggedInUserBaseTest):
    """
    Testing /explore
    """

    def test_explore(self):
        response = self.app.get('/explore')

        self.assertEqual(response.status_int, 200)
        self.assertIn('explore.html', response.template)
        self.assertIsNotNone(response.context['current_time'])
        self.assertIsNone(response.context['user'])

    def test_explore_with_user(self):
        create_employee(username='buddy')
        response = self.app.get('/explore?user=buddy')

        self.assertEqual(response.status_int, 200)
        self.assertIn('explore.html', response.template)
        self.assertIsNotNone(response.context['current_time'])
        self.assertEqual('buddy', response.context['user'].username)

    def test_explore_with_unkown_user(self):
        response = self.app.get('/explore?user=noone')

        self.assertEqual(response.status_int, 302)
        self.assertIn('/explore', response.location)


class AutocompleteTest(LoggedInUserBaseTest):
    nosegae_memcache = True
    nosegae_search = True

    def setUp(self):
        super(AutocompleteTest, self).setUp()
        create_employee(username='alice')
        create_employee(username='alex')
        create_employee(username='bob')
        create_employee(username='carol')
        logic.employee.rebuild_index()

    def test_autocomplete(self):
        self._test_autocomplete('a', ['alice', 'alex'])
        self._test_autocomplete('b', ['bob'])
        self._test_autocomplete('c', ['carol'])
        self._test_autocomplete('stupidprefix', [])
        self._test_autocomplete('', [])

    def _test_autocomplete(self, prefix, expected_values):
        response = self.app.get('/user/autocomplete', {'term': prefix})
        received_values = set(item['value'] for item in response.json)
        self.assertEqual(set(expected_values), received_values)


class EmployeeTestCase(LoggedInAdminBaseTest):
    """
    Testing /employees
    """

    def test_employees(self):
        create_employee(username='buddy')
        response = self.app.get('/employees')

        self.assertEqual(response.status_int, 200)
        self.assertIn('employees.html', response.template)
        self.assertIsNotNone(response.context['pagination_result'])

    def test_employees_import_form(self):
        response = self.app.get('/employees/import')

        self.assertEqual(response.status_int, 200)
        self.assertIn('import.html', response.template)
        self.assertIsNotNone(response.context['import_file_exists'])
