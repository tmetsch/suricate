# coding=utf-8
'''
API implementation.
'''

__author__ = 'tmetsch'

import bottle


class RestApi(object):
    '''
    Analytics Web Application. WSGI app can be retrieved by calling
    'get_wsgi_app'.
    '''

    def __init__(self, uri):
        '''
        Initialize the Web Application

        # TODO: uri for obj and notebook str.
        :param uri: Connection details for MongoDB.
        '''
        self.app = bottle.Bottle()
        self._setup_routing()

    def _setup_routing(self):
        # notebook management.
        self.app.route('/processing/notebooks', ['GET'], self.list_notebooks)
        # self.app.route('/processing/notebooks', ['POST'],
        # self.list_notebooks)
        self.app.route('/processing/notebooks/<iden>', ['GET'],
                       self.list_notebooks)
        self.app.route('/processing/notebooks/<iden>/action', ['POST'],
                       self.list_notebooks)
        # data objs

        # data streams

    def get_wsgi_app(self):
        '''
        Return the WSGI app.
        '''
        return self.app

    def list_notebooks(self):
        '''
        List notebooks.
        '''
        body = {'notebooks': [{'iden': '1', 'href': ''}]}
        return body