

from zoom import __version__
from zoom.mvc import View
from zoom.page import page
from zoom.tools import load_content
from zoom.browse import browse
import zoom.fields as f
from zoom.validators import required

import widgets

my_form = f.Fields(
    f.Section('Personal', [
        f.TextField('Name', required, size=20, value='John Doe', hint='this is a hint'),
        f.MemoField('Notes', hint='this is a hint'),
        ]),
    f.Section('Social', [
        f.TextField('Twitter', size=15, value='jdoe', hint='optional'),
        ]),
    f.ButtonField('Save'),
    )

small_form = f.Fields(
    f.TextField("Name", size=20),
    f.TextField("Address"),
)

class MyView(View):
    """main application view"""

    def index(self):
        site = self.model
        db = site.db

        cmd = 'select id, username, email, phone from users limit 10'
        data = browse(db(cmd)) + \
            '<br>or in sortable form:' + browse(db(cmd), sortable=True)

        content = load_content(
            'sample.md',
            data=data,
            name='a name',
            form1=my_form.edit(),
            form2=my_form.show(),
            form3=small_form.edit(),
        )
        return page(content)

    def widgets(self):
        return widgets.view()

    def about(self):
        return load_content('about.md', version=__version__)


def main(route, request):
    view = MyView(request.site)
    return view(*route, **request.data)
