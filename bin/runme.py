# coding=utf-8

'''
Runs the AaaS in a development environment.
'''

__author__ = 'tmetsch'

import bottle

from web import wsgi_app


class SessionMiddleWare(object):
    '''
    Demo Session middleware adding the required environment id.
    '''

    def __init__(self, app_to_wrap):
        self.wrap_app = app_to_wrap

    def __call__(self, environ, start_response):
        environ['HTTP_X_UID'] = '123'
        return self.wrap_app(environ, start_response)


app = wsgi_app.application
app = SessionMiddleWare(app)

bottle.TEMPLATE_PATH.insert(0, '../web/views')
bottle.run(app=app, host='localhost')