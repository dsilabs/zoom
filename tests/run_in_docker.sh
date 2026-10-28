#!/bin/bash

VERBOSE=${VERBOSE:-0}
VERSIONS=${VERSIONS:-"3.7 3.8 3.9 3.12"}
SUITES=${SUITES:-"unit web"}
IMAGE=dsilabs/testbase

# Loop through each Python version
for VERSION in $VERSIONS
do
    CONTAINED_VERSION=$(docker run $IMAGE:$VERSION python -V)

    for SUITE in $SUITES
    do
        echo "Running $SUITE tests in $CONTAINED_VERSION container"

        SCRIPT="/work/tests/run_docker_"$SUITE"tests.sh"
        COMMAND="docker run -v $(pwd):/work -it $IMAGE:$VERSION bash $SCRIPT"

        if [ "$VERBOSE" -eq 1 ]; then
            $COMMAND
        else
            $COMMAND | grep '===\ .*\ passed'
        fi

    done

    git checkout -q zoom/_assets/web/sites/localhost/site.ini

done

git checkout -q zoom/_assets/web/sites/localhost/site.ini
