

from zoom.mvc import View
from zoom.page import page
from zoom.tools import load_content
from zoom.browse import browse
from zoom.fields import *
from zoom.validators import required

import widgets

my_form = Fields(
    Section('Personal', [
        TextField('Name', required, size=20, value='John Doe', hint='this is a hint'),
        MemoField('Notes', hint='this is a hint'),
        ]),
    Section('Social', [
        TextField('Twitter', size=15, value='jdoe', hint='optional'),
        ]),
    ButtonField('Save'),
    )

small_form = Fields(
    TextField("Name", size=20),
    TextField("Address"),
)

class MyView(View):
    """main application view"""

    def index(self):
        site = self.model
        db = site.db

        cmd = 'select id, username, email, phone from users limit 10'
        data = browse(db(cmd)) + '<br>or in sortable form:' + browse(db(cmd), sortable=True)

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
        return load_content('about.md', version=zoom.__version__)


def main(route, request):
    view = MyView(request.site)
    return view(*route, **request.data)
