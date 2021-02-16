"""
    zoom.context
"""

import threading


context = threading.local()
context.request = None
context.site = None
context.user = None
context.response = None
context.providers = []
