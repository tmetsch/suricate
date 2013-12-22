# Work in Progress

* General
    * Better error handling needed.
    * move this all to a trello board :-)
    * General restructering of architecture/code:
        * backends for handling notebooks execution (isolate with cgroups & subprocess?)
        * simple flows fo data through program: frontend (UI) - backends - final execution
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
    * richer SDK in preload internal.
    * Rename processing to 'actionable analytics'?
    * versioning of analytics/processing notebooks (e.g. via github to also allow for sharing)
    * include external compute capacities?
    * Hadoop support? - Connect to OpenStack Savanna
    * support for inport/export ipython notebooks.
    * tagging of notebooks (example tags: Production, experimental, explorational, under development)
* web ui
    * D3 / Vega integration (via vincent, bokeh)
* packaging
    * pypi/conda
    * package runnable in OpenShift or similar

# Done

* web ui
    * responsive layout (See: http://purecss.io/layouts/side-menu/)
