# coding=utf-8

"""
Wraps around object storage.
"""

__author__ = 'tmetsch'

import bson
import pymongo
import uuid


def get_object_stor():
    """
    Returns the right instance of a object storage interface object for an
    given URI.

    :return: Instance of ObjectStore.
    """
    # TODO: implement
    pass


class ObjectStore(object):
    """
    Stores need to derive from this one.
    """

    def list_objects(self, uid, token, query={}):
        """
        List the objects of a user.

        :param uid: User id.
        :param token: Access token.
        :param query: Optional query.
        """
        raise NotImplementedError('Needs to be implemented by subclass.')

    def create_object(self, uid, token, content):
        """
        Create an object for a user. Returns and id

        :param content: Some content.
        :param uid: User id.
        :param token: Access token.
        """
        raise NotImplementedError('Needs to be implemented by subclass.')

    def retrieve_object(self, uid, token, obj_id):
        """
        Add a object for a user.

        :param obj_id: Identifier of the object.
        :param uid: User id.
        :param token: Access token.
        """
        raise NotImplementedError('Needs to be implemented by subclass.')

    def update_object(self, uid, token, obj_id, content):
        """
        Add a object for a user.

        :param content: Some content.
        :param obj_id: Identifier of the object.
        :param uid: User id.
        :param token: Access token.
        """
        raise NotImplementedError('Needs to be implemented by subclass.')

    def delete_object(self, uid, token, obj_id):
        """
        Add a object for a user.

        :param obj_id: Identifier of the object.
        :param uid: User id.
        :param token: Access token.
        """
        raise NotImplementedError('Needs to be implemented by subclass.')


class MongoStore(ObjectStore):
    """
    Object Storage based on Mongo.
    """

    auth = False

    def __init__(self, uri):
        """
        Setup a connection to the Mongo server.
        """
        self.client = pymongo.MongoClient(uri)

    def info(self, uid, token):
        """
        Return basic infos about the objects.

        :param uid: User's uid.
        :param token: Token of the user.
        :return: Dict with key/values.
        """
        res = {}
        database = self.client[uid]
        database.authenticate(uid, token)
        collection = database['data_objects']
        res['number_of_objects'] = collection.count()
        return res

    def list_objects(self, uid, token, query={}):
        """
        List the objects of a user.

        :param uid: User id.
        :param token: Access token.
        :param query: Optional query.
        """
        database = self.client[uid]
        database.authenticate(uid, token)
        collection = database['data_objects']
        res = []
        for item in collection.find(query):
            res.append((str(item['_id']), item['meta']))
        return res

    def create_object(self, uid, token, content, meta=None):
        """
        Create an object for a user. Returns and id

        :param content: Some content.
        :param uid: User id.
        :param token: Access token.
        :param meta: Some meta data.
        """
        database = self.client[uid]
        database.authenticate(uid, token)
        collection = database['data_objects']
        if meta is None:
            meta = {'name': str(uuid.uuid4()),
                    'mime-type': 'N/A',
                    'tags': []}
        tmp = {'value': content, 'meta': meta}
        obj_id = collection.insert(tmp)
        return obj_id

    def retrieve_object(self, uid, token, obj_id):
        """
        Add a object for a user.

        :param obj_id: Identifier of the object.
        :param uid: User id.
        :param token: Access token.
        """
        database = self.client[uid]
        database.authenticate(uid, token)
        collection = database['data_objects']
        tmp = collection.find_one({'_id': bson.ObjectId(obj_id)})
        tmp.pop('_id')
        return tmp

    def update_object(self, uid, token, obj_id, content):
        """
        Add a object for a user.

        :param content: Some content.
        :param obj_id: Identifier of the object.
        :param uid: User id.
        :param token: Access token.
        """
        database = self.client[uid]
        database.authenticate(uid, token)
        collection = database['data_objects']
        collection.update({'_id': bson.ObjectId(obj_id)},
                          {"$set": {'value': content}}, upsert=False)

    def delete_object(self, uid, token, obj_id):
        """
        Add a object for a user.

        :param obj_id: Identifier of the object.
        :param uid: User id.
        :param token: Access token.
        """
        database = self.client[uid]
        database.authenticate(uid, token)
        collection = database['data_objects']
        collection.remove({'_id': bson.ObjectId(obj_id)})


class CDMIStore(ObjectStore):
    """
    TODO: will retrieve objects from a (remote) CDMI enabled Object Storage
    Service.
    """

    pass
