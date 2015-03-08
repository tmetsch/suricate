# coding=utf-8

"""
An API used by the UI and RESTful API.
"""
from bson import ObjectId

__author__ = 'tmetsch'

import collections
import json
import pika
import pika.exceptions as pikaex
import uuid

from suricate.data import object_store
from suricate.data import streaming


template = '''
% if len(error.strip()) > 0:
    <div class="error">{{!error}}</div>
% end
% for item in output:
    % if item[:6] == 'image:':
    <div><img src="data:{{item[6:]}}"/></div>
    % elif item[:6] == 'embed:':
    <div>{{!item[6:]}}</div>
    % elif item[:1] == '#':
    <div>{{item.rstrip()}}</div>
    % elif item.strip() != '':
    <div class="code">{{item.rstrip()}}</div>
    % end
% end
'''


class API(object):
    """
    Little helper class to abstract the REST and UI from.
    """

    def __init__(self, amqp_uri, mongo_uri):
        self.clients = {}
        self.amqp_uri = amqp_uri

        # get obj/streaming client up!
        self.obj_str = object_store.MongoStore(mongo_uri)
        self.stream = streaming.AMQPClient(mongo_uri)

    # Data sources...

    def info_data(self, uid, token):
        """
        Return dictionary with key/values about data objects and streams.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        data_info = self.obj_str.info(uid, token)
        data_info.update(self.stream.info(uid, token))
        return data_info

    def list_data_sources(self, uid, token):
        """
        List available data sources. Return list of ids for objects & streams.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        tmp = self.obj_str.list_objects(uid, token)
        tmp2 = self.stream.list_streams(uid, token)
        return tmp, tmp2

    # Objects

    def create_object(self, content, uid, token, meta_dat):
        """
        Create a data object.

        :param content: Object content.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        self.obj_str.create_object(uid, token, content, meta=meta_dat)

    def retrieve_object(self, iden, uid, token):
        """
        Retrieve a data object.

        :param iden: Id of the object.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        tmp = self.obj_str.retrieve_object(uid, token, iden)
        return tmp

    def delete_object(self, iden, uid, token):
        """
        Delete a data object.

        :param iden: Id of the object.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        self.obj_str.delete_object(uid, token, iden)

    # Streams

    def create_stream(self, uri, queue, uid, token):
        """
        Create a data stream.

        :param uri: RabbitMQ Broker URI.
        :param queue: Queue.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        self.stream.create(uid, token, uri, queue)

    def retrieve_stream(self, iden, uid, token):
        """
        Retrieve a data stream.

        :param iden: Id of the stream.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        uri, queue, msgs = self.stream.retrieve(uid, token, iden)
        return uri, queue, msgs

    def delete_stream(self, iden, uid, token):
        """
        Delete a data stream.

        :param iden: Id of the stream.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        self.stream.delete(uid, token, iden)

    def set_meta(self, data_src, iden, tags, uid, token):
        """
        Set meta information.

        :param data_src: Reflects to db name.
        :param iden: Id of the object/stream.
        :param tags: Metadata dict.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        database = self.obj_str.client[uid]
        database.authenticate(uid, token)
        collection = database[data_src]
        collection.update({'_id': ObjectId(iden)},
                          {"$set": {'meta.tags': tags}})

    ####
    # Everything below this is RPC!
    ####

    # TODO: check if can work with function name and kwargs to construct
    # payload.

    # Projects

    def list_projects(self, uid, token):
        """
        RPC call to list notebooks.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'call': 'list_projects'}
        tmp = self._call_rpc(uid, payload)
        return tmp['projects']

    def retrieve_project(self, proj_name, uid, token):
        """
        RPC call to retrieve projects.

        :param proj_name: Name of the project.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'call': 'retrieve_project'}
        tmp = self._call_rpc(uid, payload)
        return tmp['project']

    def delete_project(self, proj_name, uid, token):
        """
        RPC call to delete a project.

        :param proj_name: Name of the project.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'call': 'delete_project'}
        self._call_rpc(uid, payload)

    # Notebooks

    def create_notebook(self, proj_name, uid, token, ntb_name='start.py',
                        src='\n'):
        """
        RPC call to create a notebook (or creating an empty project).

        :param proj_name: Name of the project.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': None,
                   'notebook': {'meta': {'tags': [],
                                         'name': ntb_name,
                                         'mime-type': 'text/x-script.phyton'},
                                'src': src,
                                'dashboard_template': template,
                                'out': [],
                                'err': ''},
                   'call': 'update_notebook'}
        self._call_rpc(uid, payload)

    def retrieve_notebook(self, proj_name, ntb_id, uid, token):
        """
        RPC call to retrieve a notebook.

        :param proj_name: Name of the project.
        :param ntb_id: Id of the notebook.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'call': 'retrieve_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp['notebook']

    def update_notebook(self, proj_name, ntb_id, ntb, uid, token):
        """
        RPC call to update a notebook.

        :param proj_name: Name of the project.
        :param ntb_id: Id of the notebook.
        :param ntb: New notebook structure.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'src': ntb,
                   'call': 'update_notebook'}
        self._call_rpc(uid, payload)

    def delete_notebook(self, proj_name, ntb_id, uid, token):
        """
        RPC call to delete a notebook.

        :param proj_name: Name of the project.
        :param ntb_id: Id of the notebook.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'call': 'delete_notebook'}
        self._call_rpc(uid, payload)

    def run_notebook(self, proj_name, ntb_id, src, uid, token):
        """
        RPC call to run a notebook.

        :param proj_name: Name of the project.
        :param ntb_id: Id of the notebook.
        :param src: source code to run.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'src': src,
                   'call': 'run_notebook'}
        self._call_rpc(uid, payload)

    def interact(self, proj_name, ntb_id, loc, uid, token):
        """
        RPC call to interact with an notebook's intepreter.

        :param proj_name: Name of the project.
        :param ntb_id: Id of the notebook.
        :param loc: Line of code.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'loc': loc,
                   'call': 'interact'}
        self._call_rpc(uid, payload)

    # Jobs.

    def list_jobs(self, uid, token):
        """
        RPC call to run a notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'call': 'list_jobs'}
        tmp = self._call_rpc(uid, payload)
        return tmp['jobs']

    def run_job(self, proj_name, ntb_id, src, uid, token):
        """
        RPC call to run a notebook.

        :param proj_name: Name of the project.
        :param ntb_id: Id of the notebook.
        :param src: source code to run.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'src': src,
                   'call': 'run_job'}
        self._call_rpc(uid, payload)

    def clear_job_list(self, uid, token):
        """
        Clear job list.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'call': 'clear_job_list'}
        self._call_rpc(uid, payload)

    def _call_rpc(self, uid, payload):
        """
        Make a lovely RPC (blocking) call.

        :param uid: user's id.
        :param payload: JSON payload for the message.
        """
        if uid not in self.clients:
            self.clients[uid] = RPCClient(self.amqp_uri)
        return self.clients[uid].call(uid, payload)


class RPCClient(object):
    """
    An RPC client using AMQP.
    """

    json_dec = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)

    def __init__(self, uri):
        self.para = pika.URLParameters(uri)
        self.connection = pika.BlockingConnection(self.para)

        self.corr_id = None
        self.response = None

    def callback(self, channel, method, props, body):
        """
        Handle a response call.

        :param channel: The channel.
        :param method: The method.
        :param props: The properties.
        :param body: The body.
        """
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, uid, payload):
        """
        Perform an RPC call.

        :param uid: Identifier of the user.
        :param payload: The payload.
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())

        try:
            channel = self.connection.channel()
        except pikaex.ChannelClosed:
            # idle connections are closed...
            self.connection = pika.BlockingConnection(self.para)
            channel = self.connection.channel()

        result = channel.queue_declare(exclusive=True)
        callback_queue = result.method.queue
        channel.basic_consume(self.callback, no_ack=True,
                              queue=callback_queue)
        prop = pika.BasicProperties(reply_to=callback_queue,
                                    correlation_id=self.corr_id)
        channel.basic_publish(exchange='',
                              routing_key=uid,
                              properties=prop,
                              body=json.dumps(payload))
        while self.response is None:
            self.connection.process_data_events()

        # making sure order is in place!
        res = self.json_dec.decode(self.response)
        self.response = None

        return res
