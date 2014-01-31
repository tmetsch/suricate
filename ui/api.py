# coding=utf-8

"""
An API used by the UI and RESTful API.
"""

__author__ = 'tmetsch'

import collections
import json
import pika
import pika.exceptions as pikaex
import uuid


class API(object):
    """
    Little helper class to abstract the REST and UI from.
    """

    def __init__(self, amqp_uri):
        self.clients = {}
        self.amqp_uri = amqp_uri

    # Data sources...
    # TODO: deal with the data part here too!

    ## Objects

    ## Streams

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

    def create_project(self, proj_name, uid, token):
        """
        RPC call to list projects.

        :param proj_name: Name of the project.
        :param uid: Identifier for the user.
        :param token: The token of the user.
        """
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': 'analytics.py',
                   'notebook': {'meta': {}, 'src': '\n'},
                   'call': 'update_notebook'}
        self._call_rpc(uid, payload)

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

    def retrieve_notebook(self, proj_name, ntb_id, uid, token):
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'call': 'retrieve_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp['notebook']

    def update_notebook(self, proj_name, ntb_id, ntb, uid, token):
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'notebook': ntb,
                   'call': 'update_notebook'}
        self._call_rpc(uid, payload)

    def delete_notebook(self, proj_name, ntb_id, uid, token):
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'call': 'delete_notebook'}
        self._call_rpc(uid, payload)

    def run_notebook(self, proj_name, ntb_id, src, uid, token):
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'src': src,
                   'call': 'run_notebook'}
        self._call_rpc(uid, payload)

    def interact(self, proj_name, ntb_id, loc, uid, token):
        payload = {'uid': uid,
                   'token': token,
                   'project_id': proj_name,
                   'notebook_id': ntb_id,
                   'loc': loc,
                   'call': 'interact'}
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
