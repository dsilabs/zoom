"""
    zoom.tools
"""

from zoom.response import RedirectResponse
from zoom.helpers import abs_url_for


def redirect_to(*args, **kwargs):
    """Return a redirect response for a URL."""
    abs_url = abs_url_for(*args, **kwargs)
    return RedirectResponse(abs_url)


def warning(message):
    pass
