#!/bin/sh

cd tests/
nosetests --cover-erase --with-cover --cover-package analytics,data,web
cd ..

pylint -r n -i y analytics data tests web

pep8 -r analytics data tests web