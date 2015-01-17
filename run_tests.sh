#!/bin/sh

cd tests/
nosetests --cover-erase --with-cover --cover-package suricate
cd ..

pylint -r n suricate

pep8 -r suricate bin