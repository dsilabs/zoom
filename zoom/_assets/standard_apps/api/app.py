"""
    zoom api
"""

from zoom.utils import create_csrf_token

def app(request):
    token = create_csrf_token()
    request.session.csrf_token = token
    return dict(
        status='200 OK',
        csrf_token=token
    )

