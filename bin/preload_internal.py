# coding=utf-8

"""
Will be preloaded and only run internally.
"""

__author__ = 'tmetsch'

import base64
import json
import os
import urllib

from StringIO import StringIO

from data import object_store
from data import streaming

obj_str = object_store.MongoStore(OBJECT_STORE_URI)
stm_str = streaming.StreamClient(OBJECT_STORE_URI)
# To hide some stuff from the user.
os.environ = {}


def show():
    """
    Show a matplotlib fig and stores it to be displayed as inline image.
    """
    tmp = StringIO()
    #axes = pyplot.axes()
    #axes.spines['top'].set_color('none')
    #axes.spines['right'].set_color('none')
    #axes.tick_params(direction='out', pad=5)
    #axes.xaxis.set_ticks_position('bottom')
    #axes.yaxis.set_ticks_position('left')
    pyplot.savefig(tmp, format='png')
    uri = 'data:image/png;base64,' + \
          urllib.quote(base64.b64encode(tmp.getvalue()))
    print uri
    tmp.close()
    # pyplot.clf()


# def show_d3():
#     """
#     Show matplotlib fig using d3.js.
#     """
#     img = _objects.D3Figure(fig).html()
#     dat = 'd3js:'
#     dat += img
#     print dat

# Everything below this line is basically an SDK...


def list_objects():
    """
    List available object ids.
    """
    return obj_str.list_objects(str(UID), str(TOKEN))


def create_object(data):
    """
    Create a new obj.

    :param data: Content to be stored.
    """
    return obj_str.create_object(str(UID), str(TOKEN), json.dumps(data))


def retrieve_object(iden):
    """
    Retrieve an previously store data obj.

    :param iden: Identifier of the object.
    """
    tmp = obj_str.retrieve_object(str(UID), str(TOKEN), iden)
    return json.loads(tmp)


def update_object(iden, data):
    """
    update an previously sotred data obj.

    :param iden: Identifier of the object.
    :param data: new contents.
    """
    obj_str.update_object(str(UID), str(TOKEN), iden, data)


def list_streams():
    """
    List all available stream ids.
    """
    return stm_str.list_streams(str(UID), str(TOKEN))


def retrieve_from_stream(iden, interval=60):
    """
    Return messages from a stream.

    :param iden: Identifier of the stream.
    :param interval: defaults to messages of last 60 seconds.
    """
    return stm_str.get_messages(str(UID), str(TOKEN), interval, iden)


def run_analytics(iden):
    """
    Run an analytics notebook.

    :param iden: Identifier of the notebook.
    """
    # TODO: implement this one...
    pass
