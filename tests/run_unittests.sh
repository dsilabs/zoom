#!/bin/bash

pip install -U pip
pip install .
pip install -r tests/requirements.txt

export PYTHONPATH=$(pwd)

apt-get update -qq
apt-get install mariadb-client

mysql -e "create user zoomuser identified by 'zoompass'"
mysql -e "grant all on *.* to zoomuser"

zoom database -e mysql -H mariadb -u zoomuser -p zoompass create zoomdata
zoom database -e mysql -H mariadb -u zoomuser -p zoompass create zoomtest

export ZOOM_TEST_DATABASE_HOST=mariadb
export ZOOM_TEST_DATABASE_USER=zoomuser
export ZOOM_TEST_DATABASE_PASSWORD=zoompass

export ZOOM_DEFAULT_INSTANCE=$(pwd)/zoom/_assets/web
export ZOOM_DEFAULT_SITE_INI=$ZOOM_DEFAULT_INSTANCE/sites/localhost/site.ini

export ZOOM_TEST_LOG=$ZOOM_DEFAULT_INSTANCE

echo "host=mariadb" >> $ZOOM_DEFAULT_SITE_INI
echo "user=zoomuser" >> $ZOOM_DEFAULT_SITE_INI
echo "password=zoompass" >> $ZOOM_DEFAULT_SITE_INI

# get locales not included in base Python image
apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all

# set locale
export LC_ALL=C

cat $ZOOM_DEFAULT_SITE_INI

# run tests
pytest \
    -x \
    -v \
    --doctest-modules \
    --ignore=zoom/testing \
    --ignore=zoom/cli \
    --ignore=zoom/_assets \
    --ignore=tests/unittests/apps \
    zoom \
    tests/unittests
