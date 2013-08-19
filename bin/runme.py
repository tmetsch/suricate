# coding=utf-8

#   Copyright 2012-2013 Thijs Metsch - engjoy UG (haftungsbeschraenkt)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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