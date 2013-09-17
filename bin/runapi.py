# coding=utf-8

'''
Runs WSGI API.
'''

import ConfigParser

__author__ = 'tmetsch'

import bottle
from runme import SessionMiddleWare

from api import wsgi_app

config = ConfigParser.RawConfigParser()
config.read('app.conf')
# MongoDB connection
host = config.get('mongo', 'host')
port = config.get('mongo', 'port')
adm = config.get('mongo', 'admin')
pwd = config.get('mongo', 'pwd')

if __name__ == '__main__':
    app = wsgi_app.RestApi('mongodb://' + host + ':' + port).get_wsgi_app()
    app = SessionMiddleWare(app)

    bottle.run(app=app, host='localhost', port=8888)
