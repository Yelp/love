# -*- coding: utf-8 -*-
import os.path

import config
import logging

from datetime import datetime
from datetime import timedelta

from flask import abort
from flask import flash
from flask import redirect
from flask import request
from flask import url_for

import logic.alias
import logic.department
import logic.employee
import logic.event
import logic.love
import logic.love_link
import logic.love_count
import logic.subscription
from errors import NoSuchEmployee
from errors import TaintedLove
from google.appengine.api import taskqueue
from logic import TIMESPAN_LAST_WEEK
from logic import TIMESPAN_THIS_WEEK
from logic import to_the_future
from logic import utc_week_limits
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
from views import common


@app.route('/', methods=['GET'])
@user_required
def home():
    recipients = request.args.get('recipients', request.args.get('recipient'))
    message = request.args.get('message')

    return render_template(
        'home.html',
        current_time=datetime.utcnow(),
        current_user=Employee.get_current_employee(),
        recipients=recipients,
        message=message,
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


@app.route('/l/<string:hash_key>', methods=['GET'])
@user_required
def love_link(hash_key):
    loveLink = logic.love_link.get_love_link(hash_key)
    logging.info(loveLink)
    return redirect(url_for('home') + '?recipient={}&message={}'.format(loveLink.recipient_list, loveLink.message))


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

    # If last week, we need to subtract *before* getting the week limits to
    # avoid being off by one hour on weeks that include a DST transition
    utc_now = datetime.utcnow()
    if timespan == TIMESPAN_LAST_WEEK:
        utc_now -= timedelta(days=7)
    utc_week_start, _ = utc_week_limits(utc_now)

    top_lovers, top_lovees = logic.love_count.top_lovers_and_lovees(utc_week_start, dept=department)

    top_lover_dicts = [
        {
            'employee': employee_key.get_async(),
            'num_sent': sent_count
        }
        for employee_key, sent_count
        in top_lovers
    ]

    top_loved_dicts = [
        {
            'employee': employee_key.get_async(),
            'num_received': received_count
        }
        for employee_key, received_count
        in top_lovees
    ]

    # get results for the futures set up previously
    map(to_the_future, top_lover_dicts)
    map(to_the_future, top_loved_dicts)

    return render_template(
        'leaderboard.html',
        top_loved=top_loved_dicts,
        top_lovers=top_lover_dicts,
        departments=logic.department.META_DEPARTMENTS,
        sub_departments=logic.department.META_DEPARTMENT_MAP,
        selected_dept=department,
        selected_timespan=timespan,
        org_title=config.ORG_TITLE,
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
    recipients = sanitize_recipients(request.form.get('recipients'))
    message = request.form.get('message').strip()
    secret = (request.form.get('secret') == 'true')

    if not recipients:
        flash('Enter a name, lover.', 'error')
        return redirect(url_for('home'))

    recipients_display_str = ', '.join(recipients)

    if not message:
        flash('Enter a message, lover.', 'error')
        return redirect(url_for('home', recipients=recipients_display_str))

    try:
        real_recipients = logic.love.send_loves(recipients, message, secret=secret)
        # actual recipients may have the sender stripped from the list
        real_display_str = ', '.join(real_recipients)

        flash('{}ove sent to {}!'.format('Secret l' if secret else 'L', real_display_str))
        return redirect(url_for('home'))
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
