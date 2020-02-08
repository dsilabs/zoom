"""
    test_settings.py

    Test the settings module.
"""

import unittest

import zoom

class MyTestSettingsController(zoom.settings.SettingsController):

    def get_fields(self):
        return zoom.fields.Fields(
            zoom.fields.TextField('Field One', zoom.validators.required),
            zoom.fields.TextField('Field Two'),
        )

class TestAudit(unittest.TestCase):

    def setUp(self):
        bunch = zoom.utils.Bunch
        # db = zoom.database.setup_test()
        zoom.system.site = zoom.sites.Site()
        zoom.system.request = bunch(
            app=bunch(name='myapp', url='/myapp'),
            user=zoom.system.site.users.first(username='user')
        )
        zoom.system.parts = zoom.Component()


    def test_settings_store(self):
        settings = zoom.settings.Settings()
        self.assertEqual(settings.item1, None)
        settings.item1 = 'test'
        settings.save(dict(item1='some_value'))

        settings2 = zoom.settings.Settings()
        self.assertEqual(settings2.item1, 'some_value')

    def test_settings_user_specific(self):
        settings = zoom.settings.Settings()
        settings.clear()
        self.assertEqual(settings.item1, None)
        settings.item1 = 'test'
        settings.save(dict(item1='some_value'))

        admin = zoom.system.site.users.first(username='admin')
        zoom.system.request.user = admin
        settings2 = zoom.settings.Settings()
        self.assertEqual(settings2.item1, None)

        user = zoom.system.site.users.first(username='user')
        zoom.system.request.user = user
        settings2 = zoom.settings.Settings()
        self.assertEqual(settings2.item1, 'some_value')

    def test_site_settings_missing(self):
        settings = zoom.system.site.settings
        settings.clear()
        self.assertEqual(settings.site.not_a_setting, None)

    def test_site_settings_missing_after_save(self):
        settings = zoom.system.site.settings
        settings.clear()
        settings.save()
        self.assertEqual(settings.site.not_a_setting, None)

    def test_site_settings_blank(self):
        settings = zoom.system.site.settings
        settings.clear()
        settings.settings.put(dict(value=''))
        self.assertEqual(settings.site.not_a_setting, None)

    def test_settings_controller_index(self):
        settings = zoom.settings.Settings()
        values = dict(field_one='value1', field_two='value2')
        settings.save(values)

        controller = MyTestSettingsController()
        response = controller.index()
        assert 'value1' in response.content
        assert 'value2' in response.content

    def test_settings_controller_save(self):
        settings = zoom.settings.Settings()
        values = dict(field_one='value1', field_two='value2')
        settings.save(values)

        new_values = dict(
            field_one='value3',
            field_two='value4'
        )
        controller = MyTestSettingsController()
        controller.save_button(**new_values)

        response = controller.index()
        assert 'value3' in response.content
        assert 'value4' in response.content

    def test_settings_controller_clear(self):
        settings = zoom.settings.Settings()
        values = dict(field_one='value1', field_two='value2')
        settings.save(values)

        new_values = dict(
            field_one='value3',
            field_two='value4'
        )
        controller = MyTestSettingsController()
        controller.save_button(**new_values)

        response = controller.index()
        assert 'value3' in response.content
        assert 'value4' in response.content

        controller.clear()
        settings2 = zoom.settings.Settings()
        settings2.load()
        self.assertEqual(settings2.values, {})
