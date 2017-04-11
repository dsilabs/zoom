"""
    zoom.models

    common models
"""

from zoom.utils import DefaultRecord, id_for
from zoom.helpers import link_to, url_for_item


class Model(DefaultRecord):
    """Model Superclass

    Provide basic model properties and functions.

    Subclass this to create a Model that can be stored in
    a RecordStore, EntityStore or some other type of store.

    Assumes every record has an id attribute.  If not, you
    will need to provide one via an additional property
    defined in the subclass.

    The key can end up being just the str of the id, however
    it is provided separately to make it easy to provide human
    friendly keys typically used in REST style URLs.  If used
    this way the key should generated such that it is unique
    for each record.
    """

    @property
    def name(self):
        """Return the key"""
        return str(self.id)

    @property
    def key(self):
        """Return the key"""
        return id_for(self.name)

    @property
    def url(self):
        """Return a valid URL"""
        return url_for_item(self.key)

    @property
    def link(self):
        """Return a link"""
        return link_to(self.name, self.url)

    def allows(self, actor, action):
        return False
