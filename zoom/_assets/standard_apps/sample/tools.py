"""
    sample tools

    show examples of the tools module
"""

import time
import sys

from zoom.page import page
from zoom.utils import pp

import zoom.tools as tools

def main(route, request):

    content = tools.markdown("""

Time
----

now()
: {now}

today()
: {today}

yesterday()
: {yesterday}

tomorrow()
: {tomorrow}

this_month()
: {this_month}

next_month()
: {next_month}

last_month()
: {last_month}

        """).format(
            now=tools.now(),
            today=tools.today(),
            yesterday=tools.yesterday(),
            tomorrow=tools.tomorrow(),
            this_month=tools.this_month(tools.today()),
            next_month=tools.next_month(tools.today()),
            last_month=tools.last_month(tools.today()),
        )

    return page(content, 'Tools')
