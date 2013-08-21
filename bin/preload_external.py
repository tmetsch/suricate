# coding=utf-8

'''
Will be preloaded and exported.
'''

__author__ = 'tmetsch'

from matplotlib import pyplot

params = {'legend.fontsize': 11,
          'legend.linewidth': 1}

fig = pyplot.figure(1, figsize=(3, 3))
pyplot.rcParams.update(params)
pyplot.clf()


def plot():
    '''
    Shows a matplotlib figure.
    '''
    pyplot.show()
    pyplot.clf()
