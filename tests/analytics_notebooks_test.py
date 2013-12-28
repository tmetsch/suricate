# coding=utf-8

"""
Unittest for the notebooks part.
"""

__author__ = 'tmetsch'

import collections
import unittest
import mox

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from analytics import notebooks


class ConsoleWrapperTest(unittest.TestCase):
    """
    Tests the Python console wrapper.
    """

    mocker = mox.Mox()

    def setUp(self):
        """
        Setup the tests.
        """
        super(ConsoleWrapperTest, self).setUp()
        coll = self.mocker.CreateMock(Collection)
        self.cut = notebooks.ConsoleWrapper('123', coll, {}, '123', 'abc',
                                            'localhost', '27017')

    # Sanity checks.

    def test_add_line_for_sanity(self):
        """
        Tests the addition of a single line.
        """
        self.cut.add_line('print "Hello"')
        tmp = self.cut.src.values()
        self.assertEquals(tmp[0][1].strip(), 'Hello')

    def test_remove_line_for_sanity(self):
        """
        Add some lines and remove it afterwards.
        """
        self.cut.add_line('i = 10')
        iden = self.cut.add_line('i = 5')
        self.cut.add_line('print i')
        self.cut.remove_line(iden)
        tmp = self.cut.src.values()
        self.assertEquals(tmp[1][1].strip(), '10')

    def test_update_line_for_sanity(self):
        """
        Add some lines and replace it afterwards.
        """
        iden = self.cut.add_line('i = 10')
        self.cut.add_line('print i')
        self.cut.update_line(iden, 'i = 5')
        tmp = self.cut.src.values()
        self.assertEquals(tmp[1][1].strip(), '5')

    def test_update_line_for_sanity2(self):
        """
        Add some lines and update it afterwards.
        """
        iden = self.cut.add_line('for i in range(0,1):\r\n\tprint i')
        self.cut.add_line('\n')
        self.cut.update_line(iden, '\r\n\tprint \"hello\"', replace=False)
        tmp = self.cut.src.values()
        self.assertEquals(tmp[1][1].strip(), '0\nhello')


class NotebookStoreTest(unittest.TestCase):
    """
    Test the notebook storage.
    """

    mocker = mox.Mox()

    def setUp(self):
        """
        Setup test case.
        """
        self.cut = Wrapper('haiku', 'notebooks')
        self.mongo_client = self.mocker.CreateMock(MongoClient)
        self.mongo_client._CreateMockMethod('host', None)
        self.mongo_db = self.mocker.CreateMock(Database)
        self.mongo_coll = self.mocker.CreateMock(Collection)
        self.cut.client = self.mongo_client

    def test_get_notebooks_for_success(self):
        """
        Test retrieval of notebooks.
        """
        self.mongo_client.__getitem__('nb1').AndReturn(self.mongo_db)
        # bit of a hack to get around property getter methods
        self.mongo_client._known_methods.add('host')
        self.mongo_client._known_methods.add('port')

        self.mongo_db.authenticate('nb1', 'abc')
        self.mongo_db.__getitem__('notebooks').AndReturn(self.mongo_coll)
        # is non existent so will call 'insert'!
        self.mongo_coll.find_one({'iden': '123'},
                                 as_class=collections.OrderedDict)\
            .AndReturn(None)
        self.mongo_coll.insert({'iden': '123', 'code': {}})
        self.mongo_coll.find_one({'iden': '123'},
                                 as_class=collections.OrderedDict)\
            .AndReturn({'_id': 'foobar', 'iden': 'nb1', 'code': {}})

        self.mocker.ReplayAll()
        self.cut.get_notebook('nb1', 'abc', '123')
        self.mocker.VerifyAll()

    def test_delete_notebook_for_success(self):
        """
        Test removal.
        """
        self.mongo_client.__getitem__('nb1').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('nb1', 'abc')
        self.mongo_db.__getitem__('notebooks').AndReturn(self.mongo_coll)
        self.mongo_coll.remove({'iden': '123'})

        self.mocker.ReplayAll()
        self.cut.delete_notebook('nb1', 'abc', '123')
        self.mocker.VerifyAll()

    def test_list_notebooks_for_sanity(self):
        """
        Test listing of names (!not _id from mongo!).
        """
        res = [
            {'iden': 'foo'},
            {'iden': 'bar'}
        ]
        self.mongo_client.__getitem__('nb1').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('nb1', 'abc')
        self.mongo_db.__getitem__('notebooks').AndReturn(self.mongo_coll)
        self.mongo_coll.find(fields={'iden': True, '_id': False}).AndReturn(
            res)

        self.mocker.ReplayAll()
        tmp = self.cut.list_notebooks('nb1', 'abc')
        self.mocker.VerifyAll()

        self.assertListEqual(tmp, ['foo', 'bar'])

    def test_get_notebooks_for_sanity(self):
        """
        Test retrieval of notebooks.
        """
        self.mongo_client._CreateMockMethod('host', None)
        # bit of a hack to get around property getter methods
        self.mongo_client._known_methods.add('host')
        self.mongo_client._known_methods.add('port')

        self.mongo_client.__getitem__('nb1').AndReturn(self.mongo_db)
        self.mongo_db.authenticate('nb1', 'abc')
        self.mongo_db.__getitem__('notebooks').AndReturn(self.mongo_coll)
        # is non existent so will call 'insert'!
        self.mongo_coll.find_one({'iden': '123'},
                                 as_class=collections.OrderedDict)\
            .AndReturn(None)
        self.mongo_coll.insert({'iden': '123', 'code': {}})
        self.mongo_coll.find_one({'iden': '123'},
                                 as_class=collections.OrderedDict)\
            .AndReturn({'_id': 'foobar', 'iden': 'nb1', 'code': {}})
        # two lines --> two calls.
        self.mongo_coll.update(mox.IsA(dict), mox.IsA(dict), upsert=False)
        self.mongo_coll.update(mox.IsA(dict), mox.IsA(dict), upsert=False)

        self.mocker.ReplayAll()
        self.cut.get_notebook('nb1', 'abc', '123', ['for i in range(0,10):',
                                                    'print i', '\n'])
        self.mocker.VerifyAll()


class Wrapper(notebooks.NotebookStore):
    """
    Simple Wrapper.
    """

    def __init__(self, uri, coll_name):
        self.cache = {}
        self.coll_name = coll_name