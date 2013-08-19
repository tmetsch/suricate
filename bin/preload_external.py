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
Will be preloaded and exported.
'''

__author__ = 'tmetsch'

from matplotlib import pyplot

params = {'legend.fontsize': 11,
          'legend.linewidth': 1}

fig = pyplot.figure(1, figsize=(3, 3))
pyplot.rcParams.update(params)


def plot():
    '''
    Shows a matplotlib figure.
    '''
    pyplot.show()
    pyplot.clf()