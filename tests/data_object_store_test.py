# coding=utf-8

"""
Unit test for the object store part.
"""

__author__ = 'tmetsch'

import mox
import unittest

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from suricate.data import object_store


class ObjectStoreTest(unittest.TestCase):
    """
    Test for the uber class :-)
    """

    def test_for_failure(self):
        """
        Test if all throw no impl errors.
        """
        self.assertRaises(NotImplementedError,
                          object_store.ObjectStore().list_objects,
                          '123', 'abc')
        self.assertRaises(NotImplementedError,
                          object_store.ObjectStore().create_object,
                          '123', 'abc', 'foo')
        self.assertRaises(NotImplementedError,
                          object_store.ObjectStore().retrieve_object,
                          '123', 'abc', 'abc')
        self.assertRaises(NotImplementedError,
                          object_store.ObjectStore().update_object,
                          '123', 'abc', 'abc', 'bar')
        self.assertRaises(NotImplementedError,
                          object_store.ObjectStore().delete_object,
                          '123', 'abc', 'abc')


class MongoStoreTest(unittest.TestCase):
    """
    Test MongoDB Object storage.
    """

    mocker = mox.Mox()

    def setUp(self):
        """
        Setup test.
        """
        self.cut = Wrapper('haiku', 123, 'foo')
        self.mongo_client = self.mocker.CreateMock(MongoClient)
        self.mongo_db = self.mocker.CreateMock(Database)
        self.mongo_coll = self.mocker.CreateMock(Collection)
        self.cut.client = self.mongo_client

    def test_list_objects_for_sanity(self):
        """
        Test listing.
        """
        self.mongo_client.__getitem__('123').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('123', 'abc')
        self.mongo_db.__getitem__('data_objects').AndReturn(self.mongo_coll)
        self.mongo_coll.find({}).AndReturn([{'_id': 'foo',
                                             'meta': {'tags': []},
                                             'content': 'bar'}])

        self.mocker.ReplayAll()
        tmp = self.cut.list_objects('123', 'abc')
        self.mocker.VerifyAll()

        self.assertListEqual(tmp, [('foo', {'tags': []})])

    def test_create_object_for_sanity(self):
        """
        Test creation.
        """
        self.mongo_client.__getitem__('123').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('123', 'abc')
        self.mongo_db.__getitem__('data_objects').AndReturn(self.mongo_coll)
        self.mongo_coll.insert({'value': {'foo': 'bar'},
                                'meta': {'tags': [],
                                         'name': 'foo'}}).AndReturn('foo123')

        self.mocker.ReplayAll()
        tmp = self.cut.create_object('123', 'abc', {'foo': 'bar'},
                                     meta={'tags': [], 'name': 'foo'})
        self.mocker.VerifyAll()

        self.assertEquals(tmp, 'foo123')

    def test_retrieve_object_for_sanity(self):
        """
        Test retrieval.
        """
        self.mongo_client.__getitem__('123').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('123', 'abc')
        self.mongo_db.__getitem__('data_objects').AndReturn(self.mongo_coll)
        self.mongo_coll.find_one(mox.IsA(dict)).AndReturn({'_id': None,
                                                           'value':
                                                           {'foo': 'bar'}})

        self.mocker.ReplayAll()
        tmp = self.cut.retrieve_object('123', 'abc',
                                       '520f896217b168455c7d5fb9')
        self.mocker.VerifyAll()

        self.assertEquals(tmp, {'value': {'foo': 'bar'}})

    def test_update_object_for_sanity(self):
        """
        Test retrieval.
        """
        self.mongo_client.__getitem__('123').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('123', 'abc')
        self.mongo_db.__getitem__('data_objects').AndReturn(self.mongo_coll)
        self.mongo_coll.update(mox.IsA(dict), mox.IsA(dict), upsert=False)

        self.mocker.ReplayAll()
        self.cut.update_object('123', 'abc', '520f896217b168455c7d5fb9',
                               {'a': 123})
        self.mocker.VerifyAll()

    def test_delete_object_for_sanity(self):
        """
        Test removeal.
        """
        self.mongo_client.__getitem__('123').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('123', 'abc')
        self.mongo_db.__getitem__('data_objects').AndReturn(self.mongo_coll)
        self.mongo_coll.remove(mox.IsA(dict))

        self.mocker.ReplayAll()
        self.cut.delete_object('123', 'abc', '520f896217b168455c7d5fb9')
        self.mocker.VerifyAll()


class CDMIStoreTest(unittest.TestCase):
    """
    Test the CDMI storage.
    """

    def test_sth_for_success(self):
        pass


class Wrapper(object_store.MongoStore):
    """
    Simple Wrapper.
    """

    def __init__(self, host, port, uri):
        pass