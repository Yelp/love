# -*- coding: utf-8 -*-
import os.path

import config

from datetime import datetime

from flask import abort
from flask import flash
from flask import redirect
from flask import request
from flask import url_for

import logic.alias
import logic.employee
import logic.event
import logic.love
import logic.love_link
import logic.love_count
import logic.subscription
from errors import NoSuchEmployee
from errors import NoSuchLoveLink
from errors import TaintedLove
from google.appengine.api import taskqueue
from logic import TIMESPAN_THIS_WEEK
from logic.love_link import create_love_link
from logic.leaderboard import get_leaderboard_data
from main import app
from models import AccessKey
from models import Alias
from models import Employee
from models import Subscription
from util.decorators import admin_required
from util.decorators import csrf_protect
from util.decorators import user_required
from util.recipient import sanitize_recipients
from util.render import render_template
from util.render import make_json_response
from util.company_values import get_company_value
from util.company_values import get_company_value_link_pairs
from util.company_values import values_matching_prefix
from views import common
from logic.office import get_all_offices
from logic.department import get_all_departments


@app.route('/', methods=['GET'])
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


@app.route('/me', methods=['GET'])
@user_required
def me():
    current_employee = Employee.get_current_employee()

    sent_love = logic.love.recent_sent_love(current_employee.key, limit=20)
    received_love = logic.love.recent_received_love(current_employee.key, limit=20)

    return render_template(
        'me.html',
        current_time=datetime.utcnow(),
        current_user=current_employee,
        sent_loves=sent_love.get_result(),
        received_loves=received_love.get_result()
    )


@app.route('/<regex("[a-zA-Z]{3,30}"):user>', methods=['GET'])
@user_required
def me_or_explore(user):
    current_employee = Employee.get_current_employee()
    username = logic.alias.name_for_alias(user.lower().strip())

    try:
        user_key = Employee.get_key_for_username(username)
    except NoSuchEmployee:
        abort(404)

    if current_employee.key == user_key:
        return redirect(url_for('me'))
    else:
        return redirect(url_for('explore', user=username))


def format_loves(loves):
    # organise loves into two roughly equal lists for displaying
    if len(loves) < 20:
        loves_list_one = loves
        loves_list_two = []
    else:
        loves_list_one = loves[:len(loves)/2]
        loves_list_two = loves[len(loves)/2:]

        if len(loves_list_one) < len(loves_list_two):
            loves_list_one.append(loves_list_two.pop())
    return loves_list_one, loves_list_two


@app.route('/value/<string:company_value_id>', methods=['GET'])
@user_required
def single_company_value(company_value_id):
    company_value = get_company_value(company_value_id.upper())
    if not company_value:
        return redirect(url_for('company_values'))

    current_employee = Employee.get_current_employee()

    loves = logic.love.recent_loves_by_company_value(None, company_value.id, limit=100).get_result()
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


@app.route('/values', methods=['GET'])
@user_required
def company_values():
    if not config.COMPANY_VALUES:
        abort(404)

    loves = logic.love.recent_loves_with_any_company_value(None, limit=100).get_result()
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


@app.route('/l/<string:link_id>', methods=['GET'])
@user_required
def love_link(link_id):
    try:
        loveLink = logic.love_link.get_love_link(link_id)
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
        return redirect(url_for('home'))


@app.route('/explore', methods=['GET'])
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
        return redirect(url_for('explore'))

    sent_love = logic.love.recent_sent_love(user_key, include_secret=False, limit=20)
    received_love = logic.love.recent_received_love(user_key, include_secret=False, limit=20)

    return render_template(
        'explore.html',
        current_time=datetime.utcnow(),
        sent_loves=sent_love.get_result(),
        received_loves=received_love.get_result(),
        user=user_key.get()
    )


@app.route('/leaderboard', methods=['GET'])
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


@app.route('/sent', methods=['GET'])
@user_required
def sent():
    link_id = request.args.get('link_id', None)
    recipients_str = request.args.get('recipients', None)
    message = request.args.get('message', None)

    if not link_id or not recipients_str or not message:
        return redirect(url_for('home'))

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


