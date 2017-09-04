"""
    basic index
"""

import zoom


import model


class MyView(zoom.mvc.View):
    """Index View"""

    def index(self, *args, **kwargs):
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

    @zoom.authorize('administrators')
    def list(self):
        if zoom.system.request.user.is_admin:
            labels = (
                'First Name',
                'Last Name',
                'Username',
                'Token',
                'Expires',
                'Action',
            )
            content = zoom.browse(model.get_registrations(), labels=labels)
            return zoom.page(content, title='Registrations')

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
        if fields.validate(data):
            values = fields.evaluate()
            if values['password'] == values['confirm']:
                if model.submit_registration(values):
                    template = zoom.tools.load('step2.html')
                    content = zoom.render.render(template).format(
                        fill=dict(
                            messages='',
                        ),
                    )
                    return zoom.page(content)
            else:
                zoom.alerts.error('Passwords do not match')

    def confirm(self, token):
        """Registration confirmation"""
        result = model.confirm_registration(token)
        if zoom.system.request.user.is_admin:
            return zoom.home('list')
        return result


    @zoom.authorize('administrators')
    def delete(self, token):
        model.delete_registration(token)
        return zoom.home()


fields = model.get_fields()
view = MyView(fields)
controller = MyController(fields)
