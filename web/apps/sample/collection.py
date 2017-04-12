"""
    simple collection example
"""

import zoom.collect
import zoom.models
from zoom.fields import (Fields, TextField, DateField, RadioField, EditField)
from zoom.validators import required, MinimumLength


statuses = [
    ('New', 'N'),
    ('Open', 'O'),
    ('Pending', 'P'),
    ('Closed', 'C'),
]


def contact_fields():
    """Return contact fields"""
    return Fields(
        TextField('Name', required, maxlength=80),
        TextField('Title', required, MinimumLength(3)),
        DateField('Date', format='%A %b %d, %Y'),
        RadioField('Status', values=statuses),
        EditField('Notes'),
    )


main = zoom.collect.Collection(contact_fields)
