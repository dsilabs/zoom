#!/bin/bash

pip install .
pip install -r tests/requirements.txt

export PYTHONPATH=$(pwd)

zoom database -e mysql -H mariadb -u root -p root create zoomdata
zoom database -e mysql -H mariadb -u root -p root create zoomtest

export ZOOM_TEST_DATABASE_HOST=mariadb
export ZOOM_TEST_DATABASE_USER=root
export ZOOM_TEST_DATABASE_PASSWORD=root

export ZOOM_DEFAULT_INSTANCE=$(pwd)/zoom/_assets/web
export ZOOM_DEFAULT_SITE_INI=$ZOOM_DEFAULT_INSTANCE/sites/localhost/site.ini

export ZOOM_TEST_LOG=$ZOOM_DEFAULT_INSTANCE

echo "host=mariadb" >> $ZOOM_DEFAULT_SITE_INI
echo "user=root" >> $ZOOM_DEFAULT_SITE_INI
echo "password=root" >> $ZOOM_DEFAULT_SITE_INI

# get locales not included in base Python image
apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all

# set locale
export LC_ALL=C

cat $ZOOM_DEFAULT_SITE_INI

pytest --doctest-modules --ignore=zoom/testing --ignore=zoom/cli --ignore=zoom/_assets zoom
pytest --ignore=tests/unittests/apps --cov tests/unittests
