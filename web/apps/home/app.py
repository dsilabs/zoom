"""
    home app

    the users home desktop
"""


from zoom.page import page
from zoom.apps import get_apps
from zoom.html import ol
from zoom.helpers import link_to


def app(request):
    skip = ['home', 'logout']
    content = ol(
        repr(a) for a in sorted(get_apps(request), key=lambda a: a.title)
        if a.name not in skip and request.user.can_run(a)
    )
    return page(content, title="Apps")
