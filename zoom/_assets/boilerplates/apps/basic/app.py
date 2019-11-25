"""This file tells Zoom about our app (for example what menus it has)."""

import zoom

app = zoom.App()
app.menu = ('About', 'Overview')
