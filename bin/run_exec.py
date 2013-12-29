#!/usr/bin/env python

# coding=utf-8

"""
Runs an execution node.
"""

import sys

import ConfigParser

from analytics import exec_node

__author__ = 'tmetsch'

config = ConfigParser.RawConfigParser()
config.read('app.conf')
# MongoDB connection
host = config.get('mongo', 'host')
port = config.get('mongo', 'port')
# Rabbit part
uri = config.get('rabbit', 'uri')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise AttributeError('please provide a tenant id for this execution '
                             'node as first argument!')
        sys.exit(1)

    user = sys.argv[1]
    mongo = 'mongodb://' + host + ':' + port
    aqmp = uri
    exec_node.ExecNode(mongo, aqmp, user)
