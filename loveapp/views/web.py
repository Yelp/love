# -*- coding: utf-8 -*-
import os.path
from datetime import datetime

from flask import abort
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import request
from flask import url_for
from google.appengine.api import taskqueue

import loveapp.config as config
import loveapp.logic.alias
import loveapp.logic.employee
import loveapp.logic.event
import loveapp.logic.love
import loveapp.logic.love_count
import loveapp.logic.love_link
import loveapp.logic.subscription
from errors import NoSuchEmployee
from errors import NoSuchLoveLink
from errors import TaintedLove
from loveapp.logic import TIMESPAN_THIS_WEEK
from loveapp.logic.department import get_all_departments
from loveapp.logic.leaderboard import get_leaderboard_data
from loveapp.logic.love_link import create_love_link
from loveapp.logic.office import get_all_offices
from loveapp.models import Alias
from loveapp.models import Employee
from loveapp.models import Subscription
from loveapp.models.access_key import AccessKey
from loveapp.util.company_values import get_company_value
from loveapp.util.company_values import get_company_value_link_pairs
from loveapp.util.company_values import values_matching_prefix
from loveapp.util.decorators import admin_required
from loveapp.util.decorators import csrf_protect
from loveapp.util.decorators import user_required
from loveapp.util.formatting import format_loves
from loveapp.util.recipient import sanitize_recipients
from loveapp.util.render import make_json_response
from loveapp.util.render import render_template
from loveapp.views import common

web_app = Blueprint('web_app', __name__)


@web_app.route('/', methods=['GET'])
@user_required
def home():
    link_id = request.args.get('link_id', None)
    recipients = request.args.get('recipients', request.args.get('recipient'))
    message = request.args.get('message')

    return render_template(
        'home.html',
        current_time=datetime.utcnow(),
        current_user=Employee.get_current_employee(),
        recipients=recipients,
        message=message,
        url='{0}l/{1}'.format(config.APP_BASE_URL, link_id) if link_id else None
    )


@web_app.route('/me', methods=['GET'])
@user_required
def me():
    current_employee = Employee.get_current_employee()

    sent_love = loveapp.logic.love.recent_sent_love(current_employee.key, limit=20)
    received_love = loveapp.logic.love.recent_received_love(current_employee.key, limit=20)

    return render_template(
        'me.html',
        current_time=datetime.utcnow(),
        current_user=current_employee,
        sent_loves=sent_love.get_result(),
        received_loves=received_love.get_result()
    )


@web_app.route('/<regex("[a-zA-Z]{3,30}"):user>', methods=['GET'])
@user_required
def me_or_explore(user):
    current_employee = Employee.get_current_employee()
    username = loveapp.logic.alias.name_for_alias(user.lower().strip())

    try:
        user_key = Employee.get_key_for_username(username)
    except NoSuchEmployee:
        abort(404)

    if current_employee.key == user_key:
        return redirect(url_for('web_app.me'))
    else:
        return redirect(url_for('web_app.explore', user=username))


@web_app.route('/value/<string:company_value_id>', methods=['GET'])
@user_required
def single_company_value(company_value_id):
    company_value = get_company_value(company_value_id.upper())
    if not company_value:
        return redirect(url_for('web_app.company_values'))

    current_employee = Employee.get_current_employee()

    loves = loveapp.logic.love.recent_loves_by_company_value(None, company_value.id, limit=100).get_result()
    loves_list_one, loves_list_two = format_loves(loves)

    return render_template(
        'values.html',
        current_time=datetime.utcnow(),
        current_user=current_employee,
        loves_first_list=loves_list_one,
        loves_second_list=loves_list_two,
        values=get_company_value_link_pairs(),
        company_value_string=company_value.display_string
    )


@web_app.route('/values', methods=['GET'])
@user_required
def company_values():
    if not config.COMPANY_VALUES:
        abort(404)

    loves = loveapp.logic.love.recent_loves_with_any_company_value(None, limit=100).get_result()
    loves_list_one, loves_list_two = format_loves(loves)

    current_employee = Employee.get_current_employee()

    return render_template(
        'values.html',
        current_time=datetime.utcnow(),
        current_user=current_employee,
        loves_first_list=loves_list_one,
        loves_second_list=loves_list_two,
        values=get_company_value_link_pairs(),
        company_value_string=None
    )


