
import zoom
from zoom.html import ul
from zoom.page import page
from zoom.helpers import link_to

def app(request):

    zoom.requires('Morphext')

    content = ul(link_to(text, url) for text, url in [
        ('Info', '/info'),
    ])

    js = """
    $("#js-rotating").Morphext({
        animation: "bounceIn",
        separator: ",",
        speed: 2000,
    });
    """

    return page(
        '<span id="js-rotating">Hello, Howdy, Hola, Hi</span> World!<br>{}'.format(content),
        title='Hello',
        js=js,
    )
