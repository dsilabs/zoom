"""
    zoom content app
"""
from zoom.page import page
from zoom.render import render

def app(request):
    content = render('content.md')
    return page(content)
