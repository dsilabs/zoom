# -*- coding: utf-8 -*-

"""
    sample Fields

    sample page showing the field types that are available in Zoom
"""

import datetime
from decimal import Decimal

from zoom.fields import *  # pylint: disable W0401
from zoom.forms import Form
from zoom.helpers import url_for_page
from zoom.mvc import View, Controller
from zoom.page import page
from zoom.response import PNGResponse, GIFResponse, JPGResponse

# from zoom import *
# from zoom.buckets import Bucket
# from zoom.response import *
# from zoom.collect import *

date1 = datetime.date(2015, 1, 1)
date2 = datetime.date(2016, 12, 31)

form1 = Form(
    TextField('Name', addon='$', hint='test hint'),
    TextField('Nickname', placeholder='Jack', hint='test hint'),
    EmailField('Email', hint='test hint'),
    PhoneField('Phone', hint='phone number'),
    PostalCodeField('Postal Code', hint='test hint'),
    # ImagesField(
    #     'Photos',
    #     url='/{}/fields/'.format(system.app.name),
    #     hint='click or drag and drop to upload'
    #     ),
    TwitterField('Twitter', hint='test hint'),
    URLField('Web', hint='test hint'),
    PasswordField('Password', hint='test hint'),
    # NumberField('Number of Things', hint='test hint'),
    # NumberField('Area', units='ft<sup>2</sup>', hint='test hint'),
    # IntegerField('Count', hint='test hint'),
    # FloatField('Size', units='meters', hint='test hint'),
    # DecimalField('Decimal', hint='test hint'),
    # MoneyField('Amount', hint='test hint'),
    # MoneyField('Placeholder', placeholder=100, hint='test hint'),
    # MoneyField('Foreign Amount', symbol='£', hint='test hint'),
    # DateField('Date', hint='test hint'),
    # DateField('Min Max Date', min=date1, max=date2, hint='test hint'),
    # DateField('Formatted Date', format='%Y-%m-%d (%A)', hint='test hint'),
    # BirthdateField('Birth Date', hint='test hint'),
    # CheckboxesField(
    #     'Select', values=['One', 'Two', 'Three'], hint='test hint'),
    # CheckboxField('Publish', hint='test hint'),
    # RadioField('Radio', values=['One', 'Two', 'Three'], hint='test hint'),
    # PulldownField(
    #     'Pulldown', options=['One', 'Two', 'Three'], hint='test hint'),
    # ChosenSelectField(
    #     'Chosen Select', options=['One', 'Two', 'Three'], hint='test hint'),
    # MultiselectField(
    #     'Multiselect', options=['One', 'Two', 'Three'], hint='test hint'),
    # ChosenMultiselectField(
    #     'Sizes', options=['One', 'Two', 'Three', 'Four'],
    #     hint='test hint', placeholder='Choose as you wish'),
    # RangeSliderField('Price', min=0, max=1500),
    # ButtonField('Okay!', hint='test hint'),
    # MemoField('Memo', hint='test hint'),
    # MarkdownField('Markdown', hint='test hint'),
    # EditField('Editor', hint='test hint'),
    ButtonField('Save', cancel=url_for_page('fields'))
    )

sample = dict(
    name='Joey',
    email='joey@dsilabs.ca',
    postal_code='V8X 2P2',
    phone='2341231234',
    twitter='dsilabs',
    web='https://www.dsilabs.ca',
    password='mypass',
    number_of_things=123,
    count=456,
    size=1.2345,
    decimal=Decimal('1234132.234'),
    amount=Decimal('12341232.32432'),
    foreign_amount=Decimal('121232.432'),
    date=datetime.date(2015, 4, 2),
    min_max_date=datetime.date(2015, 4, 2),
    formatted_date=datetime.date(2015, 4, 2),
    birth_date=datetime.date(2073, 2, 18),
    select='One',
    publish=False,
    radio='One',
    pulldown='Two',
    multiselect=['One', 'Three'],
    chosen=['One', 'Two'],
    memo='memo content',
    markdown='Heading\n====\nmarkdown content',
    editor='editor content',
    )


def menu_item(name):
    return (name, url_for_page('fields', name.lower()))


actions = [
    menu_item('Show'),
    menu_item('Edit'),
    menu_item('New'),
    ]


js = """
"""


def image_response(name, data):
    _, ext = os.path.splitext(name.lower())
    if ext == '.png':
        return PNGResponse(data)
    elif ext == '.jpg':
        return JPGResponse(data)
    elif ext == '.gif':
        return GIFResponse(data)


class MyView(View):

    def index(self, q=""):
        form1.initialize(sample)
        content = form1.show()
        return page(content, actions=actions, title='Fields Demo')

    def show(self, key=None):
        form1.initialize(sample)
        content = form1.show()
        return page(content, actions=actions, title='Show Mode')

    def edit(self, key=None, *a, **k):
        site = self.model.site
        # path = os.path.join(site.data_path, 'buckets')
        # bucket = Bucket(path)
        form1.update(sample)
        form1.update(k)
        content = form1.edit()
        return page(content, actions=actions, title='Edit Mode')

    def new(self):
        # site = self.model.site
        form1.initialize({})
        content = form1.edit()
        return page(content, actions=actions, title='Edit Mode')

    # def list_images(self, key='test', value='test'):
    #     """return list of images for an ImagesField value for this record"""
    #     attachments = store(Attachment)
    #     path = os.path.join(system.site.data_path, 'buckets')
    #     bucket = Bucket(path)
    #     t = [dict(
    #         name=a.attachment_name,
    #         size=a.attachment_size,
    #         item_id=a.attachment_id,
    #         url=url_for('get_image', item_id=a.attachment_id),
    #         ) for a in attachments.find(field_value=value)]
    #     return json.dumps(t)
    # 
    # def get_image(self, *a, **k):
    #     """return one of the images from an ImagesField value"""
    #     item_id = k.get('item_id', None)
    #     path = os.path.join(system.site.data_path, 'buckets')
    #     bucket = Bucket(path)
    #     return image_response('house.png', bucket.get(item_id))
    # 

class MyController(Controller):

    def save_button(self, *a, **k):
        if form1.validate(k):
            return page('saved', title='Result')

    # def add_image(self, *a, **k):
    #     """add a ImagesField image"""
    #     path = os.path.join(system.site.data_path, 'buckets')
    #     bucket = Bucket(path)
    #     f = k.get('file')
    #     name = f.filename
    #     data = f.file.read()
    #     item_id = bucket.put(data)
    #     return item_id
    # 
    # def remove_image(self, *a, **k):
    #     """remove a ImagesField image"""
    #     path = os.path.join(system.site.data_path, 'buckets')
    #     bucket = Bucket(path)
    #     items = bucket.keys()
    #     item_id = k.get('id', None)
    #     if item_id in bucket.keys():
    #         bucket.delete(item_id)
    #         return 'ok'
    #     return 'empty'


def main(route, request):
    view = MyView(request)
    controller = MyController(request)
    return controller(*route, **request.data) or view(*route, **request.data)
