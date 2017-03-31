"""
    zoom.user
"""

import logging

from zoom.users import Users


def get_current_username(request):
    site = request.site
    return (
        site.config.get('users', 'override', '') or
        getattr(request.session, 'username', None) or
        request.env.get('REMOTE_USER', None) or
        site.guest or
        None
    )


def user_handler(request, handler, *rest):
    logger = logging.getLogger(__name__)

    username = get_current_username(request)
    if username:
        users = Users(request.site.db)
        user = users.first(username=username)
        if user:
            request.user = user
            user.request = request
            logger.debug('user loaded: %s (%r)', user.full_name, user.username)
    return handler(request, *rest)
