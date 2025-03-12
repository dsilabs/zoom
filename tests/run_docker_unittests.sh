cd /work

echo "starting the database"

service mariadb start

source tests/run_unittests.sh
