#!/bin/bash


apt-get update -qq
apt-get install -y mariadb-client iputils-ping

if ping -c 1 mariadb &> /dev/null
then
    HOST=mariadb
else
    HOST=localhost
fi

SQL="mysql -h $HOST -u root -proot -e"
$SQL "create user zoomuser identified by 'zoompass'"
$SQL "grant all on *.* to zoomuser"
$SQL "select host, user, password from mysql.user"

pip install -U pip
pip install .
pip install -r tests/requirements.txt

export PYTHONPATH=$(pwd)

zoom database -H $HOST -u zoomuser -p zoompass create zoomdata
zoom database -H $HOST -u zoomuser -p zoompass create zoomtest

export ZOOM_TEST_DATABASE_HOST=$HOST
export ZOOM_TEST_DATABASE_USER=zoomuser
export ZOOM_TEST_DATABASE_PASSWORD=zoompass

export ZOOM_DEFAULT_INSTANCE=$(pwd)/zoom/_assets/web
export ZOOM_DEFAULT_SITE_INI=$ZOOM_DEFAULT_INSTANCE/sites/localhost/site.ini

export ZOOM_TEST_LOG=$ZOOM_DEFAULT_INSTANCE

echo "host=$ZOOM_TEST_DATABASE_HOST" >> $ZOOM_DEFAULT_SITE_INI
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

echo "Done"
