"""
    users
"""

from zoom.apps import App

app = App()
app.menu = (
    'Overview', 'Apps', 'Users', 'Groups', 'Mail',
    'Requests', 'Activity', 'Errors', 'Audit',
    'Configuration', 'About'
)
