"""
    zoom.user
"""

import logging

from zoom.users import Users, get_current_username
from zoom.context import context


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
            request.profiler.add('user initialized')

    return handler(request, *rest)
