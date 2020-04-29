"""run: Run Zoom resources.

Usage:
  zoom run background [options] [<path>]

Options:
  -h, --help                  Show this message and exit.
%s
  -r, --repeat                Repeat running jobs indefinitely.
  -t, --timeout=<val>         The amount of time to run background jobs for
                              before stopping. A value of 0 is identical to
                              specifying --repeat. In seconds.
  -d, --delay=<val>           When running jobs repeatedly, the delay between
                              ticks. Defaults to 1 second.
"""

import os
import time
import logging

from docopt import docopt

from zoom.sites import Site
from zoom.instances import Instance
from zoom.cli.common import LOGGING_OPTIONS, setup_logging
from zoom.cli.utils import resolve_path_with_context, describe_options, \
    finish, is_instance_dir

logger = logging.getLogger(__name__)

def run():
    arguments = docopt(run.__doc__)

    # Configure logging.
    setup_logging(arguments)

    # Resolve the target instance.
    instance_path = resolve_path_with_context(
        arguments.get('<path>') or '.', instance=True
    )
    if not is_instance_dir(instance_path):
        finish(True, 'Error: "%s" is not a Zoom instance'%instance_path)
    instance = Instance(instance_path)

    # Parse and comprehend options.
    repeat = arguments.get('--repeat')
    timeout = arguments.get('--timeout') or -1
    delay = arguments.get('--delay') or 1
    try:
        timeout = int(timeout)
        delay = int(delay)
    except ValueError:
        finish(True, 'Error: invalid timeout or delay')

    indefinite = repeat or timeout == 0
    only_once = timeout == -1

    # State runtime options.
    if indefinite:
        logger.debug('will repeat indefinitely with delay %d second(s)', delay)
    elif only_once:
        logger.debug('will scan once')
    else:
        logger.debug(
            'will repeat for %s second(s) with delay %s seconds(s)',
            timeout, delay
        )

    # Mark start.
    start_time = time.time()
    try:
        while True:

            instance.run_background_jobs()

            # Check whether we're done.
            if not indefinite and only_once:
                break
            elapsed_time = time.time() - start_time
            if not indefinite and elapsed_time >= timeout:
                break

            # Sleep the delay in 1 second intervals to allow nice SIGINT
            # pickup.
            sleep_time = 0
            while sleep_time < delay:
                time.sleep(1)
                sleep_time += 1

    except KeyboardInterrupt:
        print('\rstopped')

run.__doc__ = __doc__%describe_options(LOGGING_OPTIONS)
