# -*- coding: utf-8 -*-
from flask import request
from flask import Response
import json

# from google.appengine.api import taskqueue
from google.cloud import ndb
from logic.event import add_event
import logic.employee
import logic.notifier
import logic.love
import logic.love_count
import logic.love_link
from main import app
from models import Love


# All tasks that are to be executed by cron need to use HTTP GET
# see https://cloud.google.com/appengine/docs/python/config/cron
@app.route("/tasks/employees/load/s3", methods=["GET"])
def load_employees_from_s3():
    logic.employee.load_employees()
    # we need to rebuild the love count index as the departments may have changed.
    # taskqueue.add(url="/tasks/love_count/rebuild")
    add_event("load_S3", "/tasks/love_count/rebuild", {}, "GET")

    return Response(status=200)


# This task has a web UI to trigger it, so let's use POST
@app.route("/tasks/employees/load/csv", methods=["POST"])
def load_employees_from_csv():
    logic.employee.load_employees_from_csv()
    # we need to rebuild the love count index as the departments may have changed.
    # taskqueue.add(url="/tasks/love_count/rebuild")
    add_event("load_CSV", "/tasks/love_count/rebuild", {}, "GET")
    return Response(status=200)


# One-off tasks are much easier to trigger using GET
@app.route("/tasks/employees/combine", methods=["GET"])
def combine_employees():
    old_username, new_username = request.args["old"], request.args["new"]
    if not old_username:
        return Response(
            response="{} is not a valid username".format(old_username), status=400
        )
    elif not new_username:
        return Response(
            response="{} is not a valid username".format(new_username), status=400
        )

    logic.employee.combine_employees(old_username, new_username)
    return Response(status=200)


# @app.route("/tasks/index/rebuild", methods=["GET"])
# def rebuild_index():
#     logic.employee.rebuild_index()
#     return Response(status=200)


@app.route("/tasks/love/email", methods=["POST"])
def email_love():
    # print(request.get_data(as_text=True))
    payload = json.loads(request.get_data(as_text=True).replace("'", '"'))
    # payload = json.loads(payload.replace("'", "\""))
    love_id = int(payload["id"])
    love = ndb.Key(Love, love_id).get()
    logic.love.send_love_email(love)
    return Response(status=200)


@app.route("/tasks/love_count/rebuild", methods=["GET"])
def rebuild_love_count():
    logic.love_count.rebuild_love_count()
    return Response(status=200)


@app.route("/tasks/subscribers/notify", methods=["POST"])
def notify_subscribers():
    payload = json.loads(request.get_data(as_text=True).replace("'", '"'))
    # payload = json.loads(payload)
    # payload = json.loads(payload.replace("'", "\""))
    # x = request.json
    notifier = logic.notifier.notifier_for_event(payload["event"])(**payload["options"])
    notifier.notify()
    return Response(status=200)


@app.route("/tasks/lovelinks/cleanup", methods=["GET"])
def lovelinks_cleanup():
    logic.love_link.love_links_cleanup()
    return Response(status=200)
