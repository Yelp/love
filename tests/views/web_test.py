# -*- coding: utf-8 -*-
import mock
import pytest
from bs4 import BeautifulSoup

import loveapp.logic
from loveapp.config import CompanyValue
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee
from testing.factories import create_love
from testing.factories import create_love_link
from testing.factories import create_subscription
from testing.util import LoggedInAdminBaseTest
from testing.util import LoggedInUserBaseTest
from testing.util import YelpLoveTestCase


@pytest.mark.usefixtures('gae_testbed')
class TestLoggedOut(YelpLoveTestCase):
    """
    Testing access to pages when no user is logged in.
    """

    @pytest.mark.parametrize('url', [
        '/',
        '/me',
        '/explore',
        '/johnd',
        '/leaderboard',
        '/keys',
        '/user/autocomplete',
        '/values/autocomplete',
        '/value/test',
        '/values',
        '/sent',
        '/subscriptions',
        '/aliases',
        '/employees',
        '/employees/import'
    ])
    def test_get_requires_login(self, client, url):
        self.assertRequiresLogin(client.get(url))

    @pytest.mark.parametrize('url, data', [
        ('/keys/create', dict(description='My Api Key')),
        ('/love', dict(recipients='jenny', message='Love')),
        ('/subscriptions/create', dict(
            request_url='http://localhost.com/foo',
            event='lovesent',
            active='true',
            secret='mysecret')
         ),
        ('/subscriptions/1/delete', dict()),
        ('/aliases', dict(alias='johnny', username='john')),
        ('/aliases/1/delete', dict()),
        ('/employees/import', dict())
    ])
    def test_post_requires_login(self, client, url, data):
        data['_csrf_token'] = self.addCsrfTokenToSession(client)
        self.assertRequiresLogin(
            client.post(
                url,
                data=data
            )
        )


class TestAdminResources(YelpLoveTestCase):
    # Managing API Keys

    def test_keys(self, client):
        self.assertRequiresAdmin(
            client.get('/keys')
        )

    def test_create_key(self, client):
        csrf_token = self.addCsrfTokenToSession(client)
        self.assertRequiresAdmin(
            client.post(
                '/keys/create',
                data=dict(
                    description='My API Key',
                    _csrf_token=csrf_token
                )
            ),
        )

    # Managing Webhook Subscriptions
    def test_subscriptions(self, client):
        self.assertRequiresAdmin(
            client.get('/subscriptions')
        )

    def test_create_subscription(self, client):
        csrf_token = self.addCsrfTokenToSession(client)
        self.assertRequiresAdmin(
            client.post(
                '/subscriptions/create',
                data=dict(
                    request_url='http://localhost.com/foo',
                    event='lovesent',
                    active='true',
                    secret='mysecret',
                    _csrf_token=csrf_token
                )
            ),
        )

    def test_delete_subscription(self, client):
        csrf_token = self.addCsrfTokenToSession(client)
        self.assertRequiresAdmin(
            client.post(
                '/subscriptions/1/delete',
                data=dict(_csrf_token=csrf_token)
            ),
        )

    # Managing Aliases
    def test_aliases(self, client):
        self.assertRequiresAdmin(
            client.get('/aliases'),
        )

    def test_create_alias(self, client):
        csrf_token = self.addCsrfTokenToSession(client)
        self.assertRequiresAdmin(
            client.post(
                '/aliases',
                data=dict(
                    alias='johnny',
                    username='john',
                    _csrf_token=csrf_token
                )
            )
        )

    def test_delete_alias(self, client):
        csrf_token = self.addCsrfTokenToSession(client)
        self.assertRequiresAdmin(
            client.post(
                '/aliases/1/delete',
                data=dict(_csrf_token=csrf_token)
            )
        )

    def test_employees(self, client):
        self.assertRequiresAdmin(
            client.get('/employees')
        )

    def test_import_employees_form(self, client):
        self.assertRequiresAdmin(
            client.get('/employees/import')
        )

    def test_import_employees(self, client):
        csrf_token = self.addCsrfTokenToSession(client)
        self.assertRequiresAdmin(
            client.post(
                '/employees/import',
                data=dict(_csrf_token=csrf_token)
            )
        )


class TestHomepage(LoggedInUserBaseTest):
    """
    Testing the homepage
    """

    def test_index(self, client, recorded_templates):
        response = client.get('/')
        assert response.status_code == 200
        template, response_context = recorded_templates[0]
        assert 'home.html' in template.name

        assert response_context['current_time'] is not None
        assert response_context['current_user'] == self.logged_in_employee
        assert response_context['recipients'] is None
        self.assertHasCsrf(response, 'send-love-form', response_context['session'])

    def test_index_with_recipient_and_message(self, client, recorded_templates):
        response = client.get('/', query_string=dict(recipients='janedoe', message='hi'))
        assert response.status_code == 200

        template, response_context = recorded_templates[0]
        soup = BeautifulSoup(response.data, 'html.parser')
        send_love_form = soup.find('form', class_='send-love-form')
        assert response_context['recipients'] == 'janedoe'

        assert send_love_form.find('input', {'name': 'recipients'}).get('value') == 'janedoe'
        assert send_love_form.textarea.text == 'hi'
        self.assertHasCsrf(response, 'send-love-form', response_context['session'])


