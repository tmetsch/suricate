# coding=utf-8

'''
Main WSGI based app.

Assumes that there is an 'UID' key in the environ. Please make sure that the
WSGI middleware adds this.
'''

__author__ = 'tmetsch'

import bottle
import os

import ConfigParser

from StringIO import StringIO

import analytics.notebooks
import data.object_store

# Data part
config = ConfigParser.RawConfigParser()
config.read('app.conf')
# Mongo connection
host = config.get('mongo', 'host')
port = config.getint('mongo', 'port')
# TODO: look into supporting other store types.
OBJ_STR = data.object_store.MongoStore(host, port)
NTB_STR = analytics.notebooks.NotebookStore(host, port)


@bottle.view('data_srcs.tmpl')
def list_data_sources():
    '''
    List all data sources.
    '''
    uid = bottle.request.get_header('X-Uid')
    tmp = OBJ_STR.list_objects(uid)
    return {'data_objs': tmp, 'streams': None, 'uid': uid}


def create_data_source():
    '''
    Create a new data source.
    '''
    uid = bottle.request.get_header('X-Uid')
    upload = bottle.request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)
    if ext not in '.json':
        return 'File extension not supported.'

    OBJ_STR.create_object(uid, upload.file.getvalue())
    bottle.redirect('/data')


@bottle.view('data_src.tmpl')
def retrieve_data_source(iden):
    '''
    Retrieve single data source.

    :param iden: Data source identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    tmp = OBJ_STR.retrieve_object(uid, iden)
    return {'iden': iden, 'content': tmp, 'uid': uid}


def delete_data_source(iden):
    '''
    Delete data source.

    :param iden: Data source identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    OBJ_STR.delete_object(uid, iden)
    bottle.redirect('/data')

# Analysis part


@bottle.view('notebooks.tmpl')
def list_notebooks():
    '''
    Lists all notebooks.
    '''
    uid = bottle.request.get_header('X-Uid')
    tmp = NTB_STR.list_notebooks(uid)
    return {'notebooks': tmp, 'uid': uid}


def create_notebook():
    '''
    Create a new notebook.

    When code is uploaded add it to the notebook.
    '''
    uid = bottle.request.get_header('X-Uid')
    iden = bottle.request.forms.get('iden')
    upload = bottle.request.files.get('upload')
    code = []
    if upload is not None:
        name, ext = os.path.splitext(upload.filename)
        if ext not in '.py':
            return 'File extension not supported.'

        code = upload.file.getvalue().split('\n')

    NTB_STR.get_notebook(uid, iden, init_code=code)
    bottle.redirect('/analysis')


@bottle.view('notebook.tmpl')
def retrieve_notebook(iden):
    '''
    Enables interactions with one notebook.

    :param iden: Notebook identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    ntb = NTB_STR.get_notebook(uid, iden)
    res = ntb.get_results()
    return {'iden': iden, 'uid': uid, 'output': res,
            'default': ntb.white_space}


def delete_notebook(iden):
    '''
    Delete a notebook.

    :param iden: Notebook identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    NTB_STR.delete_notebook(uid, iden)
    bottle.redirect('/analysis')


def add_item_to_notebook(iden, old_id):
    '''
    Add a item to a notebook.

    :param old_id: Identifier of last line.
    :param iden: Notebook identifier.
    '''
    cmd = bottle.request.forms['cmd']
    uid = bottle.request.get_header('X-Uid')
    ntb = NTB_STR.get_notebook(uid, iden)
    if cmd == '':
        ntb.update_line(old_id, '\n', replace=False)
    elif len(ntb.white_space) != 0:
        ntb.update_line(old_id, '\n' + cmd, replace=False)
    else:
        ntb.add_line(cmd)
    bottle.redirect('/analysis/' + iden)


@bottle.view('edit_code.tmpl')
def edit_item_in_notebook(iden, line_id):
    '''
    Edit an item in a notebook.

    :param line_id: Identifier of the loc.
    :param iden: Notebook identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    ntb = NTB_STR.get_notebook(uid, iden)
    if bottle.request.GET.get('save', '').strip():
        line = bottle.request.GET.get('cmd', '').strip()
        ntb.update_line(line_id, line)
        bottle.redirect("/analysis/" + iden)
    else:
        code = ntb.src[line_id]
        return {'uid': uid, 'url': iden, 'old': code, 'line_id': line_id}


def remove_item_from_notebook(iden, line_id):
    '''
    Remove an item from a notebook.

    :param line_id: Identifier of the loc.
    :param iden: Notebook identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    ntb = NTB_STR.get_notebook(uid, iden)
    ntb.remove_line(line_id)
    bottle.redirect('/analysis/' + iden)


def download_notebook(iden):
    '''
    Download a notebook.

    :param iden: Notebook identifier.
    '''
    uid = bottle.request.get_header('X-Uid')
    tmp = NTB_STR.get_notebook(uid, iden)
    tmp_file = StringIO()
    for item in analytics.notebooks.PRELOAD.split('\n'):
        tmp_file.write(item + '\n')
    for item in tmp.get_lines():
        line = item + '\n'
        line = line.replace('\t', '')
        if line[0] != ' ':
            line += '\n'
        tmp_file.write(line)
    # will force browsers to download...
    bottle.response.set_header('Content-Type', 'ext/x-script.python')
    bottle.response.set_header('content-disposition',
                               'inline; filename=notebook.py')
    return tmp_file.getvalue()


# Processing


@bottle.view('processing.tmpl')
def list_processings():
    '''
    Processing part.
    '''
    uid = bottle.request.get_header('X-Uid')
    return {'uid': uid}

# Generic part


@bottle.view('index.tmpl')
def index():
    '''
    Initial view.
    '''
    uid = bottle.request.get_header('X-Uid')
    return {'uid': uid}


def static(filepath):
    '''
    Serve static files.
    :param filepath:
    '''
    return bottle.static_file('web/static/' + filepath, root='..')


# Setup of the WSGI app.


def setup_routing(app):
    '''
    Setup the routing.
    :param app:
    '''
    app.route('/', ['GET'], index)
    app.route('/static/<filepath:path>', ['GET'], static)
    # data
    app.route('/data', ['GET'], list_data_sources)
    app.route('/data/<iden>', ['GET'], retrieve_data_source)
    app.route('/data/upload', ['POST'], create_data_source)
    app.route('/data/delete/<iden>', ['POST'], delete_data_source)
    # analysis
    app.route('/analysis', ['GET'], list_notebooks)
    app.route('/analysis/<iden>', ['GET'], retrieve_notebook)
    app.route('/analysis/<iden>/add/<old_id>', ['POST'], add_item_to_notebook)
    app.route('/analysis/<iden>/edit/<line_id>', ['GET'],
              edit_item_in_notebook)
    app.route('/analysis/<iden>/remove/<line_id>', ['POST'],
              remove_item_from_notebook)
    app.route('/analysis/upload', ['POST'], create_notebook)
    app.route('/analysis/download/<iden>', ['GET'], download_notebook)
    app.route('/analysis/delete/<iden>', ['POST'], delete_notebook)
    # processing
    app.route('/process', ['GET'], list_processings)


def get_app():
    '''
    Return ready to use WSGI app.
    '''
    app = bottle.app()
    setup_routing(app)
    return app

# Finally get the wsgi app together!
application = get_app()