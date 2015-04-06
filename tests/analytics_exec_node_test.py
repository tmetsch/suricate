import time
import unittest

from suricate.analytics import exec_node, proj_ntb_store


class ExecNodeTest(unittest.TestCase):

    payload = {'uid': 'foo',
               'token': 'bar',
               'project_id': 'qwe'}
    mongo_uri = 'mongodb://foo:bar@localhost:27017/foo'
    amqp_uri = 'amqp://guest:guest@localhost:5672/%2f'

    def setUp(self):
        self.store = proj_ntb_store.NotebookStore(self.mongo_uri, 'foo')
        self.cut = ClassUnderTestWrapper(self.mongo_uri, self.amqp_uri,
                                         'sdk.py', 'foo')
        self.ntb_id = self.store.update_notebook('qwe',
                                                 None,
                                                 {'src': 'print "hello"',
                                                  'meta': {'name': 'abc.py',
                                                           'tags': []}},
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
                          [(self.ntb_id, {'name': 'abc.py', 'tags': []})])

        # test retrieving
        self.payload['call'] = 'retrieve_notebook'
        self.payload['notebook_id'] = self.ntb_id
        self.assertEqual(self.cut._handle(self.payload)['notebook']['src'],
                         'print "hello"')

        # test running code
        self.payload['call'] = 'run_notebook'
        self.payload['notebook_id'] = self.ntb_id
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
        self.payload['notebook_id'] = self.ntb_id
        self.payload['src'] = 'for i in range(0,5):\n\tprint i'
        self.cut._handle(self.payload)

        # retrieve it
        self.payload['call'] = 'retrieve_notebook'
        self.assertEquals(self.cut._handle(self.payload)['notebook']['src'],
                          'for i in range(0,5):\n\tprint i')

        # test run an job.
        self.payload['call'] = 'run_job'
        self.payload['notebook_id'] = self.ntb_id
        self.payload['src'] = 'import time\nfor i in range(0,10):' \
                              '\n\ttime.sleep(1)'
        self.cut._handle(self.payload)
        # list jobs
        self.payload['call'] = 'list_jobs'
        time.sleep(2)
        self.assertEquals(self.cut._handle(self.payload)['jobs'].values()[0],
                          {'project': 'qwe', 'ntb_name': 'abc.py',
                           'state': 'running', 'ntb_id': self.ntb_id})
        time.sleep(10)
        tmp = self.cut._handle(self.payload)['jobs'].values()[0]
        self.assertEquals(tmp['project'], 'qwe')
        self.assertEquals(tmp['ntb_name'], 'abc.py')
        self.assertEquals(tmp['ntb_id'], self.ntb_id)
        self.assertIsNot(tmp['state'].find('done'), -1)

        # retrieve it
        self.payload['call'] = 'retrieve_notebook'
        self.assertEquals(self.cut._handle(self.payload)['notebook']['src'],
                          'import time\nfor i in range(0,10):'
                          '\n\ttime.sleep(1)')

        # delete it
        self.payload['call'] = 'delete_notebook'
        self.payload['notebook_id'] = self.ntb_id
        self.cut._handle(self.payload)


class ClassUnderTestWrapper(exec_node.ExecNode):
    """
    Wraps around the ExecNode and disables the listening.
    """

    def __init__(self, mongo_uri, amqp_uri, sdk, uid):
        self.uid = uid
        self.uri = mongo_uri
        self.sdk = sdk
        # store
        self.stor = proj_ntb_store.NotebookStore(mongo_uri, 'foo')