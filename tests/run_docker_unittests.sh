cd /work
apt-get update -qq

echo "installing the database"

export DEBIAN_FRONTEND=noninteractive
export MYSQL_ROOT_PASSWORD=root

apt-get update
apt-get install -y mariadb-server

service mariadb start

source tests/run_unittests.sh