@web_app.route('/l/<string:link_id>', methods=['GET'])
@user_required
def love_link(link_id):
    try:
        loveLink = loveapp.logic.love_link.get_love_link(link_id)
        recipients_str = loveLink.recipient_list
        message = loveLink.message

        recipients = sanitize_recipients(recipients_str)
        loved = [
            Employee.get_key_for_username(recipient).get()
            for recipient in recipients
        ]

        return render_template(
            'love_link.html',
            current_time=datetime.utcnow(),
            current_user=Employee.get_current_employee(),
            recipients=recipients_str,
            message=message,
            loved=loved,
            link_id=link_id,
        )
    except (NoSuchLoveLink, NoSuchEmployee):
        flash('Sorry, that link ({}) is no longer valid.'.format(link_id), 'error')
        return redirect(url_for('web_app.home'))


@web_app.route('/explore', methods=['GET'])
@user_required
def explore():
    username = request.args.get('user', None)
    if not username:
        if username is not None:
            flash('Enter a name, lover.', 'error')
        return render_template(
            'explore.html',
            current_time=datetime.utcnow(),
            user=None
        )
    username = username.lower().strip()

    user_key = Employee.query(
        Employee.username == username,
        Employee.terminated == False,  # noqa
    ).get(keys_only=True)

    if not user_key:
        flash('Sorry, "{}" is not a valid user.'.format(username), 'error')
        return redirect(url_for('web_app.explore'))

    sent_love = loveapp.logic.love.recent_sent_love(user_key, include_secret=False, limit=20)
    received_love = loveapp.logic.love.recent_received_love(user_key, include_secret=False, limit=20)

    return render_template(
        'explore.html',
        current_time=datetime.utcnow(),
        sent_loves=sent_love.get_result(),
        received_loves=received_love.get_result(),
        user=user_key.get()
    )


@web_app.route('/leaderboard', methods=['GET'])
@user_required
def leaderboard():
    timespan = request.args.get('timespan', TIMESPAN_THIS_WEEK)
    department = request.args.get('department', None)
    office = request.args.get('office', None)

    (top_lover_dicts, top_loved_dicts) = get_leaderboard_data(timespan, department, office)

    return render_template(
        'leaderboard.html',
        top_loved=top_loved_dicts,
        top_lovers=top_lover_dicts,
        departments=get_all_departments(),
        offices=get_all_offices(),
        selected_dept=department,
        selected_timespan=timespan,
        selected_office=office,
        org_title=config.ORG_TITLE,
        teams_title=config.TEAMS_TITLE,
        offices_title=config.OFFICES_TITLE
    )


@web_app.route('/sent', methods=['GET'])
@user_required
def sent():
    link_id = request.args.get('link_id', None)
    recipients_str = request.args.get('recipients', None)
    message = request.args.get('message', None)

    if not link_id or not recipients_str or not message:
        return redirect(url_for('web_app.home'))

    recipients = sanitize_recipients(recipients_str)
    loved = [
        Employee.get_key_for_username(recipient).get()
        for recipient in recipients
    ]

    return render_template(
        'sent.html',
        current_time=datetime.utcnow(),
        current_user=Employee.get_current_employee(),
        message=message,
        loved=loved,
        url='{0}l/{1}'.format(config.APP_BASE_URL, link_id),
    )


@web_app.route('/keys', methods=['GET'])
@admin_required
def keys():
    api_keys = AccessKey.query().fetch()
    return render_template(
        'keys.html',
        keys=api_keys
    )


@web_app.route('/keys/create', methods=['POST'])
@csrf_protect
@admin_required
def create_key():
    description = request.form.get('description')
    new_key = AccessKey.create(description)

    flash('Your API key {} has been created. Refresh the page to see it below.'.format(new_key.access_key))
    return redirect(url_for('web_app.keys'))


