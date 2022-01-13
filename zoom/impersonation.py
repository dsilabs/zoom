"""
    impersonation
"""

import logging

import zoom
import zoom.html as h

logger = logging.getLogger(__name__)

def impersonate(username):
    """Impersonate a user"""
    zoom.authorize()
    user = zoom.get_site().users.locate(username)
    if user:
        session = zoom.system.request.session
        session.impersonated_user = username
        zoom.audit('start impersonating', zoom.system.request.user.username, username)


def get_current_username(request):
    """get actual current user username"""
    site = request.site
    return (
        getattr(request, 'username', None) or
        site.config.get('users', 'override', '') or
        getattr(request.session, 'username', None) or
        request.remote_user or
        site.guest or
        None
    )


def stop_impersonating(request):
    """Stop impersonating"""
    session = zoom.system.request.session
    if hasattr(session, 'impersonated_user'):
        impersonated_user = session.impersonated_user
        del session.impersonated_user
        actual_username = get_current_username(request)
        actual_user = zoom.system.site.users.first(username=actual_username)
        if actual_user:
            zoom.audit(
                'stop impersonating',
                actual_username,
                impersonated_user,
                user=actual_user,
                app_name='middlware'
            )
        else:
            logger.warning('Unable to log stop impersonating - unknown current user')


def get_impersonated_username():
    """Returns username of impersonated user or None"""
    session = zoom.system.request.session
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
        stop_impersonating(request)
        return zoom.redirect_to('/').render(request)
    return handle(request, *rest)
