
import unittest
import analytics.proc_backend

class NotebookProcessingTest(unittest.TestCase):
    '''
    Test the processing backend for processes.
    '''

    def test_push_code(self):
        tmp = analytics.proc_backend.PythonWrapper()
        # tmp.run('dir()')
        self.assertTrue(False)
