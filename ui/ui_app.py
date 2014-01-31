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

from data import object_store
from data import streaming
from ui import api


class AnalyticsApp(object):
    """
    Analytics Web Application. WSGI app can be retrieved by calling
    'get_wsgi_app'.
    """

    def __init__(self, mongo_uri, amqp_uri):
        """
        Initialize the Web Application

        :param mongo_uri: Connection details for MongoDB.
        :param amqp_uri: Connection details for RabbitMQ broker.
        """
        # configure bottle
        self.app = bottle.Bottle()
        self.pth = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))

        # get obj store up!
        # TODO: look into supporting other store ntb_types.
        self.obj_str = object_store.MongoStore(mongo_uri)
        self.stream = streaming.AMQPClient(mongo_uri)

        self.api = api.API(amqp_uri)
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
        self.app.route('/data/object/new', ['POST'],
                       self.create_data_obj)
        self.app.route('/data/object/<iden>', ['GET'],
                       self.retrieve_data_obj)
        self.app.route('/data/object/delete/<iden>', ['POST'],
                       self.delete_data_obj)
        self.app.route('/data/stream/new', ['POST'],
                       self.create_data_stream)
        self.app.route('/data/stream/<iden>', ['GET'],
                       self.retrieve_data_stream)
        self.app.route('/data/stream/delete/<iden>', ['POST'],
                       self.delete_data_stream)
        # project mgmt
        self.app.route('/analytics', ['GET'],
                       self.projects)
        self.app.route('/analytics/create', ['POST'],
                       self.create_project)
        self.app.route('/analytics/<proj_name>', ['GET'],
                       self.retrieve_project)
        self.app.route('/analytics/<proj_name>/delete', ['POST'],
                       self.delete_project)
        # notebook management
        self.app.route('/analytics/<proj_name>/create', ['POST'],
                       self.create_notebook)
        self.app.route('/analytics/<proj_name>/<ntb_id>', ['GET'],
                       self.retrieve_notebook)
        self.app.route('/analytics/<proj_name>/<ntb_id>/delete', ['POST'],
                       self.delete_notebook)
        self.app.route('/analytics/<proj_name>/<ntb_id>/download', ['POST'],
                       self.download_notebook)
        self.app.route('/analytics/<proj_name>/<ntb_id>/run', ['POST'],
                       self.run_notebook)
        self.app.route('/analytics/<proj_name>/<ntb_id>/interact', ['POST'],
                       self.interact)
        # self.app.route('/analytics/<proj_name>/<ntb_id>/tag', ['POST'],
        #                self.tag_notebook)

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
        _, ext = os.path.splitext(upload.filename)

        if ext == '.json':
            tmp = upload.file.getvalue()
        elif ext == '.csv':
            reader = csv.reader(upload.file, delimiter=',', quotechar='"')
            keys = next(reader)
            out = [{key: val for key, val in zip(keys, prop)}
                   for prop in reader]
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

    # Project mgmt

    @bottle.view('projects.tmpl')
    def projects(self):
        uid, token = _get_cred()
        tmp = self.api.list_projects(uid, token)
        return {'uid': uid,
                'projects': tmp}

    def create_project(self):
        uid, token = _get_cred()
        proj_name = bottle.request.forms.get('proj_name')
        self.api.create_project(proj_name, uid, token)
        bottle.redirect('/analytics/' + proj_name)

    @bottle.view('project.tmpl')
    def retrieve_project(self, proj_name):
        uid, token = _get_cred()
        tmp = self.api.retrieve_project(proj_name, uid, token)
        return {'uid': uid,
                'proj_name': proj_name,
                'notebooks': tmp}

    def delete_project(self, proj_name):
        uid, token = _get_cred()
        self.api.delete_project(proj_name, uid, token)
        bottle.redirect('/analytics')

    # Notebook mgmt.

    def create_notebook(self, proj_name):
        uid, token = _get_cred()
        ntb_id = bottle.request.forms.get('iden')
        upload = bottle.request.files.get('upload')
        ntb = {'meta': {}, 'src': '\n'}
        if upload is not None:
            _, ext = os.path.splitext(upload.filename)
            if ext not in '.py':
                return 'File extension not supported.'

            code = upload.file.read()
            ntb['src'] = code

        self.api.update_notebook(proj_name, ntb_id, ntb, uid, token)

        bottle.redirect('/analytics/' + proj_name + '/' + ntb_id)

    @bottle.view('notebook.tmpl')
    def retrieve_notebook(self, proj_name, ntb_id):
        uid, token = _get_cred()
        tmp = self.api.retrieve_notebook(proj_name, ntb_id, uid, token)
        if 'out' in tmp:
            output = tmp['out']
        else:
            output = ''
        src = tmp['src']
        if 'err' in tmp:
            err = tmp['err']
        else:
            err = ''
        return {'uid': uid,
                'proj_name': proj_name,
                'ntb_id': ntb_id,
                'src': src,
                'output': output,
                'error': err}

    def delete_notebook(self, proj_name, ntb_id):
        uid, token = _get_cred()
        self.api.delete_notebook(proj_name, ntb_id, uid, token)
        bottle.redirect('/analytics/' + proj_name)

    def download_notebook(self, proj_name, ntb_id):
        uid, token = _get_cred()
        tmp_file = StringIO()
        ntb = self.api.retrieve_notebook(proj_name, ntb_id, uid, token)
        tmp_file.write(ntb['src'])

        # will force browsers to download...
        bottle.response.set_header('Content-Type', 'ext/x-script.python')
        bottle.response.set_header('content-disposition',
                                   'inline; filename=notebook.py')
        return tmp_file.getvalue()

    def run_notebook(self, proj_name, ntb_id):
        uid, token = _get_cred()
        src = bottle.request.forms.get('source')
        self.api.run_notebook(proj_name, ntb_id, src, uid, token)
        bottle.redirect('/analytics/' + proj_name + '/' + ntb_id)

    def interact(self, proj_name, ntb_id):
        uid, token = _get_cred()
        loc = bottle.request.forms.get('interact')
        self.api.interact(proj_name, ntb_id, loc, uid, token)
        bottle.redirect('/analytics/' + proj_name + '/' + ntb_id)


def _get_cred():
    """
    Retrieve user credentials.

    :return: Set of credentials for this request.
    """
    uid = bottle.request.get_header('X-Uid')
    pwd = bottle.request.get_header('X-Token')
    return uid, pwd