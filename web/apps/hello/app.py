
from zoom.html import ul
from zoom.page import page
from zoom.helpers import link_to

def app(request):
    content = ul(link_to(text, url) for text, url in [
        ('Info', '/info'),
    ])
    return page(
        'Hello World!<br>{}'.format(content),
        title='Hello'
    )
