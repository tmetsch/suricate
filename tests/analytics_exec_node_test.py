import unittest

from analytics import exec_node, proj_ntb_store


class ExecNodeTest(unittest.TestCase):

    payload = {'uid': 'foo',
               'token': 'bar',
               'project_id': 'qwe'}
    mongo_uri = 'mongodb://foo:bar@localhost:27017/foo'
    amqp_uri = 'amqp://guest:guest@localhost:5672/%2f'

    def setUp(self):
        self.store = proj_ntb_store.NotebookStore(self.mongo_uri, 'foo')
        self.cut = ClassUnderTestWrapper(self.mongo_uri, self.amqp_uri,
                                         'foo', 'bar')
        self.store.update_notebook('qwe', 'abc.py', {'src': 'print "hello"'},
                                   'foo', 'bar')

    def tearDown(self):
        self.store.delete_project('qwe', 'foo', 'bar')

    def test_handle_for_sanity(self):
        # test listing
        self.payload['call'] = 'list_projects'
        self.assertTrue('qwe' in self.cut._handle(self.payload)['projects'])

        # retrieve project
        self.payload['call'] = 'retrieve_project'
        self.assertEquals(self.cut._handle(self.payload)['project'],
                          ['abc.py'])

        # test retrieving
        self.payload['call'] = 'retrieve_notebook'
        self.payload['notebook_id'] = 'abc.py'
        self.assertEqual(self.cut._handle(self.payload)['notebook']['src'],
                         'print "hello"')

        # test running code
        self.payload['call'] = 'run_notebook'
        self.payload['notebook_id'] = 'abc.py'
        self.payload['src'] = 'print("hello")'
        self.assertEqual(self.cut._handle(self.payload), {})
        self.payload['call'] = 'retrieve_notebook'
        self.assertEquals(self.cut._handle(self.payload)['notebook']['out'],
                          ['hello'])

        # test interacting
        self.payload['call'] = 'interact'
        self.payload['loc'] = 'print("foobar")'
        self.assertEqual(self.cut._handle(self.payload), {})

        # test update
        self.payload['call'] = 'update_notebook'
        self.payload['notebook_id'] = 'abc.py'
        self.payload['notebook'] = {'src': 'for i in range(0,5):\n\tprint i'}
        self.cut._handle(self.payload)

        # retrieve it
        self.payload['call'] = 'retrieve_notebook'
        self.assertEquals(self.cut._handle(self.payload)['notebook']['src'],
                          'for i in range(0,5):\n\tprint i')

        # delete it
        self.payload['call'] = 'delete_notebook'
        self.payload['notebook_id'] = 'abc.py'
        self.cut._handle(self.payload)


class ClassUnderTestWrapper(exec_node.ExecNode):
    """
    Wraps around the ExecNode and disables the listening.
    """

    def __init__(self, mongo_uri, amqp_uri, uid, token):
        self.uid = uid
        self.token = token
        self.uri = mongo_uri
        # store
        self.stor = proj_ntb_store.NotebookStore(mongo_uri, 'foo')