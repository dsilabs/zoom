#!/bin/bash

pip3.7 install -r requirements.txt
pip3.7 install -r tests/requirements.txt

bin/zoom database -e mysql -H mariadb -u root -p root create zoomdata
bin/zoom database -e mysql -H mariadb -u root -p root create zoomtest

export ZOOM_TEST_DATABASE_HOST=mariadb
export ZOOM_TEST_DATABASE_USER=root
export ZOOM_TEST_DATABASE_PASSWORD=root
export ZOOM_DATABASE_HOST=mariadb

echo "host=mariadb" >> web/sites/localhost/site.ini
echo "user=root" >> web/sites/localhost/site.ini
echo "password=root" >> web/sites/localhost/site.ini

cat web/sites/localhost/site.ini
nosetests --with-coverage --cover-package=zoom -vx zoom tests/unittests --exclude-dir=zoom/
