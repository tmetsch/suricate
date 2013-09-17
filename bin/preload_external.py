# coding=utf-8

'''
Will be preloaded and exported.
'''

__author__ = 'tmetsch'

from matplotlib import pyplot

params = {'legend.fontsize': 9.0,
          'legend.linewidth': 0.5,
          'font.size': 9.0,
          'axes.linewidth': 0.5,
          'lines.linewidth': 0.5,
          'grid.linewidth':   0.5}

fig = pyplot.figure(1, figsize=(3, 3))
pyplot.rcParams.update(params)
pyplot.clf()


def plot():
    '''
    Shows a matplotlib figure.
    '''
    pyplot.show()
    pyplot.clf()
