# -*- coding: utf-8 -*-
from unittest import mock

import pytest
from webtest.app import AppError

import errors
import logic
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee
from testing.factories import create_love
from testing.factories import create_love_link
from testing.factories import create_subscription
from testing.util import LoggedInAdminBaseTest
from testing.util import LoggedInUserBaseTest
from testing.util import YelpLoveTestCase
from tests import conftest


class TestLoggedOut(YelpLoveTestCase):
    """
    Testing access to pages when no user is logged in.
    """

    def _assert_requires_login(self, app, url, method='get', data=None):
        request_func = getattr(app, method)
        args = [url]
        if data is not None:
            args.append(data)

        try:
            # the admin_required decorator will return a 401 response
            request_func(*args, expect_errors=True)
        except errors.NoSuchEmployee:
            pass

        assert conftest.mock_require_login_call_count == 1
        conftest.mock_require_login_call_count = 0

    def assert_get_requires_login(self, app, url):
        self._assert_requires_login(app, url)

    def assert_post_requires_login(self, app, url, data):
        csrf_token = self.add_csrf_token_to_session(app)
        data['_csrf_token'] = csrf_token
        self._assert_requires_login(app, url, method='post', data=data)

    def test_homepage(self, app):
        self.assert_get_requires_login(app, '/')

    def test_me(self, app):
        self.assert_get_requires_login(app, '/me')

    def test_explore(self, app):
        self.assert_get_requires_login(app, '/explore')

    def test_user_shortcut(self, app):
        self.assert_get_requires_login(app, '/johnd')

    def test_leaderboard(self, app):
        self.assert_get_requires_login(app, '/leaderboard')

    def test_keys(self, app):
        self.assert_get_requires_login(app, '/keys')

    def test_autocomplete(self, app):
        self.assert_get_requires_login(app, '/user/autocomplete')

    def test_sent(self, app):
        self.assert_get_requires_login(app, '/sent')

    def test_create_key(self, app):
        self.assert_post_requires_login(app, '/keys/create', {'description': 'My API Key'})

    def test_post_love(self, app):
        self.assert_post_requires_login(
            app, '/love', {'recipients': 'jenny', 'message': 'Love'},
        )

    def test_subscriptions(self, app):
        self.assert_get_requires_login(app, '/subscriptions')

    def test_create_subscription(self, app):
        self.assert_post_requires_login(
            app,
            '/subscriptions/create',
            {
                'request_url': 'http://localhost.com/foo',
                'event': 'lovesent',
                'active': 'true',
                'secret': 'mysecret',
            },
        )

    def test_delete_subscription(self, app):
        self.assert_post_requires_login(app, '/subscriptions/1/delete', {})

    def test_listing_aliases(self, app):
        self.assert_get_requires_login(app, '/aliases')

    def test_create_alias(self, app):
        self.assert_post_requires_login(app, '/aliases', {'alias': 'johnny', 'username': 'john'})

    def test_delete_alias(self, app):
        self.assert_post_requires_login(app, '/aliases/1/delete', {})

    def test_employees(self, app):
        self.assert_get_requires_login(app, '/employees')

    def test_import_employees_form(self, app):
        self.assert_get_requires_login(app, '/employees/import')

    def test_import_employees(self, app):
        self.assert_post_requires_login(app, '/employees/import', {})


