"""
    snippet collection
"""

import zoom.collect
import zoom.fields as f
from zoom.validators import required


def snippet_fields():
    """Return snippet fields"""
    return f.Fields(
            f.TextField('Name', required, maxlength=80),
            f.EditField('Body', required),
    )

main = zoom.collect.Collection(
    snippet_fields,
    model=zoom.snippets.SystemSnippet,
    columns=('link', 'body', 'impressions')
)
