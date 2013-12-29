#!/bin/sh

cd tests/
nosetests --cover-erase --with-cover --cover-package analytics,data,web
cd ..

pylint -r n -i y analytics data web

pep8 -r analytics bin data web