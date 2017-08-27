"""
    basic index
"""

import zoom

import model

class MyView(zoom.mvc.View):

    def index(self):
        """Show registration page"""

        fields = self.model

        agreements = """
        By registering, I agree to the {{site_name}} <a
        href="/terms.html">Terms of Use</a> and <a href="/privacy.html">Privacy
        Policy</a>.
        """

        template = zoom.tools.load('registration.html')

        content = zoom.render.render(template).format(
            fill=dict(
                messages='',
                agreements=agreements,
                fields=fields.edit(),
            ),
        )

        return zoom.page(content, title='Register')


    def about(self):
        app = zoom.system.request.app
        content = '{app.description}'
        return zoom.page(
            content.format(app=app),
            title='About {app.title}'.format(app=app)
        )

class MyController(zoom.mvc.Controller):

    def register_now_button(self, **data):
        fields = self.model
        return zoom.page(zoom.tools.load_content('step2.txt'))


fields = model.get_fields()
view = MyView(fields)
controller = MyController(fields)
