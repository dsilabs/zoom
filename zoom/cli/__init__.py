# -*- coding: utf-8 -*-
"""The Zoom CLI architecture."""

import sys

def finish(failure=False, *messages):
    """Finish a CLI invocation by outputting the given messages, optionally
    as an error."""
    for message in messages:
        print(message, file=sys.stderr if failure else sys.stdout)
    sys.exit(1 if failure else 0)
