# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import request
from flask import Response
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import loveapp.logic.employee
import loveapp.logic.notifier
import loveapp.logic.love
import loveapp.logic.love_count
import loveapp.logic.love_link
from loveapp.models import Love

tasks_app = Blueprint('tasks_app', __name__)

# All tasks that are to be executed by cron need to use HTTP GET
# see https://cloud.google.com/appengine/docs/python/config/cron


@tasks_app.route('/tasks/employees/load/s3', methods=['GET'])
def load_employees_from_s3():
    loveapp.logic.employee.load_employees()
    # we need to rebuild the love count index as the departments may have changed.
    taskqueue.add(url='/tasks/love_count/rebuild')
    return Response(status=200)


# This task has a web UI to trigger it, so let's use POST
@tasks_app.route('/tasks/employees/load/csv', methods=['POST'])
def load_employees_from_csv():
    loveapp.logic.employee.load_employees_from_csv()
    # we need to rebuild the love count index as the departments may have changed.
    taskqueue.add(url='/tasks/love_count/rebuild')
    return Response(status=200)


# One-off tasks are much easier to trigger using GET
@tasks_app.route('/tasks/employees/combine', methods=['GET'])
def combine_employees():
    old_username, new_username = request.args['old'], request.args['new']
    if not old_username:
        return Response(response='{} is not a valid username'.format(old_username), status=400)
    elif not new_username:
        return Response(response='{} is not a valid username'.format(new_username), status=400)

    loveapp.logic.employee.combine_employees(old_username, new_username)
    return Response(status=200)


@tasks_app.route('/tasks/index/rebuild', methods=['GET'])
def rebuild_index():
    loveapp.logic.employee.rebuild_index()
    return Response(status=200)


@tasks_app.route('/tasks/love/email', methods=['POST'])
def email_love():
    love_id = int(request.form['id'])
    love = ndb.Key(Love, love_id).get()
    loveapp.logic.love.send_love_email(love)
    return Response(status=200)


@tasks_app.route('/tasks/love_count/rebuild', methods=['GET'])
def rebuild_love_count():
    loveapp.logic.love_count.rebuild_love_count()
    return Response(status=200)


@tasks_app.route('/tasks/subscribers/notify', methods=['POST'])
def notify_subscribers():
    notifier = loveapp.logic.notifier.notifier_for_event(request.json['event'])(**request.json['options'])
    notifier.notify()
    return Response(status=200)


@tasks_app.route('/tasks/lovelinks/cleanup', methods=['GET'])
def lovelinks_cleanup():
    loveapp.logic.love_link.love_links_cleanup()
    return Response(status=200)
