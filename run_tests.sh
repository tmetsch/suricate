#!/bin/sh

cd tests/
nosetests --cover-erase --with-cover --cover-package api,analytics,data,web
cd ..

pylint -r n -i y analytics api data tests web

pep8 -r analytics api data tests web