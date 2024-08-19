cd /work
apt-get update -qq

echo "installing the database"

# echo "127.0.0.1 mariadb" | tee -a /etc/hosts
export DEBIAN_FRONTEND=noninteractive
export MYSQL_ROOT_PASSWORD=root

# apt-get update
# apt-get install -y wget gnupg
# wget -qO /etc/apt/trusted.gpg.d/mariadb_release_signing_key.asc https://mariadb.org/mariadb_release_signing_key.asc
# echo "deb [arch=amd64,arm64,ppc64el] http://mirror.nodesdirect.com/mariadb/repo/10.7/debian bookworm main" > /etc/apt/sources.list.d/mariadb.list

# apt-get install software-properties-common dirmngr -y
# wget -qO /etc/apt/trusted.gpg.d/mariadb_release_signing_key.asc https://mariadb.org/mariadb_release_signing_key.asc
# add-apt-repository -y 'deb [arch=amd64,arm64,ppc64el] http://mirror.nodesdirect.com/mariadb/repo/10.7/ubuntu focal main'

# apt-key adv --fetch-keys 'https://mariadb.org/mariadb_release_signing_key.asc'
# add-apt-repository -y 'deb [arch=amd64,arm64,ppc64el] http://mirror.nodesdirect.com/mariadb/repo/10.7/ubuntu focal main'
apt-get update
apt-get install -y mariadb-server

service mariadb start

# mysql -u root -e "SET PASSWORD FOR root@'localhost' = PASSWORD('root'); FLUSH PRIVILEGES;"

# mysql -u root -proot -e "UPDATE mysql.user SET host='%' WHERE user='root'; FLUSH PRIVILEGES;"

# bash

# apt-get update -qq
# apt-get install -y mariadb-server-10.7

# # apt-get install -yqq mariadb-server

# service mariadb start

# bash

# mysql -e "select host, user, password from mysql.user"

# mysql -e "create user zoomuser identified by 'zoompass'"
# mysql -e "grant all on *.* to zoomuser"

# mysql -e "select host, user, password from mysql.user"

# mysql -h mariadb -u zoomuser -pzoompass -e "show databases"

source tests/run_unittests.sh

# bash