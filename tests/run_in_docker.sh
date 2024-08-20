#!/bin/bash

VERBOSE=${VERBOSE:-0}
VERSIONS=${VERSIONS:-"3.7 3.8 3.9 3.12"}

# Loop through each Python version
for VERSION in $VERSIONS
do
    echo "Running unittests in Python $VERSION"

    # Run the Docker command and conditionally apply grep based on VERBOSE
    if [ "$VERBOSE" -eq 1 ]; then
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash /work/tests/run_docker_unittests.sh"
    else
        docker run \
            -v $(pwd):/work \
            -it python:$VERSION \
            bash -c "bash /work/tests/run_docker_unittests.sh" \
            | grep "===\ .*\ passed"
    fi

done
