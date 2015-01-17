#!/usr/bin/env python

# coding=utf-8

"""
Runs the analytics service in a development environment.
"""

__author__ = 'tmetsch'

import ConfigParser

import bottle
import pymongo
import subprocess
import sys

from urlparse import urlparse
from suricate.ui import ui_app


config = ConfigParser.RawConfigParser()
config.read('app.conf')
# MongoDB connection
mongo = config.get('mongo', 'uri')
adm = config.get('mongo', 'admin')
pwd = config.get('mongo', 'pwd')
# Rabbit broker
broker = config.get('rabbit', 'uri')

# dict with <username>:(<token>,<db_exists>)
USERS = {'foo': ('bar', False)}


def check_database(user_id):
    """
    Checks if database for a user exists, if not creates it.

    :param user_id: username.
    """
    if USERS[user_id][1]:
        return

    # authenticate as user admin...
    tmp = urlparse(mongo)
    uri = 'mongodb://' + adm + ':' + pwd + '@' + tmp.hostname + ':' + \
          str(tmp.port) + '/admin'
    client = pymongo.MongoClient(uri)

    # if user doesn't exist create new DB!
    if user_id not in client.database_names():
        db = client[user_id]
        db.add_user(user_id, USERS[user_id][0], roles=['readWrite'])
        USERS[user_id] = (USERS[user_id][0], True)
    else:
        USERS[user_id] = (USERS[user_id][0], True)
    client.disconnect()


def authorize(user_id):
    """
    Authorize a user.

    :param user_id: user name.
    :return: True or False.
    """
    if user_id in USERS.keys():
        check_database(user_id)
        return True
    else:
        return False


class SessionMiddleWare(object):
    """
    Demo Session middleware adding the required environment id.
    """

    def __init__(self, app_to_wrap):
        self.wrap_app = app_to_wrap

    def __call__(self, environ, start_response):
        user_id = 'foo'
        if authorize(user_id):
            environ['HTTP_X_UID'] = user_id
            environ['HTTP_X_TOKEN'] = USERS[user_id][0]
            return self.wrap_app(environ, start_response)

if __name__ == '__main__':
    # start execution node for each user.
    processes = []
    for user in USERS.keys():
        p = subprocess.Popen([sys.executable, 'run_exec.py', user])
        processes.append(p)

    # launch web app
    app = ui_app.AnalyticsApp(mongo, broker).get_wsgi_app()
    app = SessionMiddleWare(app)

    bottle.TEMPLATE_PATH.insert(0, '../suricate/ui/views')
    bottle.run(app=app, host='localhost')

    # let's cleanup shall we?
    for process in processes:
        process.kill()
