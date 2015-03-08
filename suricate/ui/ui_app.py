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
from bottle import template

from suricate.ui import api


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

        # API
        self.api = api.API(amqp_uri, mongo_uri)

        # Routing
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
        self.app.route('/data/object/<iden>/delete', ['POST'],
                       self.delete_data_obj)
        self.app.route('/data/object/<iden>/download', ['GET'],
                       self.download_data_obj)
        self.app.route('/data/stream/new', ['POST'],
                       self.create_data_stream)
        self.app.route('/data/stream/<iden>', ['GET'],
                       self.retrieve_data_stream)
        self.app.route('/data/stream/<iden>/delete', ['POST'],
                       self.delete_data_stream)
        # project mgmt
        self.app.route('/analytics', ['GET'],
                       self.list_projects)
        self.app.route('/analytics/clear', ['POST'],
                       self.clear_job_list)
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
        self.app.route('/analytics/<proj_name>/<ntb_id>/action', ['POST'],
                       self.action_notebook)
        self.app.route('/analytics/<proj_name>/<ntb_id>/interact', ['POST'],
                       self.interact)
        # tagging
        self.app.route('/tag/<data_src>/<iden>', ['POST'],
                       self.tag_item)

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
        uid, token = _get_cred()
        jobs = self.api.list_jobs(uid, token)
        data_info = self.api.info_data(uid, token)
        return {'uid': uid,
                'jobs': jobs,
                'data_info': data_info}

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
        objs, streams = self.api.list_data_sources(uid, token)
        return {'data_objs': objs, 'data_streams': streams, 'uid': uid}

    def create_data_obj(self):
        """
        Create a new data source.
        """
        uid, token = _get_cred()
        upload = bottle.request.files.get('upload')
        fname = bottle.request.files.get('upload').filename
        _, ext = os.path.splitext(upload.filename)

        if ext == '.json':
            tmp = json.loads(upload.file.read().decode('utf-8-sig'))
        elif ext == '.csv':
            reader = csv.reader(upload.file, delimiter=',', quotechar='"')
            keys = next(reader)
            out = [{key: val for key, val in zip(keys, prop)}
                   for prop in reader]
            tmp = json.dumps(out)
        else:
            return 'File extension not supported.'

        meta = {'name': fname,
                'mime-type': 'application/json',
                'tags': []}

        self.api.create_object(tmp, uid, token, meta_dat=meta)
        bottle.redirect('/data')

    @bottle.view('data_object.tmpl')
    def retrieve_data_obj(self, iden):
        """
        Retrieve single data source.

        :param iden: Data source identifier.
        """
        uid, token = _get_cred()
        obj = self.api.retrieve_object(iden, uid, token)
        return {'obj_name': obj['meta']['name'],
                'content': obj['value'],
                'uid': uid}

    def delete_data_obj(self, iden):
        """
        Delete data source.

        :param iden: Data source identifier.
        """
        uid, token = _get_cred()
        self.api.delete_object(iden, uid, token)
        bottle.redirect('/data')

    def download_data_obj(self, iden):
        """
        Download data source.

        :param iden: Data source identifier.
        """
        uid, token = _get_cred()
        tmp = self.api.retrieve_object(iden, uid, token)
        bottle.response.set_header('Content-Type', 'application/json')
        bottle.response.set_header('Content-Disposition',
                                   'inline; filename=data.json')
        return tmp['value']

    def create_data_stream(self):
        """
        Setup a new data stream.
        """
        uid, token = _get_cred()
        uri = bottle.request.forms.get('uri')
        queue = bottle.request.forms.get('queue')
        self.api.create_stream(uri, queue, uid, token)
        bottle.redirect('/data')

    @bottle.view('data_stream.tmpl')
    def retrieve_data_stream(self, iden):
        """
        Retrieve stream details.

        :param iden: Identifier of the stream.
        """
        uid, token = _get_cred()
        uri, queue, msgs = self.api.retrieve_stream(iden, uid, token)
        return {'iden': iden, 'uri': uri, 'queue': queue, 'msgs': msgs,
                'val': len(msgs), 'uid': uid}

    def delete_data_stream(self, iden):
        """
        Remove a data stream.

        :param iden: Identifier of the stream.
        """
        uid, token = _get_cred()
        self.api.delete_stream(iden, uid, token)
        bottle.redirect('/data')

    def tag_item(self, data_src, iden):
        """
        Tag an data object.

        :param data_src: Reflects to database.
        :param iden: Identifier of object/stream.
        """
        uid, token = _get_cred()
        tags = bottle.request.forms.get('tags').split(',')
        tags = [item.strip() for item in tags]
        self.api.set_meta(data_src, iden, tags, uid, token)
        bottle.redirect(bottle.request.headers.get('Referer'))

    # Project mgmt

    @bottle.view('projects.tmpl')
    def list_projects(self):
        """
        List projects.
        """
        uid, token = _get_cred()
        tmp = self.api.list_projects(uid, token)
        return {'uid': uid,
                'projects': tmp}

    def create_project(self):
        """
        Create a project.
        """
        uid, token = _get_cred()
        proj_name = bottle.request.forms.get('proj_name')
        self.api.create_notebook(proj_name, uid, token)
        bottle.redirect('/analytics/' + proj_name)

    @bottle.view('project.tmpl')
    def retrieve_project(self, proj_name):
        """
        Retrieve a single project.

        :param proj_name: name of the project.
        """
        uid, token = _get_cred()
        tmp = self.api.retrieve_project(proj_name, uid, token)
        return {'uid': uid,
                'proj_name': proj_name,
                'notebooks': tmp}

    def delete_project(self, proj_name):
        """
        Delete a single project.

        :param proj_name: name of the project.
        """
        uid, token = _get_cred()
        self.api.delete_project(proj_name, uid, token)
        bottle.redirect('/analytics')

    # Notebook mgmt.

    def create_notebook(self, proj_name):
        """
        Create a new notebook.

        :param proj_name: name of the project.
        """
        uid, token = _get_cred()
        ntb_name = bottle.request.forms.get('iden')
        upload = bottle.request.files.get('upload')
        code = '\n'
        if upload is not None:
            _, ext = os.path.splitext(upload.filename)
            if ext not in '.py':
                return 'File extension not supported.'

            code = upload.file.read()

        self.api.create_notebook(proj_name, uid, token, ntb_name=ntb_name,
                                 src=code)

        bottle.redirect('/analytics/' + proj_name)

    @bottle.view('notebook.tmpl')
    def retrieve_notebook(self, proj_name, ntb_id):
        """
        Retrieve a notebook.

        :param proj_name: name of the project.
        :param ntb_id: Identifier for the notebook.
        """
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

        rend = template(tmp['dashboard_template'], error=err, output=output)

        return {'uid': uid,
                'proj_name': proj_name,
                'ntb_name': tmp['meta']['name'],
                'ntb_id': ntb_id,
                'src': src,
                'rendered_dashboard': rend}

    def delete_notebook(self, proj_name, ntb_id):
        """
        Delete a notebook.

        :param proj_name: name of the project.
        :param ntb_id: Identifier for the notebook.
        """
        uid, token = _get_cred()
        self.api.delete_notebook(proj_name, ntb_id, uid, token)
        bottle.redirect('/analytics/' + proj_name)

    def download_notebook(self, proj_name, ntb_id):
        """
        Download a notebook.

        :param proj_name: name of the project.
        :param ntb_id: Identifier for the notebook.
        """
        uid, token = _get_cred()
        tmp_file = StringIO()
        ntb = self.api.retrieve_notebook(proj_name, ntb_id, uid, token)
        tmp_file.write(ntb['src'])

        # will force browsers to download...
        bottle.response.set_header('Content-Type', 'ext/x-script.python')
        bottle.response.set_header('Content-Disposition',
                                   'inline; filename=notebook.py')
        return tmp_file.getvalue()

    def action_notebook(self, proj_name, ntb_id):
        """
        Perform action on a notebook.

        :param proj_name: name of the project.
        :param ntb_id: Identifier for the notebook.
        """
        uid, token = _get_cred()
        src = bottle.request.forms.get('source')
        action = bottle.request.forms.get('run')
        if action == 'Save':
            self.api.update_notebook(proj_name, ntb_id, src, uid, token)
            bottle.redirect('/analytics/' + proj_name + '/' + ntb_id)
        elif action == 'Run':
            self.api.run_notebook(proj_name, ntb_id, src, uid, token)
            bottle.redirect('/analytics/' + proj_name + '/' + ntb_id)
        elif action == 'Run Job':
            self.api.run_job(proj_name, ntb_id, src, uid, token)
            bottle.redirect('/')

    def interact(self, proj_name, ntb_id):
        """
        Interact with a notebook's interpreter.

        :param proj_name: name of the project.
        :param ntb_id: Identifier for the notebook.
        """
        uid, token = _get_cred()
        loc = bottle.request.forms.get('interact')
        self.api.interact(proj_name, ntb_id, loc, uid, token)
        bottle.redirect('/analytics/' + proj_name + '/' + ntb_id)

    def clear_job_list(self):
        """
        Clear job list.
        """
        uid, token = _get_cred()
        self.api.clear_job_list(uid, token)
        bottle.redirect('/')


def _get_cred():
    """
    Retrieve user credentials.

    :return: Set of credentials for this request.
    """
    uid = bottle.request.get_header('X-Uid')
    pwd = bottle.request.get_header('X-Token')
    return uid, pwd