class TestSent(LoggedInUserBaseTest):
    """
    Testing the sent page
    """

    def test_missing_args_is_redirect(self, client):
        response = client.get('/sent')
        assert response.status_code == 302

    @mock.patch('loveapp.config')
    def test_sent_with_args(self, mock_config, client, recorded_templates):
        mock_config.APP_BASE_URL = 'http://foo.io/'
        mock_config.DOMAIN = 'example.com'

        create_employee('janedoe')
        client.get('/sent', query_string=dict(recipients='janedoe', message='hi', link_id='cn23sx'))

        _, response_context = recorded_templates[0]
        assert response_context['current_time'] is not None
        response_context['current_user'] == self.logged_in_employee
        assert response_context['loved'] is not None
        response_context['url'] == 'http://foo.io/l/cn23sx'


class TestLoveLink(LoggedInUserBaseTest):
    """
    Testing the sent page
    """

    def test_bad_hash(self, client):
        response = client.get('/l/badId')
        assert response.status_code == 302

    def test_good_hash(self, client, recorded_templates):
        create_employee(username='janedoe')
        create_love_link('lOvEr', 'i love you!', 'janedoe')
        client.get('/l/lOvEr')

        _, response_context = recorded_templates[0]

        assert response_context['current_time'] is not None
        assert response_context['current_user'] == self.logged_in_employee
        assert response_context['loved'] is not None
        assert response_context['recipients'] == 'janedoe'
        assert response_context['message'] == 'i love you!'
        assert response_context['link_id'] == 'lOvEr'


class TestSendLove(LoggedInUserBaseTest):

    @pytest.fixture
    def jenny(self):
        jenny = create_employee(username='jenny')
        yield jenny
        jenny.key.delete()

    @mock.patch('loveapp.logic.love.send_loves', autospec=True)
    def test_send_love_without_csrf(self, mock_send_loves, client, jenny):
        response = client.post('/love', data={'recipients': 'jenny', 'message': 'Love'}, )

        assert response.status_code == 403
        assert mock_send_loves.called is False

    @mock.patch('loveapp.logic.love.send_loves', autospec=True)
    def test_send_love(self, mock_send_loves, client, jenny):
        csrf_token = self.addCsrfTokenToSession(client)
        response = client.post('/love', data={'recipients': 'jenny', 'message': 'Love', '_csrf_token': csrf_token})

        assert response.status_code == 302
        mock_send_loves.assert_called_once_with(set([u'jenny']), u'Love', secret=False)


class TestMe(LoggedInUserBaseTest):
    """
    Testing /me
    """

    def test_me(self, client, recorded_templates):
        response = client.get('/me')
        template, response_context = recorded_templates[0]

        assert response.status_code == 200
        assert 'me.html' in template.name

        assert response_context['current_time'] is not None
        assert response_context['current_user'] == self.logged_in_employee
        assert response_context['sent_loves'] == []
        assert 'Give and ye shall receive!' in response.data.decode()
        assert response_context['received_loves'] == []
        assert 'You haven\'t sent any love yet.' in response.data.decode()

    def test_me_with_loves(self, client, recorded_templates):
        dude = create_employee(username='dude')
        sent_love = create_love(
            sender_key=self.logged_in_employee.key,
            recipient_key=dude.key,
            message='Well done.'
        )
        received_love = create_love(
            sender_key=dude.key,
            recipient_key=self.logged_in_employee.key,
            message='Awesome work.'
        )
        response = client.get('/me')
        _, response_context = recorded_templates[0]

        assert response_context['sent_loves'] == [sent_love]
        assert 'Well done.' in response.data.decode()
        assert response_context['received_loves'] == [received_love]
        assert 'Awesome work.' in response.data.decode()

        dude.key.delete()


