# -*- coding: utf-8 -*-

#   ____                      ____
#     /     _     _    _   _  |__    _          _     __   __
#    /    /   \ /   \ | \_/ | |    /   \ |   | | \ | |  \ |__| \___/
#   /___  \ _ / \ _ / |     | |    \ _ / |___| |  \| |__/ |  \   |
#

"""
    ZoomFoundry Web Framework
"""

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

from .__version__ import __version__
from .apps import App, get_app
from .auditing import audit
from .browse import browse
from .collect import collection_of
from .component import Component, DynamicComponent
from .context import context as system
from .forms import form, Form
from .helpers import link_to, url_for, url_for_page, link_to_page
from .instances import Instance
from .mvc import View, Controller, dispatch, DynamicView
from .page import page, Page
from .packages import requires
from .store import store_of
from .records import table_of
from .sites import get_site, get_db, db
from .tools import home, redirect_to, load, partial
from .users import authorize, can, get_user, locate_user
from .utils import Record

__license__ = "MIT"
