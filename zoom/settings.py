"""
    zoom.settings

    Classes for mananging settings.
"""

import zoom
from zoom.page import page

class AppSettings(zoom.store.Entity):
    """settings storage class"""
    pass


class Settings(object):
    """Settings storage class"""

    def __init__(self):
        self.settings = zoom.store_of(AppSettings)
        app = zoom.system.request.app
        user = zoom.system.request.user
        self.key = dict(
            app=app.name,
            user_id=user.user_id
        )
        self.values = None

    def save(self, value):
        """put the stash value"""
        rec = self.settings.first(**self.key) or AppSettings(**self.key)
        rec.update(dict(value=zoom.jsonz.dumps(value)))
        self.settings.put(rec)

    def load(self):
        """get the stash value"""
        rec = self.settings.first(**self.key)
        if rec:
            self.values = zoom.jsonz.loads(rec.value)
        else:
            self.values = {}
        return self.values

    def clear(self):
        """Clear all settings"""
        self.settings.delete(**self.key)

    def __getattr__(self, name):
        if self.values is None:
            self.load()
        return self.values.get(name)


class SettingsController(zoom.mvc.Controller):
    """settings controller"""

    form = None

    def __init__(self):
        zoom.Controller.__init__(self)
        self.settings = Settings()
        self.form = self.get_form()

    def get_form(self):
        """Get the settings form

        Override this method to provide a settings form specific to your app.
        """
        app = zoom.system.request.app
        fields = self.get_fields()
        return zoom.forms.Form(
            fields,
            zoom.fields.ButtonField('Save', cancel=app.url)
        )

    def get_fields(self):
        """Get the settings fields

        Override this method to provide settings fields specific to your app.
        """
        pass

    def index(self, **kwargs):
        """show the settings form"""
        values = self.settings.load()
        values.update(kwargs)
        self.form.initialize(values)
        content = self.form.edit()
        return page(content, title='Settings')

    def save_button(self, **values):
        """save settings"""
        if self.form.validate(values):
            self.settings.save(values)
            zoom.alerts.success('settings saved')

    def clear(self):
        """clear settings"""
        self.settings.clear()
        zoom.alerts.success('settings cleared')
        return zoom.home('settings')
