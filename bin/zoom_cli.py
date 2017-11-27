"""
    Zoom CLI
"""

import sys
from os.path import abspath, split, join
import finder

required = ['tools/zoom', '']
root = abspath(join(split(finder.__file__)[0], '..'))

for directory in required:
    path = join(root, directory)
    if path not in sys.path:
        sys.path.insert(0, path)

from main import main
