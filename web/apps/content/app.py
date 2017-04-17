"""
    zoom content app
"""
from zoom.page import page
from zoom.tools import load_content

def app(request):
    content = load_content('content.md')
    return page(content)
