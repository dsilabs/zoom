"""
    settings.index
"""

import zoom

def view(**_):
    content = 'System settings will go here.'
    return zoom.page(content, title='Settings')
