"""
    users
"""

from zoom.apps import App

app = App()
app.menu = (
    'Overview', 'Apps', 'Users', 'Groups', 
    'Database', 'Mail',
    'Requests', 'Activity', 'Errors', 'Audit',
    'Configuration', 'About'
)
