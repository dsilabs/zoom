"""
    zoom.settings

    Classes for mananging settings.
"""

import zoom
from zoom.page import page


class AppSettings(zoom.store.Entity):
    """settings storage class"""
    pass



class SystemSettings(zoom.store.Entity):
    """site settings"""
    pass


class SettingsSection(zoom.utils.Record):
    """settings section"""
    pass


class SiteSettings(object):
    """Site Settings"""

    def __init__(self, config):
        self.kind = SystemSettings
        self.settings = zoom.store_of(self.kind)
        self._values = None
        self.config = config

    def load(self):
        """load the settings values"""
        rec = self.settings.first()
        self._values = zoom.jsonz.loads(rec.value) if rec else {}
        return self._values

    @property
    def values(self):
        if self._values is None:
            self.load()
        return self._values

    def save(self):
        """save the settings values"""
        rec = self.settings.first() or self.kind()
        rec.update(dict(value=zoom.jsonz.dumps(self.values)))
        self.settings.put(rec)

    def clear(self):
        """Clear all settings"""
        self._values = None
        self.settings.zap()

    def items(self, section):
        items = dict(self.config.items(section))
        items.update(self.values.get(section, {}))
        return items

    def get(self, section, name, default=None):
        return self.values.get(section, {}).get(name, self.config.get(name))

    def section(self, name):
        return SettingsSection(self.items(name))

    def __getattr__(self, name):
        return self.section(name)

    def update(self, section, values):
        self._values.setdefault(section, {}).update(values)


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
