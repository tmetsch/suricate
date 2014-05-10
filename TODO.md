## General
- [x] Better error handling needed.
- [x] backends for handling notebooks execution (isolate with cgroups & subprocess?)
- [x] simple flows for data through program: frontend (UI) - backends - final execution
- [ ] split web frontend from an engine.

## Data:
- [ ] in memory DB support (for caching)
- [ ] Include object storage through CDMI?
- [ ] Let Suricate download data (could be done by new scripts in project now)
- [ ] FIX: do not cache data coming from stream...(zmq?)
- [x] data tagging & then retrieve objects streams via tag queries
- [x] download data objects.

## Setup RESTful interface which supports:
- [ ] Uploading data & notebooks
- [ ] Add new streaming sources
- [ ] trigger processing & analytics external
   - [ ] Trigger execution of projects/notebooks with parameters (files, attributes, ...) from other apps/web frontends so endusers benefit
   - [ ] so you can write cron jobs :-)
   - [ ] support continuously running scripts.

## Analytics/Processing:
- [ ] Run exec_node as http://www.zerovm.org to bring data and compute closer together.
   - [ ] for storage then use swift...
- [x] run notebooks as (remote) jobs to support longrunning tasks & have job lists with states,
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
    - [ ] sharing of notebooks
- [ ] store projects/notebooks with iden of mongo not the name - put that in meta.

## Packaging
- [ ] pypi/conda
- [ ] package runnable in OpenShift or similar

## Fixes
- [x] firefox just not jump to end in input field
- [x] move js and css loading to base
- [ ] unittests

## web ui
- [x] Clear done jobs from list
- [x] responsive layout (See: http://purecss.io/layouts/side-menu/)
- [x] D3 / Vega integration (via vincent, bokeh)
- [x] Consistency on where to place download, delete action buttons
- [x] tiles for projects & notebooks & data srcs & create operation (have tags in it etc.)
- [x] output code divs & newlines should be fixed (in output and error)
- [x] messages div have wrong padding box.
- [ ] Print button
- [ ] Build workflows/processes - graph editor
- [ ] dashboard support through templating