class TestSubscriptions(LoggedInAdminBaseTest):
    """
    Testing /subscriptions
    """

    def test_subscriptions(self, client, recorded_templates):
        response = client.get('/subscriptions')
        template, response_context = recorded_templates[0]

        assert response.status_code == 200
        assert 'subscriptions.html' in template.name

    @mock.patch('loveapp.views.web.Subscription', autospec=True)
    def test_create_subscription(self, mock_model_subscription, client):
        csrf_token = self.addCsrfTokenToSession(client)
        response = client.post(
            '/subscriptions/create',
            data=dict(
                request_url='http://example.org',
                event='lovesent',
                active='true',
                secret='secret-sauce',
                _csrf_token=csrf_token,
            )
        )

        assert response.status_code == 302
        mock_model_subscription.create_from_dict.assert_called_once_with(
            dict(
                request_url='http://example.org',
                event='lovesent',
                active=True,
                secret='secret-sauce',
            )
        )

    @mock.patch('loveapp.logic.subscription', autospec=True)
    def test_deleting_alias(self, mock_logic_subscription, client):
        csrf_token = self.addCsrfTokenToSession(client)
        subscription = create_subscription()
        response = client.post(
            '/subscriptions/{id}/delete'.format(id=subscription.key.id()),
            data=dict(_csrf_token=csrf_token),
        )

        assert response.status_code == 302
        mock_logic_subscription.delete_subscription.assert_called_once_with(subscription.key.id())


class TestAliases(LoggedInAdminBaseTest):
    """
    Testing /aliases
    """

    def test_listing_aliases(self, client, recorded_templates):
        response = client.get('/aliases')
        assert response.status_code == 200
        template, response_context = recorded_templates[0]
        assert 'aliases.html' in template.name
        self.assertHasCsrf(response, 'alias-form', response_context['session'])

    @mock.patch('loveapp.logic.alias', autospec=True)
    def test_saving_alias(self, mock_logic_alias, client):
        create_employee(username='dude')
        csrf_token = self.addCsrfTokenToSession(client)

        response = client.post(
            '/aliases',
            data={'alias': 'duden', 'username': 'dude', '_csrf_token': csrf_token},
        )

        assert response.status_code == 302
        mock_logic_alias.save_alias.assert_called_once_with(
            'duden',
            'dude',
        )

    def test_saving_alias_all_empty(self, client):
        csrf_token = self.addCsrfTokenToSession(client)

        response = client.post(
            '/aliases',
            data={'alias': '', 'username': '', '_csrf_token': csrf_token}
        )

        assert response.status_code == 302
        assert loveapp.logic.alias.get_alias('foo') is None

    @mock.patch('loveapp.logic.alias', autospec=True)
    def test_deleting_alias(self, mock_logic_alias, client):
        create_employee(username='man')
        csrf_token = self.addCsrfTokenToSession(client)

        alias = create_alias_with_employee_username(name='mano', username='man')
        response = client.post(
            '/aliases/{id}/delete'.format(id=alias.key.id()),
            data={'_csrf_token': csrf_token},
        )

        assert response.status_code == 302
        mock_logic_alias.delete_alias.assert_called_once_with(alias.key.id())


class TestMeOrExplore(LoggedInUserBaseTest):
    """
    Testing redirect to /me or /explore?user=johnd
    """

    def test_no_such_employee(self, client):
        response = client.get('/panda')
        assert response.status_code == 404

    def test_redirect_to_me(self, client):
        response = client.get('/{username}'.format(username=self.logged_in_employee.username))
        assert response.status_code == 302
        assert '/me' in response.headers.get('location')

    def test_redirect_to_explore(self, client):
        create_employee(username='buddy')
        response = client.get('/buddy')

        assert response.status_code == 302
        assert '/explore?user=buddy' in response.headers.get('location')

    def test_with_alias(self, client):
        create_employee(username='buddy')
        create_alias_with_employee_username(name='buddyalias', username='buddy')
        response = client.get('/buddyalias')

        assert response.status_code == 302
        assert '/explore?user=buddy' in response.headers.get('location')


class TestLeaderboard(LoggedInUserBaseTest):
    """
    Testing /leaderboard
    """

    def test_leaderboard(self, client, recorded_templates):
        response = client.get('/leaderboard')
        template, response_context = recorded_templates[0]

        assert response.status_code == 200
        assert 'leaderboard.html' in template.name
        assert response_context['top_loved'] is not None
        assert response_context['top_lovers'] is not None
        assert response_context['departments'] is not None
        assert response_context['offices'] is not None
        assert response_context['selected_dept'] is None
        assert response_context['selected_timespan'] is not None
        assert response_context['selected_office'] is None


class TestExplore(LoggedInUserBaseTest):
    """
    Testing /explore
    """

    def test_explore(self, client, recorded_templates):
        response = client.get('/explore')
        template, response_context = recorded_templates[0]

        assert response.status_code == 200
        assert 'explore.html' in template.name
        assert response_context['current_time'] is not None
        assert response_context['user'] is None

    def test_explore_with_user(self, client, recorded_templates):
        create_employee(username='buddy')
        response = client.get('/explore?user=buddy')
        template, response_context = recorded_templates[0]

        assert response.status_code == 200
        assert 'explore.html' in template.name
        assert response_context['current_time'] is not None
        assert 'buddy' == response_context['user'].username

    def test_explore_with_unkown_user(self, client):
        response = client.get('/explore?user=noone')

        assert response.status_code == 302
        assert '/explore' in response.headers.get('location')


