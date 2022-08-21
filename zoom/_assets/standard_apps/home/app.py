"""
    home app

    the users home desktop
"""

import zoom
import zoom.html as h


def app(request):
    """Return a page containing a list of available apps"""

    zoom.requires('fontawesome4', 'bootstrap-icons')

    css = """
        .app-icons ul {
            list-style-type: none;
            margin-top: 50px;
        }
        .app-icons li {
            display: inline;
        }
        .zoom-app-as-icon {
            width: 110px;
            height: 120px;
            text-align: center;
            float: left;
        }
        .zoom-app-as-icon:hover {
            background: #eee;
        }
        .zoom-app-icon {
            height: 50px;
            width: 50px;
            border-radius: 5px;
            margin-top: 16px;
            padding-top: 5px;
            line-height: 50px;
            text-align: center;
            box-shadow: inset 0px 49px 0px -24px #67828b;
            background-color: #5a7179;
            border: 1px solid #ffffff;
            display: inline-block;
            color: #ffffff;
            font-size: 15px;
            text-decoration: none;
        }
        .zoom-app-icon .fa {
            font-size: 2em;
        }
        .zoom-app-icon .bi {
            font-size: 2rem;
            line-height: 2rem;
        }
    """

    if len(request.route) > 1 or request.data:
        return zoom.home()

    skip = 'home', 'logout', 'login', 'settings'
    content = h.div(
        h.ul(
            a.as_icon for a in sorted(request.site.apps, key=lambda a: a.title.lower())
            if a.name not in skip and a.visible and request.user.can_run(a)
        ), classed='app-icons'
    ) + '<div style="clear:both"></div>'
    return zoom.page(content, css=css)