@web_app.route('/love', methods=['POST'])
@csrf_protect
@user_required
def love():
    action = request.form.get('action')
    recipients = sanitize_recipients(request.form.get('recipients'))
    message = request.form.get('message').strip()
    secret = (request.form.get('secret') == 'true')
    link_id = request.form.get('link_id')

    if not recipients:
        flash('Enter a name, lover.', 'error')
        return redirect(url_for('web_app.home'))

    recipients_display_str = ', '.join(recipients)

    if not message:
        flash('Enter a message, lover.', 'error')
        return redirect(url_for('web_app.home', recipients=recipients_display_str))

    try:
        if action == 'create_link':
            _, real_recipients = loveapp.logic.love.validate_love_recipients(recipients)
            real_display_str = ', '.join(real_recipients)
            hash_key = create_love_link(real_display_str, message).hash_key
            return redirect(url_for('web_app.home', recipients=real_display_str, link_id=hash_key, message=message))
        else:
            real_recipients = loveapp.logic.love.send_loves(recipients, message, secret=secret)
            # actual recipients may have the sender stripped from the list
            real_display_str = ', '.join(real_recipients)

            if secret:
                flash('Secret love sent to {}!'.format(real_display_str))
                return redirect(url_for('web_app.home'))
            else:
                hash_key = link_id if link_id else create_love_link(real_display_str, message).hash_key
                return redirect(url_for('web_app.sent', message=message, recipients=real_display_str, link_id=hash_key))

    except TaintedLove as exc:
        if exc.is_error:
            flash(exc.user_message, 'error')
        else:
            flash(exc.user_message)

        return redirect(url_for('web_app.home', recipients=recipients_display_str, message=message))


@web_app.route('/user/autocomplete', methods=['GET'])
@user_required
def autocomplete_web():
    return common.autocomplete(request)


@web_app.route('/values/autocomplete', methods=['GET'])
@user_required
def autocomplete_company_values_web():
    matching_prefixes = values_matching_prefix(request.args.get('term', None))
    return make_json_response(matching_prefixes)


@web_app.route('/subscriptions', methods=['GET'])
@admin_required
def subscriptions():
    return render_template(
        'subscriptions.html',
        subscriptions=Subscription.query().fetch(),
        events=loveapp.logic.event.EVENTS,
    )


@web_app.route('/subscriptions/create', methods=['POST'])
@csrf_protect
@admin_required
def create_subscription():
    subscription_dict = dict(
        request_url=request.form.get('request_url').strip(),
        event=request.form.get('event').strip(),
        active=(request.form.get('active') == 'true'),
        secret=request.form.get('secret').strip(),
    )

    try:
        Subscription.create_from_dict(subscription_dict)
        flash('Subscription created. Refresh the page to see it.')
    except ValueError:
        flash('Something went wrong. Please check your input.', 'error')

    return redirect(url_for('web_app.subscriptions'))


@web_app.route('/subscriptions/<int:subscription_id>/delete', methods=['POST'])
@csrf_protect
@admin_required
def delete_subscription(subscription_id):
    loveapp.logic.subscription.delete_subscription(subscription_id)
    flash('Subscription deleted. Refresh the page to see it\'s gone.', 'info')
    return redirect(url_for('web_app.subscriptions'))


@web_app.route('/aliases', methods=['GET'])
@admin_required
def aliases():
    return render_template(
        'aliases.html',
        aliases=Alias.query().fetch(),
    )


@web_app.route('/aliases', methods=['POST'])
@csrf_protect
@admin_required
def create_alias():
    try:
        loveapp.logic.alias.save_alias(
            request.form.get('alias').strip(),
            request.form.get('username').strip(),
        )
        flash('New alias successfully saved. Refresh the page to see it.')
    except Exception as e:
        flash('Something went wrong: {}.'.format(str(e)), 'error')

    return redirect(url_for('web_app.aliases'))


@web_app.route('/aliases/<int:alias_id>/delete', methods=['POST'])
@csrf_protect
@admin_required
def delete_alias(alias_id):
    loveapp.logic.alias.delete_alias(alias_id)
    flash('Alias successfully deleted. Refresh the page to see it\'s gone.', 'info')
    return redirect(url_for('web_app.aliases'))


@web_app.route('/employees', methods=['GET'])
@admin_required
def employees():
    return render_template(
        'employees.html',
        pagination_result=Employee.paginate(
            order_by=Employee.username,
            prev_cursor_str=request.args.get('prev_cursor'),
            next_cursor_str=request.args.get('next_cursor'),
        ),
    )


@web_app.route('/employees/import', methods=['GET'])
@admin_required
def import_employees_form():
    import_file_exists = os.path.isfile(loveapp.logic.employee.csv_import_file())
    return render_template(
        'import.html',
        import_file_exists=import_file_exists,
    )


@web_app.route('/employees/import', methods=['POST'])
@admin_required
def import_employees():
    flash('We started importing employee data in the background. Refresh the page to see it.', 'info')
    taskqueue.add(url='/tasks/employees/load/csv')
    return redirect(url_for('web_app.employees'))
