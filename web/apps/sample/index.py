

from zoom.mvc import View
from zoom.page import page
from zoom.tools import load_content
from zoom.browse import browse
from zoom.fields import *
from zoom.validators import required

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
        data = browse(db(cmd))

        content = load_content(
            'sample.md',
            data=data,
            name='a name',
            form1=my_form.edit(),
            form2=my_form.show(),
            form3=small_form.edit(),
        )
        return page(content)


def main(route, request):
    view = MyView(request.site)
    return view(*route, **request.data)
