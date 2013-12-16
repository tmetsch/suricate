# Work in Progress

* General
    * Better error handling needed.
    * move this all to a trello board :-)
* Data:
    * in memory DB support (for caching)
    * Include object storage through CDMI?
    * Let Suricate download data (could be done by processing scripts now)
* Setup RESTful interface which supports:
    * Uploading data & notebooks
    * Add new streaming sources
    * trigger processing & analytics external
        * so you can write cron jobs :-)
        * support continuously running scripts.
* Analytics/Processing:
    * Rename processing to 'actionable analytics'?
    * versioning of analytics/processing notebooks (e.g. via github to also allow for sharing)
    * include external compute capacities?
    * Hadoop support? - Connect to OpenStack Savanna
    * support for inport/export ipython notebooks.
    * tagging of notebooks (example tags: Production, experimental, explorational, under development)
* web ui
    * responsive layout
    * D3 / Vega integration (via vincent, bokeh)
* packaging
    * pypi/conda
    * package runnable in OpenShift or similar
