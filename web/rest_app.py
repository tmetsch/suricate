# coding=utf-8

"""
RESTful API implementation.
"""

__author__ = 'tmetsch'

import bottle


class RestApi(object):
    """
    RESTful API.

    WSGI app can be retrieved by calling 'get_wsgi_app'.
    """

    def __init__(self):
        """
        Initialize the RESTful API.
        """
        self.app = bottle.Bottle()
        self._setup_routing()

    def _setup_routing(self):
        """
        Setup routing.
        """
        pass

    def get_wsgi_app(self):
        """
        Return the WSGI app.
        """
        return self.app
