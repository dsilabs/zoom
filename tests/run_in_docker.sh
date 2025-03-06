#!/bin/bash

VERBOSE=${VERBOSE:-0}
VERSIONS=${VERSIONS:-"3.7 3.8 3.9 3.12"}
SUITES=${SUITES:-"unit web"}

# Loop through each Python version
for VERSION in $VERSIONS
do
    CONTAINED_VERSION=$(docker run python:$VERSION python -V)
    echo "Running tests in $CONTAINED_VERSION container"

    if [ "$VERBOSE" -eq 1 ]; then
        FILTER="===\ .*\ passed"
        FILTER="| grep "$FILTER
    else
        FITLER=""
    fi

    for SUITE in $SUITES
    do
        SCRIPT="/work/tests/run_docker_"$SUITE"tests.sh"
        echo "Script: " $SCRIPT
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash $SCRIPT" \
            $FILTER
    done

done
