"""
Adapters for different languages.
"""
import ConfigParser

import code
import sys

import StringIO
import urlparse

CONFIG = ConfigParser.RawConfigParser()
CONFIG.read('app.conf')


def grep_stdout(func):
    """
    Wrap stderr and stdout to a str return value.
    :param func:
    """

    def wrap(*args):
        """
        Wraps a function.

        :param args: Bunch of Arguments.
        """
        old_out = sys.stdout
        old_err = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
        func(*args)
        err = sys.stderr.getvalue()
        out = sys.stdout.getvalue().strip().split('\n')
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_out
        sys.stderr = old_err
        return out, err
    return wrap


class PythonWrapper(object):
    """
    Wrapper to use Python for Analytics.
    """

    def __init__(self, uid, token, mongo_uri):
        self.console = code.InteractiveConsole()
        sdk = CONFIG.get('suricate', 'python_sdk')
        # set User identifier and tell where object store is.
        self.console.push('UID = \'' + str(uid) + '\'')
        self.console.push('TOKEN = \'' + str(token) + '\'')
        uri = urlparse.urlparse(mongo_uri)
        str_uri = uri.scheme + '://'+ uid + ':' + token + '@' + uri.netloc \
                  + '/' + uid
        self.console.push('OBJECT_STORE_URI = \'' + str(str_uri) + '\'')
        # This preload will be downloaded with the notebook.
        preload = file(sdk).read()
        self.console.runcode(preload)

    @grep_stdout
    def run(self, src):
        """
        Run some code.
        """
        self.console.resetbuffer()
        self.console.runcode(src)

    @grep_stdout
    def interact(self, loc):
        """
        Interact with the interpreter directly.
        """
        self.console.push(loc)


class RWrapper(object):
    """
    Wrapper to use the R language...
    """

    pass