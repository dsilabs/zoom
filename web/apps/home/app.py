
from zoom.page import page
from zoom.apps import get_apps
from zoom.html import ol
from zoom.helpers import link_to


def app(request):
    content = ol(
        repr(a) for a in get_apps(request)
        if a.name != 'home'
    )
    return page(content)
