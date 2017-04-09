"""
    sample app

    Demonstrates the user interface features of Zoom
"""

import logging


from zoom.apps import App

app = App()
app.menu = 'Content', 'Fields', 'Alerts'
