## General
- [x] Better error handling needed.
- [x] backends for handling notebooks execution (isolate with cgroups & subprocess?)
- [x] simple flows for data through program: frontend (UI) - backends - final execution

## Data:
- [ ] in memory DB support (for caching)
- [ ] Include object storage through CDMI?
- [ ] Let Suricate download data (could be done by new scripts in project now)
- [ ] FIX: do not cache data coming from stream...(zmq?)
- [ ] data tagging & then retrieve objects streams via tag queries
- [ ] download data objects.

## Setup RESTful interface which supports:
- [ ] Uploading data & notebooks
- [ ] Add new streaming sources
- [ ] trigger processing & analytics external
   - [ ] so you can write cron jobs :-)
   - [ ] support continuously running scripts.

## Analytics/Processing:
- [ ] run n otebooks as (remote ) jobs , have job lists with states, to support longrunning jobs
- [x] Interactive command should be presented in output as well - maybe as comment?
- [ ] richer SDK (Analytics/Processing Development Kit)
- [ ] Versioning of analytics/processing notebooks (e.g. via github to also allow for sharing)
- [ ] include external compute capacities?
- [ ] Hadoop support? - Connect to OpenStack Savanna
- [ ] support for import/export ipython notebooks.
- [ ] tagging of notebooks (example tags: Production, experimental, explorational, under development)
- [ ] Support for Julia, R, ...
- [x] management of notebooks in project which are then shareable -> exec node per project for better isolation!
    - [ ] could be git repositories with the code in it... 
    - [ ] have samples hosted on github for direct cloning and testing the service.

## Packaging
- [ ] pypi/conda
- [ ] package runnable in OpenShift or similar

## Fixes
- [x] firefox just not jump to end in input field
- [x] move js and css loading to base
- [ ] unittests

## web ui
- [x] responsive layout (See: http://purecss.io/layouts/side-menu/)
- [x] D3 / Vega integration (via vincent, bokeh)
- [ ] Consistency on where to place download, delete action buttons
- [ ] messages dov have wrong padding box.
