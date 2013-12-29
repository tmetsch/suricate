#!/usr/bin/env python

# coding=utf-8

"""
Runs the analytics service in a development environment.
"""

__author__ = 'tmetsch'

import bottle
import os
import pymongo
import subprocess
import sys

import ConfigParser

from web import ui_app

config = ConfigParser.RawConfigParser()
config.read('app.conf')
# MongoDB connection
host = config.get('mongo', 'host')
port = config.get('mongo', 'port')
adm = config.get('mongo', 'admin')
pwd = config.get('mongo', 'pwd')
# Rabbit broker
broker = config.get('rabbit', 'uri')

# dict with <username>:(<token>,<db_exists>)
USERS = {'foo': ('bar', False)}


def check_database(user):
    """
    Checks if database for a user exists, if not creates it.

    :param user: username.
    """
    if USERS[user][1]:
        return

    # authenticate as user admin...
    uri = 'mongodb://' + adm + ':' + pwd + '@' + host + ':' + port + '/admin'
    client = pymongo.MongoClient(uri)

    # if user doesn't exist create new DB!
    if user not in client.database_names():
        db = client[user]
        db.add_user(user, USERS[user][0], roles=['readWrite'])
        USERS[user] = (USERS[user][0], True)
    else:
        USERS[user] = (USERS[user][0], True)
    client.disconnect()


def authorize(user):
    """
    Authorize a user.

    :param user: user name.
    :return: True or False.
    """
    if user in USERS.keys():
        check_database(user)
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
        user = 'foo'
        if authorize(user):
            environ['HTTP_X_UID'] = user
            environ['HTTP_X_TOKEN'] = USERS[user][0]
            return self.wrap_app(environ, start_response)

if __name__ == '__main__':
    # start execution node for each user.
    processes = []
    for user in USERS.keys():
        p = subprocess.Popen([sys.executable, 'run_exec.py', user])
        processes.append(p)

    # launch web app
    mongo = 'mongodb://' + host + ':' + port
    app = ui_app.AnalyticsApp(mongo, broker).get_wsgi_app()
    app = SessionMiddleWare(app)

    bottle.TEMPLATE_PATH.insert(0, '../web/views')
    bottle.run(app=app, host='localhost')

    # let's cleanup shall we?
    for process in processes:
        process.kill()
