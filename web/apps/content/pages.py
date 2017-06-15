"""
    page collection
"""

import zoom.collect
from zoom.fields import (Fields, TextField, DateField, RadioField, EditField)
from zoom.validators import required, MinimumLength


statuses = [
    ('New', 'N'),
    ('Open', 'O'),
    ('Pending', 'P'),
    ('Closed', 'C'),
]


def page_fields():
    """Return page fields"""
    return Fields(
        TextField('Name', required, maxlength=80),
        # TextField('Title', required, MinimumLength(3)),
        # DateField('Date', format='%A %b %d, %Y'),
        # RadioField('Status', values=statuses),
        EditField('Body'),
    )


main = zoom.collect.Collection(page_fields)
