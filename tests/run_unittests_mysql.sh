#!/bin/bash

pip install .
pip install -r tests/requirements.txt

export PYTHONPATH=$(pwd)
export ZOOM_TEST_DATABASE_HOST=mysql
export ZOOM_TEST_DATABASE_USER=root
export ZOOM_TEST_DATABASE_PASSWORD=root
export ZOOM_DEFAULT_INSTANCE=$(pwd)/zoom/_assets/web
export ZOOM_DEFAULT_SITE_INI=$ZOOM_DEFAULT_INSTANCE/sites/localhost/site.ini
export ZOOM_TEST_LOG=$ZOOM_DEFAULT_INSTANCE

zoom database \
    -e mysql \
    -H $ZOOM_TEST_DATABASE_HOST \
    -u $ZOOM_TEST_DATABASE_USER \
    -p $ZOOM_TEST_DATABASE_PASSWORD \
    create zoomdata

zoom database \
    -e mysql \
    -H $ZOOM_TEST_DATABASE_HOST \
    -u $ZOOM_TEST_DATABASE_USER \
    -p $ZOOM_TEST_DATABASE_PASSWORD \
    create zoomtest

cat <<EOL >> $ZOOM_DEFAULT_SITE_INI
host=$ZOOM_TEST_DATABASE_HOST
user=$ZOOM_TEST_DATABASE_USER
password=$ZOOM_TEST_DATABASE_PASSWORD
EOL

# get locales not included in base Python image
apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all

# set locale
export LC_ALL=C

cat $ZOOM_DEFAULT_SITE_INI

nosetests \
    --with-doctest \
    --with-coverage \
    --cover-package=zoom \
    -vx \
    --exclude-dir=zoom/testing \
    --exclude-dir=zoom/cli \
    zoom tests/unittests/test_database.py
