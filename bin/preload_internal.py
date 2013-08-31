# coding=utf-8

#   Copyright 2012-2013 Thijs Metsch - engjoy UG (haftungsbeschraenkt)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''
Will be preloaded and only run internally.
'''

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


def plot():
    '''
    Plots a matploglib fig and stores it to be displayed as inline image.
    '''
    tmp = StringIO()
    pyplot.savefig(tmp, format='png')
    uri = 'data:image/png;base64,' + \
          urllib.quote(base64.b64encode(tmp.getvalue()))
    print uri
    tmp.close()
    # pyplot.clf()


def list_objects():
    '''
    List available object ids.
    '''
    return obj_str.list_objects(str(UID), str(TOKEN))


def create_object(data):
    '''
    Create a new obj.

    :param data: Content to be stored.
    '''
    return obj_str.create_object(str(UID), str(TOKEN), json.dumps(data))


def retrieve_object(iden):
    '''
    Retrieve an previously store data obj.

    :param iden: Identifier of the object.
    '''
    tmp = obj_str.retrieve_object(str(UID), str(TOKEN), iden)
    print tmp
    return json.loads(tmp)


def list_streams():
    '''
    List all available stream ids.
    '''
    return stm_str.list_streams(str(UID), str(TOKEN))


def retrieve_from_stream(iden, interval=60):
    '''
    Return messages from a stream.

    :param iden: Identifier of the stream.
    :param interval: defaults to messages of last 60 seconds.
    '''
    return stm_str.get_messages(str(UID), str(TOKEN), interval, iden)