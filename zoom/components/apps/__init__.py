"""
    apps components
"""

import zoom

class AppMenuItem(zoom.component.DynamicComponent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        zoom.requires('fontawesome4', 'bootstrap-icons')