class TestAutocomplete(LoggedInUserBaseTest):

    @pytest.fixture(autouse=True)
    def create_employees(self, gae_testbed):
        create_employee(username='alice')
        create_employee(username='alex')
        create_employee(username='bob')
        create_employee(username='carol')
        with mock.patch('loveapp.logic.employee.memory_usage', autospec=True):
            loveapp.logic.employee.rebuild_index()

    @pytest.mark.parametrize('prefix, expected_values', [
        ('a', ['alice', 'alex']),
        ('b', ['bob']),
        ('c', ['carol']),
        ('stupidprefix', []),
        ('', [])

    ])
    def test_autocomplete(self, client, prefix, expected_values):
        response = client.get('/user/autocomplete', query_string={'term': prefix})
        received_values = set(item['value'] for item in response.json)
        assert set(expected_values) == received_values


class TestValuesAutocomplete(LoggedInUserBaseTest):

    @pytest.mark.parametrize('prefix, expected_values', [
        ('#aw', ['#awesome', '#awesometacular']),
        ('#su', ['#superAwesome']),
        ('#derp', [])
    ])
    def test_autocomplete(self, client, prefix, expected_values):
        with mock.patch('loveapp.util.company_values.config') as mock_config:
            mock_config.COMPANY_VALUES = [
                CompanyValue('AWESOME', 'awesome', ['awesome', 'awesometacular', 'superAwesome']),
            ]

            response = client.get('/values/autocomplete', query_string={'term': prefix})
            received_values = set(item for item in response.json)
            assert set(expected_values) == received_values


class TestValues(LoggedInUserBaseTest):

    @pytest.fixture(autouse=True)
    def create_loves(self, gae_testbed):
        receiver = create_employee(username='receiver')
        sender = create_employee(username='sender')

        create_love(
            sender_key=sender.key,
            recipient_key=receiver.key,
            message='really cool',
            company_values=['COOL']
        )

        create_love(
            sender_key=sender.key,
            recipient_key=receiver.key,
            message='really quite cool',
            company_values=['COOL']
        )

        create_love(
            sender_key=sender.key,
            recipient_key=receiver.key,
            message='#cool #notcool',
            company_values=['COOL']
        )

        create_love(
            sender_key=sender.key,
            recipient_key=receiver.key,
            message='jk really awesome',
            company_values=['AWESOME']
        )

        create_love(
            sender_key=sender.key,
            recipient_key=receiver.key,
            message='bogus',
            company_values=[]
        )

    @mock.patch('loveapp.util.company_values.config')
    @mock.patch('loveapp.logic.love.config')
    def test_single_value_page(self, mock_util_config, mock_logic_config, client, recorded_templates):
        mock_util_config.COMPANY_VALUES = mock_logic_config.COMPANY_VALUES = [
            CompanyValue('AWESOME', 'awesome', ['awesome']),
            CompanyValue('COOL', 'cool', ['cool'])
        ]

        response = client.get('/value/cool')
        template, response_context = recorded_templates[0]
        assert 'really cool' in response.data.decode()
        assert 'really quite cool' in response.data.decode()

        # check linkification of hashtags
        assert '<a href="/value/cool">#cool</a>' in response.data.decode()

        # check only relevant hashtags are linkified
        assert '#notcool' in response.data.decode()
        assert '<a href="/value/cool">#notcool</a>' not in response.data.decode()

        assert 'jk really awesome' not in response.data.decode()

    @mock.patch('loveapp.util.company_values.config')
    @mock.patch('loveapp.logic.love.config')
    def test_all_values_page(self, mock_util_config, mock_logic_config, client, recorded_templates):
        mock_util_config.COMPANY_VALUES = mock_logic_config.COMPANY_VALUES = [
            CompanyValue('AWESOME', 'awesome', ['awesome']),
            CompanyValue('COOL', 'cool', ['cool'])
        ]

        response = client.get('/values')
        template, response_context = recorded_templates[0]

        assert 'really cool' in response.data.decode()
        assert 'jk really awesome' in response.data.decode()
        assert 'bogus' not in response.data.decode()


class TestEmployee(LoggedInAdminBaseTest):
    """
    Testing /employees
    """

    def test_employees(self, client, recorded_templates):
        create_employee(username='buddy')
        response = client.get('/employees')

        assert response.status_code == 200
        template, response_context = recorded_templates[0]
        assert 'employees.html' in template.name
        assert response_context['pagination_result'] is not None

    def test_employees_import_form(self, client, recorded_templates):
        response = client.get('/employees/import')

        assert response.status_code == 200
        template, response_context = recorded_templates[0]
        assert 'import.html' in template.name
        assert response_context['import_file_exists'] is not None
