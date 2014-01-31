# coding=utf-8

"""
Serves as SDK for notebooks.
"""

__author__ = 'tmetsch'

import base64
import json
import os
import urllib

from StringIO import StringIO
from matplotlib import pyplot
from mpld3 import _objects

from data import object_store
from data import streaming

# Imports for easier analytics development
import numpy as np
import pandas as pd

# Storage access.
obj_str = object_store.MongoStore(OBJECT_STORE_URI)
stm_str = streaming.StreamClient(OBJECT_STORE_URI)

# setup figure
params = {'legend.fontsize': 9.0,
          'legend.linewidth': 0.5,
          'font.size': 9.0,
          'axes.linewidth': 0.5,
          'lines.linewidth': 0.5,
          'grid.linewidth':   0.5}
fig = pyplot.figure(1, figsize=(6, 4))
pyplot.rcParams.update(params)
pyplot.clf()

# To hide some stuff from the user.
os.environ = {}

# Constants
D3_URL = 'https://cdnjs.cloudflare.com/ajax/libs/d3/3.4.1/d3.min.js'


def show():
    """
    Show a matplotlib fig and stores it to be displayed as inline image.
    """
    tmp = StringIO()
    pyplot.savefig(tmp, format='png')
    uri = 'image:image/png;base64,' + \
          urllib.quote(base64.b64encode(tmp.getvalue()))
    print uri
    tmp.close()


def show_d3(figure=None):
    """
    Show matplotlib fig using d3.js.
    """
    if figure:
        img = _objects.D3Figure(figure).html(D3_URL)
    else:
        img = _objects.D3Figure(fig).html(D3_URL)
    dat = 'embed:'
    dat += img.replace('\n', '\r')
    print dat

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