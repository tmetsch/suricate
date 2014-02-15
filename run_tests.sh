#!/bin/sh

cd tests/
nosetests --cover-erase --with-cover --cover-package analytics,data,ui
cd ..

pylint -r n -i y analytics data ui

pep8 -r analytics bin data ui