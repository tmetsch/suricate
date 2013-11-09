# coding=utf-8

'''
Supports Data streams through services like AMQP.
'''

__author__ = 'tmetsch'

import pika
import pymongo
import threading
import time

from bson import ObjectId


class StreamClient(object):
    '''
    Simple streaming client.
    '''

    def __init__(self, uri):
        '''
        Initialize StreamingClient.
        '''
        self.client = pymongo.MongoClient(uri)

    def list_streams(self, uid, token):
        '''
        Retrieve list of available streams.

        :param uid: User's uid.
        :param token: Token of the user.
        :return: List of identifiers.
        '''
        db = self.client[uid]
        db.authenticate(uid, token)
        collection = db['data_streams']
        res = []
        for obj in collection.find():
            res.append(obj['_id'])
        return res

    def get_messages(self, uid, token, interval, iden):
        '''
        Retrieve list of messages.

        :param uid: User's uid.
        :param token: Token of the user.
        :param interval: Intervall to get messages from.
        :param iden: Identifier for the stream
        :return: List of messages.
        '''
        db = self.client[uid]
        db.authenticate(uid, token)
        begin = time.time() - interval
        end = time.time()

        collection = db['data_streams.' + str(iden)]
        items = collection.aggregate([
            {"$match": {"resv": {"$gt": begin, "$lte": end}}},
            {"$project": {"_id": 0, "body": 1}},
            {"$sort": {"resv": 1}}
        ])['result']

        return list(items)


class AMQPClient(object):
    '''
    Stream client for Suricate.
    '''

    def __init__(self, uri):
        self.client = pymongo.MongoClient(uri)
        self.cache = {}
        self.uri = uri

    def list_streams(self, uid, token):
        '''
        List available streams. Make sure AMQP clients are up & running.

        :param uid: User's uid.
        :param token: Token of the user.
        :return: List of ids.
        '''
        db = self.client[uid]
        db.authenticate(uid, token)
        collection = db['data_streams']
        res = []
        for obj in collection.find():
            if str(obj['_id']) not in self.cache:
                iden = str(obj['_id'])
                content = collection.find_one({'_id': ObjectId(iden)})
                uri = content['uri']
                queue = content['queue']
                self.cache[iden] = StreamConsumer(uid, token, iden,
                                                  self.uri, str(uri),
                                                  str(queue))
                self.cache[iden].start()
            res.append(obj['_id'])
        return res

    def create(self, uid, token, uri, queue):
        '''
        Create a new stream.

        :param uid: User's uid.
        :param token: Token of the user.
        :param uri: URI of the RabbitMQ server.
        :param queue: Queue name
        :return: Identifier.
        '''
        db = self.client[uid]
        db.authenticate(uid, token)
        collection = db['data_streams']
        tmp = {'uri': uri, 'queue': queue}
        obj_id = collection.insert(tmp)
        return obj_id

    def retrieve(self, uid, token, iden):
        '''
        Retrieve a stream.

        :param uid: User's uid.
        :param token: Token of the user.
        :param iden: Identifier of the stream
        :return: URI, Queue name and msgs from last minute.
        '''
        db = self.client[uid]
        db.authenticate(uid, token)
        collection = db['data_streams']
        # get URI
        content = collection.find_one({'_id': ObjectId(iden)})
        uri = content['uri']
        queue = content['queue']

        # Get messages
        begin = time.time() - 60
        end = time.time()

        collection = db['data_streams.' + str(iden)]
        items = collection.aggregate([
            {"$match": {"resv": {"$gt": begin, "$lte": end}}},
            {"$project": {"_id": 0, "body": 1}},
            {"$sort": {"resv": 1}}
        ])['result']

        return uri, queue, list(items)

    def delete(self, uid, token, iden):
        '''
        Delete a stream.

        :param uid: User's uid.
        :param token: Token of the user.
        :param iden: Identifier of the stream.
        '''
        db = self.client[uid]
        db.authenticate(uid, token)
        collection = db['data_streams']
        collection.remove({'_id': ObjectId(iden)})
        collection = db['data_streams.' + str(iden)]
        collection.drop()

        self.cache[iden].stop()
        self.cache.pop(iden)


class StreamConsumer(threading.Thread):
    '''
    Consumer which extracts messages from a Queue and stores them.
    '''

    def __init__(self, uid, token, iden, str_uri, amqp_uri, queue):
        super(StreamConsumer, self).__init__()
        # for storing msgs.
        client = pymongo.MongoClient(str_uri)
        db = client[uid]
        db.authenticate(uid, token)
        self.collection = db['data_streams.' + str(iden)]

        # amqp conn.
        self.queue = queue
        connection = pika.BlockingConnection(pika.URLParameters(amqp_uri))
        self.channel = connection.channel()
        self.channel.queue_declare(queue=queue)

    def run(self):
        '''
        Strat consuming.
        '''
        self.channel.basic_consume(self.callback, queue=self.queue,
                                   no_ack=True)
        self.channel.start_consuming()

    def stop(self):
        '''
        Stop consuming.
        '''
        self.channel.stop_consuming()

    def callback(self, ch, method, properties, body):
        '''
        Callback which stores the messages.

        :param body: msg body.
        :param properties: msg props.
        :param method: msg method.
        :param ch: channel.
        '''
        tmp = time.time()
        tmp = {'resv': tmp, 'body': body}
        self.collection.insert(tmp)