class TestAdminResources(LoggedInUserBaseTest):
    # Managing API Keys

    def test_keys(self, app):
        self.assert_requires_admin(
            app.get('/keys', expect_errors=True),
        )

    def test_create_key(self, app):
        csrf_token = self.add_csrf_token_to_session(app)
        self.assert_requires_admin(
            app.post(
                '/keys/create',
                dict(
                    description='My API Key',
                    _csrf_token=csrf_token,
                ),
                expect_errors=True,
            ),
        )

    # Managing Webhook Subscriptions
    def test_subscriptions(self, app):
        self.assert_requires_admin(
            app.get('/subscriptions', expect_errors=True),
        )

    def test_create_subscription(self, app):
        csrf_token = self.add_csrf_token_to_session(app)
        self.assert_requires_admin(
            app.post(
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

    def test_delete_subscription(self, app):
        csrf_token = self.add_csrf_token_to_session(app)
        self.assert_requires_admin(
            app.post(
                '/subscriptions/1/delete',
                dict(_csrf_token=csrf_token),
                expect_errors=True,
            ),
        )

    # Managing Aliases
    def test_aliases(self, app):
        self.assert_requires_admin(
            app.get('/aliases', expect_errors=True),
        )

    def test_create_alias(self, app):
        csrf_token = self.add_csrf_token_to_session(app)
        self.assert_requires_admin(
            app.post(
                '/aliases',
                dict(
                    alias='johnny',
                    username='john',
                    _csrf_token=csrf_token,
                ),
                expect_errors=True,
            ),
        )

    def test_delete_alias(self, app):
        csrf_token = self.add_csrf_token_to_session(app)
        self.assert_requires_admin(
            app.post(
                '/aliases/1/delete',
                dict(_csrf_token=csrf_token),
                expect_errors=True,
            ),
        )

    def test_employees(self, app):
        self.assert_requires_admin(
            app.get('/employees', expect_errors=True)
        )

    def test_import_employees_form(self, app):
        self.assert_requires_admin(
            app.get('/employees/import', expect_errors=True)
        )

    def test_import_employees(self, app):
        csrf_token = self.add_csrf_token_to_session(app)
        self.assert_requires_admin(
            app.post(
                '/employees/import',
                dict(_csrf_token=csrf_token),
                expect_errors=True,
            )
        )


class TestHomepage(LoggedInUserBaseTest):
    """
    Testing the homepage
    """

    def test_index(self, app, mock_oidc, current_user):
        response = app.get('/')

        assert response.status_int == 200
        assert 'home.html' in response.template

        assert mock_oidc.require_login.call_count == 1
        assert response.context['current_time'] is not None
        assert response.context['current_user'] == current_user
        assert response.context['recipients'] is None
        self.assert_has_csrf(response.forms['send-love-form'], response.session)

    def test_index_with_recipient_and_message(self, app):
        response = app.get('/', dict(recipients='janedoe', message='hi'))

        assert response.context['recipients'] == 'janedoe'
        assert response.forms['send-love-form'].get('recipients').value == 'janedoe'
        assert response.forms['send-love-form'].get('message').value == 'hi'
        self.assert_has_csrf(response.forms['send-love-form'], response.session)


class TestSent(LoggedInUserBaseTest):
    """
    Testing the sent page
    """

    def test_missing_args_is_redirect(self, app):
        response = app.get('/sent')

        assert response.status_int == 302

    @mock.patch('views.web.config')
    def test_sent_with_args(self, mock_config, app, current_user, recipient):
        mock_config.APP_BASE_URL = 'http://foo.io/'

        response = app.get('/sent', dict(recipients='janedoe', message='hi', link_id='cn23sx'))
        assert response.context['current_time'] is not None
        assert response.context['current_user'] == current_user
        assert response.context['loved'] is not None
        assert response.context['url'] == 'http://foo.io/l/cn23sx'


class TestLoveLink(LoggedInUserBaseTest):
    """
    Testing the sent page
    """

    @pytest.fixture
    def love_link(self, recipient):
        link = create_love_link('lOvEr', 'i love you!', 'janedoe')
        yield link
        link.key.delete()

    def test_bad_hash(self, app):
        response = app.get('/l/badId')

        assert response.status_int == 302

    def test_good_hash(self, app, current_user, love_link):
        response = app.get('/l/lOvEr')
        assert response.context['current_time'] is not None
        assert response.context['current_user'] == current_user
        assert response.context['loved'] is not None
        assert response.context['recipients'] == 'janedoe'
        assert response.context['message'] == 'i love you!'
        assert response.context['link_id'] == 'lOvEr'


class TestSendLove(LoggedInUserBaseTest):

    @mock.patch('logic.love.send_loves', autospec=True)
    def test_send_love_without_csrf(self, mock_send_loves, app):
        response = app.post('/love', {'recipients': 'janedoe', 'message': 'Love'}, expect_errors=True)

        assert response.status_int == 403
        self.assertFalse(mock_send_loves.called)

    @mock.patch('logic.love.send_loves', autospec=True)
    def test_send_love(self, mock_send_loves, app):
        csrf_token = self.add_csrf_token_to_session(app)
        response = app.post('/love', {'recipients': 'janedoe', 'message': 'Love', '_csrf_token': csrf_token})

        assert response.status_int == 302
        mock_send_loves.assert_called_once_with(set([u'janedoe']), u'Love', secret=False)


class TestMe(LoggedInUserBaseTest):
    """
    Testing /me
    """

    def test_me(self, app):
        response = app.get('/me')

        assert response.status_int == 200
        assert 'me.html' in response.template

        assert response.context['current_time'] is not None
        assert response.context['current_user'] == self.current_user
        assert response.context['sent_loves'] == []
        assert 'Give and ye shall receive!' in response.body
        assert response.context['received_loves'] == []
        assert 'You haven\'t sent any love yet.' in response.body

    def test_me_with_loves(self, app):
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
        response = app.get('/me')

        assert response.context['sent_loves'] == [sent_love]
        assert 'Well done.' in response.body
        assert response.context['received_loves'] == [received_love]
        assert 'Awesome work.' in response.body

        dude.key.delete()


class SubscriptionsTestCase(LoggedInAdminBaseTest):
    """
    Testing /subscriptions
    """

    def test_subscriptions(self, app):
        response = app.get('/subscriptions')

        assert response.status_int == 200
        assert 'subscriptions.html' in response.template

    @mock.patch('views.web.Subscription', autospec=True)
    def test_create_subscription(self, mock_model_subscription, app):
        csrf_token = self.add_csrf_token_to_session(app)
        response = app.post(
            '/subscriptions/create',
            dict(
                request_url='http://example.org',
                event='lovesent',
                active='true',
                secret='secret-sauce',
                _csrf_token=csrf_token,
            )
        )

        assert response.status_int == 302
        mock_model_subscription.create_from_dict.assert_called_once_with(
            dict(
                request_url='http://example.org',
                event='lovesent',
                active=True,
                secret='secret-sauce',
            )
        )

    @mock.patch('views.web.logic.subscription', autospec=True)
    def test_deleting_alias(self, mock_logic_subscription, app):
        csrf_token = self.add_csrf_token_to_session(app)
        subscription = create_subscription()
        response = app.post(
            '/subscriptions/{id}/delete'.format(id=subscription.key.id()),
            dict(_csrf_token=csrf_token),
        )

        assert response.status_int == 302
        mock_logic_subscription.delete_subscription.assert_called_once_with(subscription.key.id())


class AliasesTestCase(LoggedInAdminBaseTest):
    """
    Testing /aliases
    """

    def test_listing_aliases(self, app):
        response = app.get('/aliases')

        assert response.status_int == 200
        assert 'aliases.html' in response.template
        self.assert_has_csrf(response.forms['alias-form'], response.session)

    @mock.patch('views.web.logic.alias', autospec=True)
    def test_saving_alias(self, mock_logic_alias, app):
        create_employee(username='dude')
        csrf_token = self.add_csrf_token_to_session(app)

        response = app.post(
            '/aliases',
            {'alias': 'duden', 'username': 'dude', '_csrf_token': csrf_token},
        )

        assert response.status_int == 302
        mock_logic_alias.save_alias.assert_called_once_with(
            'duden',
            'dude',
        )

    def test_saving_alias_all_empty(self, app):
        csrf_token = self.add_csrf_token_to_session(app)

        response = app.post(
            '/aliases',
            {'alias': '', 'username': '', '_csrf_token': csrf_token},
        )

        assert response.status_int == 302
        assert logic.alias.get_alias('foo') is None

    @mock.patch('views.web.logic.alias', autospec=True)
    def test_deleting_alias(self, mock_logic_alias, app):
        create_employee(username='man')
        csrf_token = self.add_csrf_token_to_session(app)

        alias = create_alias_with_employee_username(name='mano', username='man')
        response = app.post(
            '/aliases/{id}/delete'.format(id=alias.key.id()),
            {'_csrf_token': csrf_token},
        )

        assert response.status_int == 302
        mock_logic_alias.delete_alias.assert_called_once_with(alias.key.id())


class TestMeOrExplore(LoggedInUserBaseTest):
    """
    Testing redirect to /me or /explore?user=johnd
    """

    def test_no_such_employee(self, app):
        with self.assertRaises(AppError) as caught:
            app.get('/panda')

        self.assert_(
            caught.exception.message.startswith('Bad response: 404'),
            'Expected request for unknown employee to return 404',
        )

    def test_redirect_to_me(self, app):
        response = app.get('/{username}'.format(username=self.current_user.username))

        assert response.status_int == 302
        assert '/me' in response.location

    def test_redirect_to_explore(self, app):
        create_employee(username='buddy')
        response = app.get('/buddy')

        assert response.status_int == 302
        assert '/explore?user=buddy' in response.location

    def test_with_alias(self, app):
        create_employee(username='buddy')
        create_alias_with_employee_username(name='buddyalias', username='buddy')
        response = app.get('/buddyalias')

        assert response.status_int == 302
        assert '/explore?user=buddy' in response.location


class TestLeaderboard(LoggedInUserBaseTest):
    """
    Testing /leaderboard
    """

    def test_leaderboard(self, app):
        response = app.get('/leaderboard')

        assert response.status_int == 200
        assert 'leaderboard.html' in response.template
        assert response.context['top_loved'] is not None
        assert response.context['top_lovers'] is not None
        assert response.context['departments'] is not None
        assert response.context['sub_departments'] is not None
        assert response.context['selected_dept'] is None
        assert response.context['selected_timespan'] is not None


class TestExplore(LoggedInUserBaseTest):
    """
    Testing /explore
    """

    def test_explore(self, app):
        response = app.get('/explore')

        assert response.status_int == 200
        assert 'explore.html' in response.template
        assert response.context['current_time'] is not None
        assert response.context['user'] is None

    def test_explore_with_user(self, app):
        create_employee(username='buddy')
        response = app.get('/explore?user=buddy')

        assert response.status_int == 200
        assert 'explore.html' in response.template
        assert response.context['current_time'] is not None
        assert 'buddy' == response.context['user'].username

    def test_explore_with_unkown_user(self, app):
        response = app.get('/explore?user=noone')

        assert response.status_int == 302
        assert '/explore' in response.location


class TestAutocomplete(LoggedInUserBaseTest):
    nosegae_memcache = True
    nosegae_search = True

    def setUp(self):
        create_employee(username='alice')
        create_employee(username='alex')
        create_employee(username='bob')
        create_employee(username='carol')
        with mock.patch('logic.employee.memory_usage', autospec=True):
            logic.employee.rebuild_index()

    def test_autocomplete(self, app):
        self._test_autocomplete(app, 'a', ['alice', 'alex'])
        self._test_autocomplete(app, 'b', ['bob'])
        self._test_autocomplete(app, 'c', ['carol'])
        self._test_autocomplete(app, 'stupidprefix', [])
        self._test_autocomplete(app, '', [])

    def _test_autocomplete(self, app, prefix, expected_values):
        response = app.get('/user/autocomplete', {'term': prefix})
        received_values = set(item['value'] for item in response.json)
        assert set(expected_values) == received_values


class EmployeeTestCase(LoggedInAdminBaseTest):
    """
    Testing /employees
    """

    def test_employees(self, app):
        create_employee(username='buddy')
        response = app.get('/employees')

        assert response.status_int == 200
        assert 'employees.html' in response.template
        assert response.context['pagination_result'] is not None

    def test_employees_import_form(self, app):
        response = app.get('/employees/import')

        assert response.status_int == 200
        assert 'import.html' in response.template
        assert response.context['import_file_exists'] is not None
