# -*- coding: utf-8 -*-

#   ____
#     /     _     _    _   _
#    /    /   \ /   \ | \_/ |
#   /___  \ _ / \ _ / |     |

"""
    Zoom Web Framework
"""

__version__ = "6.0"
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
from .browse import browse
from .component import Component
from .context import context as system
from .forms import form, Form
from .helpers import link_to
from .instances import Instance
from .mvc import View, Controller, dispatch
from .page import page, Page
from .packages import requires
from .store import store_of
from .tools import home, redirect_to
from .users import authorize
from .utils import Record
