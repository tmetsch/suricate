# coding=utf-8

'''
Module for the handling of notebooks.
'''

__author__ = 'tmetsch'

import code
import pymongo
import sys
import uuid

import ConfigParser

from bson import son

from StringIO import StringIO
from collections import OrderedDict

config = ConfigParser.RawConfigParser()
config.read('app.conf')
preload_int = config.get('suricate', 'preload_int')
preload_ext = config.get('suricate', 'preload_ext')

# This preload will be downloaded with the notebook.
PRELOAD = file(preload_ext, 'r').read()

# Preload 2 will not be download with the notebook!
PRELOAD2 = file(preload_int, 'r').read()


def grep_stdout(func):
    '''
    Wrap stderr and stdout to a str return value.
    :param func:
    '''

    def wrap(*args):
        '''
        Wraps a function.

        :param args: Bunch of Arguments.
        '''
        old_out = sys.stdout
        old_err = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        func(*args)
        err = sys.stderr.getvalue()
        print err  # make sure err can be retrieved!
        out = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_out
        sys.stderr = old_err
        return out
    return wrap


class ConsoleWrapper(object):
    '''
    Wraps around a single python console interpreter.
    '''

    def __init__(self, iden, collection, init_src, uid):
        self.iden = iden
        self.collection = collection
        # Needs to be ordered!!!
        self.src = OrderedDict(init_src)
        self.console = code.InteractiveConsole()
        # set User identifier!
        self.console.push('suricate_uid = ' + str(uid))
        self.console.runcode(PRELOAD)
        self.console.runcode(PRELOAD2)
        self.white_space = ''

    @grep_stdout
    def _run_line(self, line):
        '''
        Run single line of python code.
        '''
        cont = self.console.push(line)
        if cont and line.lstrip()[:3] in ['for', 'if ']:
            self.white_space += '    '
        else:
            self.white_space = ''

    def _rerun(self):
        '''
        Reset buffer and rerun all.
        '''
        self.console.resetbuffer()
        nw_src = OrderedDict({})
        for item in self.src:
            iden = item
            loc = self.src[item][0]
            out = self._run_line(loc)
            nw_src[iden] = (loc, out)
        self.src = nw_src

    def add_lines(self, code_lines):
        '''
        Add multiple lines of source code.

        TODO: check necessity.

        :param code_lines: List of lines of code.
        '''
        for line in code_lines:
            self.add_line(line)

    def get_lines(self):
        '''
        Retrieve the source code.
        '''
        # List is ordered!
        res = []
        for line in self.src.values():
            res.append(line[0])
        return res

    def add_line(self, line):
        '''
        Add a single source code line.

        :param line: Single line of Python code.
        '''
        iden = str(uuid.uuid4())
        out = self._run_line(line)
        self.src[iden] = (line, out)
        self.collection.update({'_id': self.iden},
                               {"$set": {'code': son.SON(self.src)}},
                               upsert=False)
        return iden

    def remove_line(self, iden):
        '''
        Remove a line. Means we need to rerun all code :-(

        :param iden: Identifier of the line.
        '''
        self.src.pop(iden)
        # now we need to rerun all :-( could have been important line...
        self._rerun()
        # store it
        self.collection.update({'_id': self.iden},
                               {"$set": {'code': son.SON(self.src)}},
                               upsert=False)

    def update_line(self, iden, line, replace=True):
        '''
        Update a code passage.

        :param line: Line of Python code.
        :param iden: Identifier of the line.
        :param replace: Defaults to True - If True will replace,
        otherwise append.
        '''
        if replace:
            # the + '\n' is so that interpreter execute the code block!
            self.src[iden] = (line + '\n', None)
        else:
            self.src[iden] = (self.src[iden][0] + '\n' + line, None)
        # now we need to rerun all :-( could have been important line...
        self._rerun()
        # store it
        self.collection.update({'_id': self.iden},
                               {"$set": {'code': son.SON(self.src)}},
                               upsert=False)

    def get_results(self):
        '''
        Retrieve the coding results.
        '''
        return self.src


class NotebookStore(object):
    '''
    Stores Notebooks in a MongoDB collection.
    '''

    # XXX: Problem there is that there is no guarantee the order of the
    # OrderedDict coming from MongoDB. The as_class helps prevent this!

    def __init__(self, host, port):
        self.client = pymongo.MongoClient(host, port)
        self.cache = {}

    def get_notebook(self, uid, iden, init_code=None):
        '''
        Retrieve a notebook if existing - otherwise creates new one.

        :param iden: Identifier of the notebook.
        :param uid: User id.
        :param init_code: (Optional) List of lines of code.
        '''
        if not init_code:
            init_code = []
        if iden + uid in self.cache:
            return self.cache[iden + uid]
        else:
            db = self.client[uid]
            collection = db['notebooks']
            # XXX: the as_class is important - see note above!
            content = collection.find_one({'iden': iden}, as_class=OrderedDict)
            if content is None:
                collection.insert({'iden': iden, 'code': {}})
                content = collection.find_one({'iden': iden},
                                              as_class=OrderedDict)
            wrapper = ConsoleWrapper(content['_id'], collection,
                                     content['code'], uid)

            # uploaded code...
            to_add = []
            for line in init_code:
                if len(line.strip()) == 0:
                    continue
                if line[:4] != '    ':
                    to_add.append(line)
                else:
                    to_add.append(to_add.pop() + '\n' + line)
            for line in to_add:
                wrapper.add_line(line)

            self.cache[iden+uid] = wrapper
            return wrapper

    def delete_notebook(self, uid, iden):
        '''
        Deletes a notebook from the storage.

        :param uid: User id.
        :param iden: Idnetifier for the notebook.
        '''
        db = self.client[uid]
        collection = db['notebooks']
        collection.remove({'iden': iden})

    def list_notebooks(self, uid):
        '''
        Lists all notebook names.

        :param uid: User id.
        '''
        db = self.client[uid]
        collection = db['notebooks']
        tmp = collection.find(fields={'iden': True, '_id': False})
        res = []
        for item in tmp:
            res.append(item['iden'])
        return res
