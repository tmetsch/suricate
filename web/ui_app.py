# coding=utf-8

"""
Main WSGI based app.

Assumes that there is an 'UID' & TOKEN key in the environ. Please make sure
that the WSGI middleware adds this.
"""

__author__ = 'tmetsch'

import bottle
import csv
import inspect
import json
import os

from StringIO import StringIO

import api

import data.object_store
import data.streaming


class AnalyticsApp(object):
    """
    Analytics Web Application. WSGI app can be retrieved by calling
    'get_wsgi_app'.
    """

    def __init__(self, uri):
        """
        Initialize the Web Application

        # TODO: uri for obj and notebook str.
        :param uri: Connection details for MongoDB.
        """
        self.app = bottle.Bottle()

        self.pth = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))

        # TODO: look into supporting other store ntb_types.
        self.obj_str = data.object_store.MongoStore(uri)
        self.stream = data.streaming.AMQPClient(uri)

        self.api = api.API()
        self._setup_routing()

    def _setup_routing(self):
        """
        Setup the routing.
        """
        # basic
        self.app.route('/', ['GET'], self.index)
        self.app.route('/static/<filepath:path>', ['GET'], self.static)
        # data
        self.app.route('/data', ['GET'],
                       self.list_data_sources)
        self.app.route('/data/object/<iden>', ['GET'],
                       self.retrieve_data_obj)
        self.app.route('/data/object/new', ['POST'],
                       self.create_data_obj)
        self.app.route('/data/object/delete/<iden>', ['POST'],
                       self.delete_data_obj)
        self.app.route('/data/stream/<iden>', ['GET'],
                       self.retrieve_data_stream)
        self.app.route('/data/stream/new', ['POST'],
                       self.create_data_stream)
        self.app.route('/data/stream/delete/<iden>', ['POST'],
                       self.delete_data_stream)
        # analytics
        self.app.route('/analytics', ['GET'],
                       self.list_notebooks)
        self.app.route('/analytics/<iden>', ['GET'],
                       self.retrieve_notebook)
        self.app.route('/analytics/<iden>/add/<line_id>', ['POST'],
                       self.add_item_to_notebook)
        self.app.route('/analytics/<iden>/edit/<line_id>', ['GET'],
                       self.edit_item_in_notebook)
        self.app.route('/analytics/<iden>/remove/<line_id>', ['POST'],
                       self.remove_item_from_notebook)
        self.app.route('/analytics/upload', ['POST'],
                       self.create_notebook)
        self.app.route('/analytics/rerun/<iden>', ['POST'],
                       self.rerun_notebook)
        self.app.route('/analytics/download/<iden>', ['GET'],
                       self.download_notebook)
        self.app.route('/analytics/delete/<iden>', ['POST'],
                       self.delete_notebook)
        # processing
        self.app.route('/processing', ['GET'],
                       self.list_notebooks)
        self.app.route('/processing/<iden>', ['GET'],
                       self.retrieve_notebook)
        self.app.route('/processing/<iden>/add/<line_id>', ['POST'],
                       self.add_item_to_notebook)
        self.app.route('/processing/<iden>/edit/<line_id>', ['GET'],
                       self.edit_item_in_notebook)
        self.app.route('/processing/<iden>/remove/<line_id>', ['POST'],
                       self.remove_item_from_notebook)
        self.app.route('/processing/upload', ['POST'],
                       self.create_notebook)
        self.app.route('/processing/rerun/<iden>', ['POST'],
                       self.rerun_notebook)
        self.app.route('/processing/download/<iden>', ['GET'],
                       self.download_notebook)
        self.app.route('/processing/delete/<iden>', ['POST'],
                       self.delete_notebook)

    def get_wsgi_app(self):
        """
        Return the WSGI app.
        """
        return self.app

    # Generic part

    @bottle.view('index.tmpl')
    def index(self):
        """
        Initial view.
        """
        uid, _ = _get_cred()
        return {'uid': uid}

    def static(self, filepath):
        """
        Serve static files.
        :param filepath:
        """
        return bottle.static_file('/static/' + filepath, root=self.pth)

    # Data

    @bottle.view('data_srcs.tmpl')
    def list_data_sources(self):
        """
        List all data sources.
        """
        uid, token = _get_cred()
        tmp = self.obj_str.list_objects(uid, token)
        tmp2 = self.stream.list_streams(uid, token)
        return {'data_objs': tmp, 'data_streams': tmp2, 'uid': uid}

    def create_data_obj(self):
        """
        Create a new data source.
        """
        uid, token = _get_cred()
        upload = bottle.request.files.get('upload')
        name, ext = os.path.splitext(upload.filename)

        if ext == '.json':
            tmp = upload.file.getvalue()
        elif ext == '.csv':
            reader = csv.reader(upload.file, delimiter=',', quotechar='"')
            keys = next(reader)
            out = [{key: val for key, val in zip(keys, prop)} for prop in reader]
            tmp = json.dumps(out)
        else:
            return 'File extension not supported.'

        self.obj_str.create_object(uid, token, tmp)
        bottle.redirect('/data')

    @bottle.view('data_object.tmpl')
    def retrieve_data_obj(self, iden):
        """
        Retrieve single data source.

        :param iden: Data source identifier.
        """
        uid, token = _get_cred()
        tmp = self.obj_str.retrieve_object(uid, token, iden)
        return {'iden': iden, 'content': tmp, 'uid': uid}

    def delete_data_obj(self, iden):
        """
        Delete data source.

        :param iden: Data source identifier.
        """
        uid, token = _get_cred()
        self.obj_str.delete_object(uid, token, iden)
        bottle.redirect('/data')

    def create_data_stream(self):
        """
        Setup a new data stream.
        """
        uid, token = _get_cred()
        uri = bottle.request.forms.get('uri')
        queue = bottle.request.forms.get('queue')
        self.stream.create(uid, token, uri, queue)
        bottle.redirect('/data')

    @bottle.view('data_stream.tmpl')
    def retrieve_data_stream(self, iden):
        """
        Retrieve stream details.

        :param iden: Identifier of the stream.
        """
        uid, token = _get_cred()
        uri, queue, msgs = self.stream.retrieve(uid, token, iden)
        return {'iden': iden, 'uri': uri, 'queue': queue, 'msgs': msgs,
                'val': len(msgs), 'uid': uid}

    def delete_data_stream(self, iden):
        """
        Remove a data stream.

        :param iden: Identifier of the stream.
        """
        uid, token = _get_cred()
        self.stream.delete(uid, token, iden)
        bottle.redirect('/data')

    # Analytics/Processing part

    @bottle.view('notebooks.tmpl')
    def list_notebooks(self):
        """
        Lists all notebooks.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        tmp = self.api.list_notebooks(uid, token, ntb_type)

        return {'notebooks': tmp, 'ntb_type': ntb_type, 'uid': uid}

    def create_notebook(self):
        """
        Create a new notebook.

        When code is uploaded add it to the notebook.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        iden = bottle.request.forms.get('iden')
        upload = bottle.request.files.get('upload')
        code = []
        if upload is not None:
            _, ext = os.path.splitext(upload.filename)
            if ext not in '.py':
                return 'File extension not supported.'

            code = upload.file.getvalue().split('\n')

        self.api.create_notebook(uid, token, ntb_type, iden, init_code=code)

        bottle.redirect('/' + ntb_type)

    @bottle.view('notebook.tmpl')
    def retrieve_notebook(self, iden):
        """
        Enables interactions with one notebook.

        :param iden: Notebook identifier.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        res, indent = self.api.retrieve_notebook(uid, token, ntb_type, iden)

        return {'iden': iden, 'output': res, 'indent': indent,
                'ntb_type': ntb_type, 'uid': uid}

    def delete_notebook(self, iden):
        """
        Delete a notebook.

        :param iden: Notebook identifier.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        self.api.delete_notebook(uid, token, ntb_type, iden)

        bottle.redirect('/' + ntb_type)

    def add_item_to_notebook(self, iden, line_id):
        """
        Add a item to a notebook.

        :param line_id: Identifier of last line.
        :param iden: Notebook identifier.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        cmd = bottle.request.forms['cmd']
        indent = bottle.request.forms['indent']
        if cmd == '':
            # finally execute old open block of code
            self.api.update_item_in_notebook(uid, token, ntb_type, iden, line_id,
                                        '\r\n', replace=False)
        elif len(indent) != 0:
            # add to open block of code
            self.api.update_item_in_notebook(uid, token, ntb_type, iden, line_id,
                                        '\r\n' + cmd.rstrip('\n'),
                                        replace=False)
        else:
            # or just add
            self.api.add_item_to_notebook(uid, token, ntb_type, iden, cmd)

        bottle.redirect('/' + ntb_type + '/' + iden)

    @bottle.view('edit_code.tmpl')
    def edit_item_in_notebook(self, iden, line_id):
        """
        Edit an item in a notebook.

        :param iden: Notebook identifier.
        :param line_id: Identifier of the loc.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        if bottle.request.GET.get('save', '').strip():
            line = bottle.request.GET.get('cmd', '').strip()
            self.api.update_item_in_notebook(uid, token, ntb_type, iden, line_id, line)
            bottle.redirect('/' + ntb_type + '/' + iden)
        else:
            src, _ = self.api.retrieve_notebook(uid, token, ntb_type, iden)
            code = src[line_id]
            return {'url': iden, 'old': code, 'line_id': line_id,
                    'ntb_type': ntb_type, 'uid': uid}

    def remove_item_from_notebook(self, iden, line_id):
        """
        Remove an item from a notebook.

        :param iden: Notebook identifier.
        :param line_id: Identifier of the loc.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        self.api.delete_item_of_notebook(uid, token, ntb_type, iden, line_id)

        bottle.redirect('/' + ntb_type + '/' + iden)

    def rerun_notebook(self, iden):
        """
        Rerun a notebook.json

        :param iden: Notebook identifier.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        self.api.notebook_event(uid, token, ntb_type, iden, 'rerun')

        bottle.redirect('/' + ntb_type + '/' + iden)

    def download_notebook(self, iden):
        """
        Download a notebook.

        :param iden: Notebook identifier.
        """
        uid, token = _get_cred()
        ntb_type = _get_ntb_ntb_type()

        src, _ = self.api.retrieve_notebook(uid, token, ntb_type, iden)


        tmp_file = StringIO()
        # TODO: fix preload
        for item in src.values():
            tmp = item[0]
            line = tmp + '\n'
            line = line.replace('\t', '')
            if line[0] != ' ':
                line += '\n'
            tmp_file.write(line)

        # will force browsers to download...
        bottle.response.set_header('Content-ntb_type', 'ext/x-script.python')
        bottle.response.set_header('content-disposition',
                                   'inline; filename=notebook.py')
        return tmp_file.getvalue()


def _get_ntb_ntb_type():
    """
    Return the notebook backend - either analytics or processing.

    :return: Returns a notebook store.
    """
    path = bottle.request.path.lstrip('/')
    if path.find('analytics') == 0:
        return 'analytics'
    elif path.find('processing') == 0:
        return 'processing'


def _get_cred():
    """
    Retrieve user credentials.

    :return: Set of credentials for this request.
    """
    uid = bottle.request.get_header('X-Uid')
    pw = bottle.request.get_header('X-Token')
    return uid, pw
