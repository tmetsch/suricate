# coding=utf-8

"""
An API used by the UI and RESTful API.
"""

__author__ = 'tmetsch'

import collections
import json
import pika
import uuid


class API(object):
    """
    Little helper class to abstract the REST and UI from.
    """

    def __init__(self):
        # TODO: configure properly!
        para = pika.URLParameters('amqp://guest:os4all@localhost:5672/%2f')
        self.connection = pika.BlockingConnection(para)
        self.clients = {}

    # Data sources...

    ## Objects

    ## Streams

    ####
    # Everything below this is RPC!
    ####

    # Notebooks - can have two types: processing or analytics!


    def list_notebooks(self, uid, token, ntb_type):
        """
        RPC call to list notebooks.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'call': 'list_notebooks'}
        tmp = self._call_rpc(uid, payload)
        return tmp['notebooks']


    def create_notebook(self, uid, token, ntb_type, iden, init_code):
        """
        RPC call to create a new notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        :param init_code: Initial code if present.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'init_code': init_code,
                   'call': 'create_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp


    def retrieve_notebook(self, uid, token, ntb_type, iden):
        """
        RPC call to retrieve a notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'call': 'retrieve_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp['src'], tmp['indent']


    def delete_notebook(self, uid, token, ntb_type, iden):
        """
        RPC call to delete a notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'call': 'delete_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp


    def add_item_to_notebook(self, uid, token, ntb_type, iden, cmd):
        """
        RPC call to add an item to an notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        :param cmd: A python command as string.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'cmd': cmd,
                   'call': 'add_item_to_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp


    def update_item_in_notebook(self, uid, token, ntb_type, iden, line_id, cmd,
                                replace=True):
        """
        RPC call to update an item in a notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        :param line_id: Identifier of the line in the notebook.
        :param cmd: A python command as string.
        :param replace: Whether to replace existing code or not (def: True)
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'line_id': line_id,
                   'cmd': cmd,
                   'replace': replace,
                   'call': 'update_item_in_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp


    def delete_item_of_notebook(self, uid, token, ntb_type, iden, line_id):
        """
        RPC call to delete a item from a notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        :param line_id: Identifier of the line in the notebook.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'line_id': line_id,
                   'call': 'delete_item_of_notebook'}
        tmp = self._call_rpc(uid, payload)
        return tmp


    def notebook_event(self, uid, token, ntb_type, iden, event):
        """
        RPC call to trigger an evebt on a notebook.

        :param uid: Identifier for the user.
        :param token: The token of the user.
        :param ntb_type: Type of the notebook.
        :param iden: Identifier of the notebook.
        :param event: Which event to trigger.
        """
        payload = {'uid': uid,
                   'token': token,
                   'ntb_type': ntb_type,
                   'iden': iden,
                   'event': event,
                   'call': 'notebook_event'}
        tmp = self._call_rpc(uid, payload)
        return tmp

    def _call_rpc(self, uid, payload):
        if uid not in self.clients:
            self.clients[uid] = RPCClient(self.connection)
        return self.clients[uid].call(uid, payload)


class RPCClient(object):
    """
    An RPC client using AMQP.
    """

    json_dec = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)


    def __init__(self, connection):
        self.connection = connection
        self.channel = connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.response, no_ack=True,
                                   queue=self.callback_queue)
        self.corr_id = None
        self.response = None

    def response(self, ch, method, props, body):
        """
        Handle a response call.

        :param ch: The channel.
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
        prop = pika.BasicProperties(reply_to=self.callback_queue,
                                    correlation_id=self.corr_id)
        self.channel.basic_publish(exchange='',
                                   routing_key=uid,
                                   properties=prop,
                                   body=json.dumps(payload))
        while self.response is None:
            self.connection.process_data_events()

        # making usre order is in place!
        res = self.json_dec.decode(self.response)
        self.response = None

        return res