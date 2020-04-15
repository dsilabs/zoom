"""
    common testing functions
"""

import os

def get_output_path():
    """Return the location of the test output artifacts"""
    default_path = os.path.join('tests', 'artifacts')
    path = os.environ.get('ZOOM_TEST_ARTIFACTS_PATH', default_path)
    return path
