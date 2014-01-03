# General
- [ ] Better error handling needed.
- [x] move this all to a trello board :-)

## Data:
    * in memory DB support (for caching)
    * Include object storage through CDMI?
    * Let Suricate download data (could be done by processing scripts now)
    * FIX: do not cache data coming from stream...(zmq?)
    * data tagging
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
    * support for import/export ipython notebooks.
    * tagging of notebooks (example tags: Production, experimental, explorational, under development)
* packaging
    * pypi/conda
    * package runnable in OpenShift or similar
* Fixes
    * firefox just not jump to end in input field

# Done

* web ui
    * responsive layout (See: http://purecss.io/layouts/side-menu/)
    * D3 / Vega integration (via vincent, bokeh)
* General restructering of architecture/code:
    * backends for handling notebooks execution (isolate with cgroups & subprocess?)
    * simple flows fo data through program: frontend (UI) - backends - final execution
