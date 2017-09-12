"""
    templates.zoom
"""

from zoom.page import page


def app_not_found(request):
    # pylint: disable=unused-argument
    return """
    <h1>System Message</h1>
    <p>This site is currently under construction.</p>
    """


page_not_found = """
    <div class="jumbotron">
        <h1>Page Not Found</h1>
        <p>The page you requested could not be found.
        Please contact the administrator or try again.<p>
    </div>
    """

site_not_found = """
    <body>
    <div class="jumbotron">
        <h1>Site Not Found</h1>
        <p>{request.domain} does not exist.
        Please contact the system administrator or try again.<p>
    </div>
    </body>
    """
