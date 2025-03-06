cd /work
apt-get update -qq

echo "installing the database"

export DEBIAN_FRONTEND=noninteractive
export MYSQL_ROOT_PASSWORD=root

apt-get update -qq
apt-get install -y -qqq mariadb-server

service mariadb start

source tests/run_webtests.sh
