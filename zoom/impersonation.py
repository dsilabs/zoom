"""
    impersonation
"""

import zoom
import zoom.html as h


def impersonate(username):
    """Impersonate a user"""
    zoom.authorize()
    site = zoom.system.site
    if site.users.first(username=username):
        zoom.system.request.session.impersonated_user = username


def stop_impersonating():
    """Stop impersonating"""
    session = zoom.system.request.session
    if hasattr(session, 'impersonated_user'):
        del session.impersonated_user


def get_impersonated_username():
    """Returns username of impersonated user or None"""
    session = zoom.system.request.session
    # print(session)
    # print(getattr(session, 'impersonated_user', None))
    return getattr(session, 'impersonated_user', None)


def get_impersonation_notice():
    username = get_impersonated_username()
    if username is None:
        return ''
    return str(
        zoom.Component(
            h.div(
                'Impersonating {}'.format(username),
                zoom.link_to(
                    'Stop Impersonating',
                    '/stop-impersonation',
                    classed='action'
                ),
                id='impersonation-notice'
            )
        )
    )


def handler(request, handle, *rest):
    """impersonation handler"""
    if request.path == '/stop-impersonation':
        stop_impersonating()
        return zoom.redirect_to('/').render(request)
    return handle(request, *rest)
