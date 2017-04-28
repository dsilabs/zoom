"""
    zoom.context
"""

import threading


context = threading.local()


def handler(request, handle, *rest):
    """context handler"""
    #
    # this could be implemented in a different way
    # where each handler has the opporunity to contribute
    # something to the context, but for now I am doing
    # it this way to see if the pattern makes sense.  How
    # we do it is an implementation detail - which will
    # affect how the framework evolves, but ideally not
    # so much how the framework is used.
    #
    context.request = request
    context.site = request.site
    context.user = request.user
    return handle(request, *rest)
