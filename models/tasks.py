# -*- coding: utf-8 -*-
from google.cloud import tasks_v2
import config


class Tasks:
    def __init__(self, queue='default'):
        self.project = config.PROJECT_NAME
        self.queue = queue
        self.location = 'us-west2'

    def create_task(self, payload, task):
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(self.project, self.location, self.queue)
        if payload:
            converted_payload = str(payload).encode()
            task['app_engine_http_request']['body'] = converted_payload
        client.create_task(parent, task)
        return
