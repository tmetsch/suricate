# coding=utf-8

'''
Runs the AaaS in a development environment.
'''

__author__ = 'tmetsch'

import bottle
import pymongo

import ConfigParser

from web import wsgi_app

config = ConfigParser.RawConfigParser()
config.read('app.conf')
# MongoDB connection
host = config.get('mongo', 'host')
port = config.get('mongo', 'port')
adm = config.get('mongo', 'admin')
pwd = config.get('mongo', 'pwd')

# dict with <username>:<token>
USERS = {'foo': 'bar'}


def check_database(user, pw):
    '''
    Checks if database for a user exists, if not creates it.

    :param pw: pw of ther user.
    :param user: username.
    '''
    # authenticate as user admin...
    uri = 'mongodb://' + adm + ':' + pwd + '@' + host + ':' + port + '/admin'
    client = pymongo.MongoClient(uri)

    # if user doesn't exist create new DB!
    if user not in client.database_names():
        db = client[user]
        db.add_user(user, pw, roles=['readWrite'])
    client.disconnect()


def authorize(user):
    """
    Authorize a user.

    :param user: user name.
    :return: True or False.
    """
    if user in USERS.keys():
        check_database(user, USERS[user])
        return True
    else:
        return False


class SessionMiddleWare(object):
    '''
    Demo Session middleware adding the required environment id.
    '''

    def __init__(self, app_to_wrap):
        self.wrap_app = app_to_wrap

    def __call__(self, environ, start_response):
        user = 'foo'
        if authorize(user):
            environ['HTTP_X_UID'] = user
            environ['HTTP_X_TOKEN'] = USERS[user]
            return self.wrap_app(environ, start_response)

app = wsgi_app.AnalyticsApp('mongodb://' + host + ':' + port).get_wsgi_app()
app = SessionMiddleWare(app)

bottle.TEMPLATE_PATH.insert(0, '../web/views')
bottle.run(app=app, host='localhost')
