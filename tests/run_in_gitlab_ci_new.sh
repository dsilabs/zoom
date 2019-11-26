#!/bin/bash

pip install .
pip install -r tests/requirements.txt

export PYTHONPATH=$(pwd)

zoom init /tmp/testinstance -H mariadb -u root -p root -d zoomdata -v root -q root
zoom new database zoomtest -H mariadb -u root -p root

export ZOOM_TEST_DATABASE_HOST=mariadb
export ZOOM_TEST_DATABASE_USER=root
export ZOOM_TEST_DATABASE_PASSWORD=root
export ZOOM_DATABASE_HOST=mariadb
# environment variables describing the instance we created as the default
export ZOOM_DEFAULT_INSTANCE=/tmp/testinstance
export ZOOM_DEFAULT_SITE=/tmp/testinstance/sites/localhost
export ZOOM_TEST_PATH=/tmp/testinstance/sites/localhost

# install google chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
apt-get -y update
apt-get install -y google-chrome-stable

# install chromedriver
apt-get install -yqq unzip
wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
export DISPLAY=:99

# get locales not included in base Python image
apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all

# set locale
export LC_ALL=C

# run zoom server
pushd /tmp/testinstance
zoom serve -p 8000 &
popd

cat /tmp/testinstance/sites/default/site.ini

nosetests --with-doctest --with-coverage --cover-package=zoom -vx zoom tests/unittests tests/apptests tests/webtests --exclude-dir=zoom/testing --exclude-dir=zoom/cli
