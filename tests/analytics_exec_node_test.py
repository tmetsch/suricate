# coding=utf-8

"""
Tests for the execution node.
"""

__author__ = 'tmetsch'

import mox
import unittest

from analytics import exec_node
from analytics import notebooks


class ExecNodeTest(unittest.TestCase):
    """
    Test the exec node for processes.
    """

    mocker = mox.Mox()

    def setUp(self):
        self.cut = Wrapper('', '', 'foo')
        self.cut.a_ntb_str = self.mocker.CreateMock(notebooks.NotebookStore)
        self.wrp = self.mocker.CreateMock(notebooks.ConsoleWrapper)
        self.wrp.__setattr__('white_space', '')
        self.wrp.__setattr__('src', {})

    def test_handle_for_sanity(self):
        body = {'uid': 'foo',
                'token': 'bar',
                'ntb_type': 'analytics'}
        # list
        body['call'] = 'list_notebooks'
        self.cut.a_ntb_str.list_notebooks('foo', 'bar').AndReturn(None)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # create
        self.mocker.ResetAll()
        body['call'] = 'create_notebook'
        body['iden'] = 'abc'
        body['init_code'] = []
        self.cut.a_ntb_str.get_notebook('foo', 'bar', 'abc', init_code=[]).AndReturn(None)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # retrieve
        self.mocker.ResetAll()
        body['call'] = 'retrieve_notebook'
        body['iden'] = 'abc'
        self.cut.a_ntb_str.get_notebook('foo', 'bar', 'abc').AndReturn(self.wrp)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # delete
        self.mocker.ResetAll()
        body['call'] = 'delete_notebook'
        body['iden'] = 'abc'
        self.cut.a_ntb_str.delete_notebook('foo', 'bar', 'abc').AndReturn(None)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # add item
        self.mocker.ResetAll()
        body['call'] = 'add_item_to_notebook'
        body['iden'] = 'abc'
        body['line_id'] = '1'
        body['cmd'] = 'a = 10'
        self.wrp.add_line('a = 10')
        self.cut.a_ntb_str.get_notebook('foo', 'bar', 'abc').AndReturn(self.wrp)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # update item
        self.mocker.ResetAll()
        body['call'] = 'update_item_in_notebook'
        body['iden'] = 'abc'
        body['line_id'] = '1'
        body['replace'] = False
        self.wrp.update_line('1', 'a = 10', replace=False)
        self.cut.a_ntb_str.get_notebook('foo', 'bar', 'abc').AndReturn(self.wrp)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # delete item
        self.mocker.ResetAll()
        body['call'] = 'delete_item_of_notebook'
        body['iden'] = 'abc'
        body['line_id'] = '1'
        self.wrp.remove_line('1')
        self.cut.a_ntb_str.get_notebook('foo', 'bar', 'abc').AndReturn(self.wrp)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()
        # rerun!
        self.mocker.ResetAll()
        body['call'] = 'notebook_event'
        body['iden'] = 'abc'
        body['event'] = 'rerun'
        self.wrp.rerun()
        self.cut.a_ntb_str.get_notebook('foo', 'bar', 'abc').AndReturn(self.wrp)
        self.mocker.ReplayAll()
        self.cut.handle(body)
        self.mocker.VerifyAll()


class Wrapper(exec_node.ExecNode):

    def __init__(self, m_uri, a_uri, uid):
        pass
