"""
To Add a new time-based task:
    - set the task in tasks.route folder as a POST request
    - add a function in THIS file that `waits` until a certain condition and makes a POST requests to the server
    - add a wrapper for the function in TaskManager class. (this function is continuous)
    - add the Thread(target=TaskManager.past_function_wrapper) class in TaskManager.run_tasks
    Note:
        - Imagine sending multiple POST requests from not synced program... You must send `some data` that makes sure no
        error happens. `some data` is checked on the server to make sure the client is not out-synced.
        - Be sure to send the sha256(SECRET_KEY) in JSON
TODO:
    - This scheme is really complex and contains a lot of spaghetti code... A new EXPERT approach is needed
Note:
    For no apparent reason, TaskManager.run_tasks functions runs two times (tested on v0.8) on SEPARATE processes.
    --> Don't Judge o-o
"""
from threading import Thread
from time import sleep
from datetime import timedelta, datetime
import os
from hashlib import sha256
import requests


SECRET_KEY = os.getenv('SECRET_KEY')
sk_hash = sha256(SECRET_KEY.encode('utf-8')).hexdigest()
base_url = 'http://127.0.0.1'


def send_increment_week_duel_request(base_time, week_duel, interval):
    while base_time + interval > datetime.utcnow():
        sleep(5)

    json = {'password': sk_hash,
            'week-duel': week_duel
            }
    url = base_url + "/increment-week-duel"
    request = requests.post(url, json=json)

    return True if request.status_code == 200 else False


class TaskManager:

    @staticmethod
    def send_increment_week_duel_request_wrapper(launch_time, week_duel, interval):
        start_time = launch_time
        while True:
            send_increment_week_duel_request(start_time, week_duel, interval)
            start_time = start_time + interval

    @staticmethod
    def run_tasks():
        sleep(5)  # wait till server initialize
        launch_time, week_duel, base_date = TaskManager.request_data()

        threads = [Thread(target=TaskManager.send_increment_week_duel_request_wrapper,
                          args=(base_date, week_duel, timedelta(days=14)))
                   ]
        for thread in threads:
            thread.start()

        # lock execution
        while True:
            sleep(60)
            continue

    @staticmethod
    def request_data():
        json = {'password': sk_hash,
                'encoding': '%Y %m %d %H %M %S %f'
                }
        url = base_url + "/get-data"
        request = requests.post(url, json=json)
        response = request.text
        if request.status_code != 200:
            raise

        time_str, week_duel, base_date = response.split('\r')
        week_duel = int(week_duel)
        base_date = datetime.strptime(base_date, json['encoding'])
        launch_time = datetime.strptime(time_str, json['encoding'])

        return launch_time, week_duel, base_date
