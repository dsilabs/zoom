# -*- coding: utf-8 -*-

"""
    zoom CLI

    Zoom command line utility.
"""

# pylint: disable=unused-argument

import logging
import os
import sys
from argparse import ArgumentParser

from zoom.cli.setup import setup
from database import database
from zoom.cli.new import new
from zoom.cli.server import server

__all__ = [
    'server',
    'database',
    'new',
    'setup',
]

