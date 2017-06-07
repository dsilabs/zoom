"""
    zoom.user
"""

import logging

from zoom.users import Users
from zoom.context import context


def get_current_username(request):
    """get current user username"""
    site = request.site
    return (
        site.config.get('users', 'override', '') or
        getattr(request.session, 'username', None) or
        request.env.get('REMOTE_USER', None) or
        site.guest or
        None
    )


def handler(request, handler, *rest):
    """handle user"""
    logger = logging.getLogger(__name__)

    username = get_current_username(request)
    if username:
        users = Users(request.site.db)
        user = users.first(username=username)
        if user:
            context.user = request.user = user
            user.initialize(request)
            logger.debug('user loaded: %s (%r)', user.full_name, user.username)
    return handler(request, *rest)
