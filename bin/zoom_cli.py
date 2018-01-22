"""
    Zoom CLI
"""

import sys
from os.path import dirname, join

required = ['tools/zoom', '']
root = dirname(dirname(__file__))

for directory in required:
    path = join(root, directory)
    if path not in sys.path:
        sys.path.insert(0, path)

# pylint: disable=C0413,W0611
from main import main
