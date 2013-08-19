#!/usr/bin/env python
# coding=utf-8

'''
Setuptools file.
'''

__author__ = 'tmetsch'

from distutils.core import setup

setup(name='suricate',
      version='1.0',
      description='Analytics as a Service',
      author='Thijs Metsch',
      author_email='tmetsch@engjoy.eu',
      url='http://engjoy.eu',
      packages=['web'],
      requires=['bottle', 'pymongo', 'matplotlib'],
     )