@app.route('/keys', methods=['GET'])
@admin_required
def keys():
    api_keys = AccessKey.query().fetch()
    return render_template(
        'keys.html',
        keys=api_keys
    )


@app.route('/keys/create', methods=['POST'])
@csrf_protect
@admin_required
def create_key():
    description = request.form.get('description')
    new_key = AccessKey.create(description)

    flash('Your API key {} has been created. Refresh the page to see it below.'.format(new_key.access_key))
    return redirect(url_for('keys'))


@app.route('/love', methods=['POST'])
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
        return redirect(url_for('home'))

    recipients_display_str = ', '.join(recipients)

    if not message:
        flash('Enter a message, lover.', 'error')
        return redirect(url_for('home', recipients=recipients_display_str))

    try:
        if action == 'create_link':
            _, real_recipients = logic.love.validate_love_recipients(recipients)
            real_display_str = ', '.join(real_recipients)
            hash_key = create_love_link(real_display_str, message).hash_key
            return redirect(url_for('home', recipients=real_display_str, link_id=hash_key, message=message))
        else:
            real_recipients = logic.love.send_loves(recipients, message, secret=secret)
            # actual recipients may have the sender stripped from the list
            real_display_str = ', '.join(real_recipients)

            if secret:
                flash('Secret love sent to {}!'.format(real_display_str))
                return redirect(url_for('home'))
            else:
                hash_key = link_id if link_id else create_love_link(real_display_str, message).hash_key
                return redirect(url_for('sent', message=message, recipients=real_display_str, link_id=hash_key))

    except TaintedLove as exc:
        if exc.is_error:
            flash(exc.user_message, 'error')
        else:
            flash(exc.user_message)

        return redirect(url_for('home', recipients=recipients_display_str, message=message))


@app.route('/user/autocomplete', methods=['GET'])
@user_required
def autocomplete_web():
    return common.autocomplete(request)


@app.route('/values/autocomplete', methods=['GET'])
@user_required
def autocomplete_company_values_web():
    matching_prefixes = values_matching_prefix(request.args.get('term', None))
    return make_json_response(matching_prefixes)


@app.route('/subscriptions', methods=['GET'])
@admin_required
def subscriptions():
    return render_template(
        'subscriptions.html',
        subscriptions=Subscription.query().fetch(),
        events=logic.event.EVENTS,
    )


@app.route('/subscriptions/create', methods=['POST'])
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

    return redirect(url_for('subscriptions'))


@app.route('/subscriptions/<int:subscription_id>/delete', methods=['POST'])
@csrf_protect
@admin_required
def delete_subscription(subscription_id):
    logic.subscription.delete_subscription(subscription_id)
    flash('Subscription deleted. Refresh the page to see it\'s gone.', 'info')
    return redirect(url_for('subscriptions'))


@app.route('/aliases', methods=['GET'])
@admin_required
def aliases():
    return render_template(
        'aliases.html',
        aliases=Alias.query().fetch(),
    )


@app.route('/aliases', methods=['POST'])
@csrf_protect
@admin_required
def create_alias():
    try:
        logic.alias.save_alias(
            request.form.get('alias').strip(),
            request.form.get('username').strip(),
        )
        flash('New alias successfully saved. Refresh the page to see it.')
    except Exception as e:
        flash('Something went wrong: {}.'.format(e.message), 'error')

    return redirect(url_for('aliases'))


@app.route('/aliases/<int:alias_id>/delete', methods=['POST'])
@csrf_protect
@admin_required
def delete_alias(alias_id):
    logic.alias.delete_alias(alias_id)
    flash('Alias successfully deleted. Refresh the page to see it\'s gone.', 'info')
    return redirect(url_for('aliases'))


@app.route('/employees', methods=['GET'])
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


@app.route('/employees/import', methods=['GET'])
@admin_required
def import_employees_form():
    import_file_exists = os.path.isfile(logic.employee.csv_import_file())
    return render_template(
        'import.html',
        import_file_exists=import_file_exists,
    )


@app.route('/employees/import', methods=['POST'])
@admin_required
def import_employees():
    flash('We started importing employee data in the background. Refresh the page to see it.', 'info')
    taskqueue.add(url='/tasks/employees/load/csv')
    return redirect(url_for('employees'))
