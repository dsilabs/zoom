"""
    zoom.audit

    Requires the zoom.context middleware.
"""

import logging

from zoom.context import context
from zoom.tools import now

def audit(action, subject1, subject2, user=None):
    """audit an action"""
    db = context.site.db
    user_id = user and user._id or context.user._id
    app_name = context.request.app.name
    cmd = """
    insert into audit_log (
        app,
        user_id,
        activity,
        subject1,
        subject2,
        timestamp
    ) values (%s,%s,%s,%s,%s,%s)
    """
    db(cmd,
        app_name,
        user_id,
        action,
        subject1,
        subject2,
        now(),
    )
