# -*- coding: utf-8 -*-

#   ____
#     /     _     _    _   _
#    /    /   \ /   \ | \_/ |
#   /___  \ _ / \ _ / |     |

"""
    Zoom Web Framework
"""

from .__version__ import __version__
__license__ = "MIT"

import zoom.alerts
import zoom.collect
import zoom.database
import zoom.jsonz
import zoom.queues
import zoom.records
import zoom.services
import zoom.settings
import zoom.store
import zoom.users

from .apps import App
from .auditing import audit
from .browse import browse
from .component import Component, DynamicComponent
from .context import context as system
from .forms import form, Form
from .helpers import link_to, url_for, url_for_page
from .instances import Instance
from .mvc import View, Controller, dispatch, DynamicView
from .page import page, Page
from .packages import requires
from .store import store_of
from .records import table_of
from .tools import home, redirect_to, load, partial
from .users import authorize, get_user
from .utils import Record
