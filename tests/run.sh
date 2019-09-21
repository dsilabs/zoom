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

# run zoom server
python3.7 bin/zoom server -p 8000 web &

cat web/sites/localhost/site.ini

nosetests --with-coverage --cover-package=zoom -vx
