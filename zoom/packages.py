"""
    zoom.packages

    Provide a simple shorthand way to include external components in projects.
"""

import json
import os

import zoom


default_packages = {
    'c3': {
        'libs': [
            'https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.js'
            ],
        'styles': [
            'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.css',
        ]
    }
}


def load(pathname):
    """Load a packages file into a dict"""
    isfile = os.path.isfile
    if isfile(pathname):
        with open(pathname, 'r', encoding='utf-8') as data:
            return json.load(data)
    return {}


def get_registered_packages():
    """Returns the list of packages known to the site"""
    registered = {}
    packages_list = [
        default_packages,
        zoom.system.site.packages,
        # app_packages,
    ]
    for packages in packages_list:
        registered.update(packages)
    return registered


def requires(*package_names):
    """Inform framework of the packages required for rendering"""

    parts = zoom.Component()

    registered_packages = get_registered_packages()

    for name in package_names:
        package = registered_packages.get(name)
        if package:
            parts += zoom.Component(**package)
        else:
            missing = set(package_names) - set(registered_packages)
            raise Exception('Missing required packages: {}'.format(missing))

    zoom.component.composition.parts += parts
