"""
    sample Alerts
"""

from random import choice

from zoom.mvc import View, Controller
from zoom.page import page
from zoom.tools import markdown, home, redirect_to
from zoom.components import success, warning, error


class MyView(View):

    def index(self):
        content = markdown("""
        Alerts
        ====
        * [Success](alerts/success)
        * [Warning](alerts/warning)
        * [Error](alerts/error)
        * [Random](alerts/random)

        Developer
        ====
        * [Stdout](alerts/stdout)
        """)
        return page(content)


class MyController(Controller):

    def success(self):
        success('that was great!')
        return page(markdown('return to [index](/sample/alerts)'), title='Alerts')

    def warning(self):
        warning('that was close!')
        return redirect_to('/sample/alerts')

    def error(self):
        error('that was bad!')
        return redirect_to('/sample/alerts')

    def stdout(self):
        print('Here is some stdout output!')
        msg = """
        stdout output
        <br><br>
        <a href="<dz:parent_path>">Go Back</a>
        """
        return page(msg, title='Stdout')

    def random(self):
        for n in range(5):
            choice([
                lambda: success('Success %s' % n),
                lambda: warning('Warning %s' % n),
                lambda: error('Error %s' % n),
            ])()
        return redirect_to('/sample/alerts')


def main(route, request):
    view = MyView(request)
    controller = MyController(request)
    return controller(*route, **request.data) or view(*route, **request.data)
