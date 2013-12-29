# coding=utf-8

"""
Module representing an execution node.
"""

__author__ = 'tmetsch'

import json
import pika

from analytics import notebooks


class ExecNode(object):
    """
    Execution node - will be started per tenant.
    """

    def __init__(self, mongo_uri, amqp_uri, uid):
        # have the notebook stores in place
        self.a_ntb_str = notebooks.NotebookStore(mongo_uri, 'analytics')
        self.p_ntb_str = notebooks.NotebookStore(mongo_uri, 'processing')

        # connect to AMQP broker
        connection = pika.BlockingConnection(pika.URLParameters(amqp_uri))
        self.channel = connection.channel()
        self.channel.queue_declare(queue=uid)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callback, queue=uid)
        self.channel.start_consuming()

    def callback(self, channel, method, props, body):
        """
        Handle incoming request for this tenant.

        :param channel: The channel used.
        :param method: The message method.
        :param props: The message properties.
        :param body: The message body.
        """
        tmp = json.loads(body)
        response = self.handle(tmp)

        # set uuid so the right requester get the answer:-)
        prop = pika.BasicProperties(correlation_id=props.correlation_id)
        channel.basic_publish(exchange='',
                              routing_key=props.reply_to,
                              properties=prop,
                              body=json.dumps(response))
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def handle(self, body):
        """
        Handle the incoming requests.

        :param body: The message body.
        """
        call = body['call']
        uid = body['uid']
        token = body['token']
        store = self._get_store(body['ntb_type'])
        res = {}
        if call == 'list_notebooks':
            res = {'notebooks': store.list_notebooks(uid, token)}
        elif call == 'create_notebook':
            iden = body['iden']
            code = body['init_code']
            store.get_notebook(uid, token, iden, init_code=code)
            res = {}
        elif call == 'retrieve_notebook':
            iden = body['iden']
            ntb = store.get_notebook(uid, token, iden)
            res = {'indent': ntb.white_space, 'src': ntb.src}
        elif call == 'delete_notebook':
            iden = body['iden']
            store.delete_notebook(uid, token, iden)
            res = {}
        elif call == 'add_item_to_notebook':
            iden = body['iden']
            line = body['cmd']
            ntb = store.get_notebook(uid, token, iden)
            ntb.add_line(line)
            res = {}
        elif call == 'update_item_in_notebook':
            iden = body['iden']
            line = body['cmd']
            line_id = body['line_id']
            replace = body['replace']
            ntb = store.get_notebook(uid, token, iden)
            ntb.update_line(line_id, line, replace=replace)
            res = {}
        elif call == 'delete_item_of_notebook':
            iden = body['iden']
            line_id = body['line_id']
            ntb = store.get_notebook(uid, token, iden)
            ntb.remove_line(line_id)
            res = {}
        elif call == 'notebook_event':
            iden = body['iden']
            event = body['event']
            ntb = store.get_notebook(uid, token, iden)
            if event == 'rerun':
                ntb.rerun()
            res = {}
        return res

    def _get_store(self, ntb_type):
        """
        Retrieve type of store.

        :param ntb_type: string representation of str.
        """
        if ntb_type == 'analytics':
            return self.a_ntb_str
        elif ntb_type == 'processing':
            return self.p_ntb_str
