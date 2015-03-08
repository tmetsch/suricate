# coding=utf-8

"""
Serves as SDK for notebooks.
"""

__author__ = 'tmetsch'

# basic imports
import base64
import json
import os
import urllib

from StringIO import StringIO

# graphing imports
try:
    import matplotlib
    matplotlib.use('cairo')
    from matplotlib import pyplot as plt
except UserWarning:
    pass
import mpld3

# internal imports
from suricate.data import object_store
from suricate.data import streaming

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
fig = plt.figure(1, figsize=(6, 4))
plt.rcParams.update(params)
plt.clf()

# To hide some stuff from the user.
os.environ = {}

# Constants
D3_URL = 'https://cdnjs.cloudflare.com/ajax/libs/d3/3.4.8/d3.min.js'


def show():
    """
    Show a matplotlib fig and stores it to be displayed as inline image.
    """
    tmp = StringIO()
    plt.savefig(tmp, format='png')
    uri = 'image/png;base64,' + \
          urllib.quote(base64.b64encode(tmp.getvalue()))
    print 'image:', uri
    tmp.close()


def show_d3(figure=None):
    """
    Show matplotlib fig using d3.js.
    """
    if figure:
        img = mpld3.fig_to_html(figure, d3_url=D3_URL)
    else:
        img = mpld3.fig_to_html(fig, d3_url=D3_URL)
    dat = img.replace('\n', '\r')
    print 'embed:', dat


def embed(content):
    """
    Embed content in output.
    """
    print 'embed:', content

# Everything below this line is basically an SDK...


def list_objects(tag='', with_meta=False):
    """
    List available object ids.

    :param tag: Optional tag to search for.
    :param with_meta: Indicates if metadata should be returned too.
    """
    if tag is not '':
        query = {'meta.tags':  tag}
    else:
        query = {}
    ids = obj_str.list_objects(str(UID), str(TOKEN), query=query)
    if with_meta:
        res = [item for item in ids]
    else:
        res = [item[0] for item in ids]
    return res


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
    if isinstance(tmp['value'], unicode):
        return json.loads(tmp['value'])
    return tmp['value']


def update_object(iden, data):
    """
    update an previously sotred data obj.

    :param iden: Identifier of the object.
    :param data: new contents.
    """
    obj_str.update_object(str(UID), str(TOKEN), iden, data)


def list_streams(tag=''):
    """
    List all available stream ids.

    :param tag: Optional tag to search for.
    """
    if tag is not '':
        query = {'meta.tags':  tag}
    else:
        query = {}
    ids = stm_str.list_streams(str(UID), str(TOKEN), query=query)
    return ids


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
