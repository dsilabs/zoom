#!/bin/bash

VERBOSE=${VERBOSE:-0}
VERSIONS=${VERSIONS:-"3.7 3.8 3.9 3.12"}

# Loop through each Python version
for VERSION in $VERSIONS
do
    CONTAINED_VERSION=$(docker run python:$VERSION python -V)
    echo "Running tests in $CONTAINED_VERSION container"

    # Run the Docker command and conditionally apply grep based on VERBOSE
    if [ "$VERBOSE" -eq 1 ]; then
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash /work/tests/run_docker_unittests.sh"
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash /work/tests/run_docker_webtests.sh"
    else
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash /work/tests/run_docker_unittests.sh" \
            | grep "===\ .*\ passed"
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash /work/tests/run_docker_webtests.sh" \
            | grep "===\ .*\ passed"
    fi

    git checkout -q zoom/_assets/web/sites/localhost/site.ini

done
