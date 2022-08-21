"""
    zoom.auditing
"""

import zoom

def audit(action, subject1, subject2='', user=None, app_name=None):
    """audit an action"""
    db = zoom.system.site.db
    user_id = user.user_id if user else zoom.system.user.user_id
    app = app_name or zoom.system.request.app.name
    cmd = """
    insert into audit_log (
        app,
        user_id,
        activity,
        subject1,
        subject2,
        timestamp
    ) values (%s, %s, %s, %s, %s, %s)
    """
    db(
        cmd,
        app,
        user_id,
        action,
        subject1,
        subject2,
        zoom.tools.now(),
    )
