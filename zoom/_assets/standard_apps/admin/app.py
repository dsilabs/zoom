"""
    users
"""

from zoom.apps import App

app = App()
app.menu = (
    'Overview', 'Users', 'Groups', 'Apps',
    'Jobs', 'Database', 'Mail',
    'Requests', 'Activity', 'Errors', 'Warnings', 'Audit',
    'Configuration', 'Environment', 'About'
)
