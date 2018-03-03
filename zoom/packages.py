"""
    zoom.packages

    Provide a simple shorthand way to include external components in projects.
"""

import json
import os

import zoom


default_packages = {
    'bootstrap3': {
        'libs': [
            '//maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js',
        ],
        'styles': [
            '//maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
        ]
    },
    'c3': {
        'libs': [
            'https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.js'
            ],
        'styles': [
            'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.css',
        ]
    },
    'fontawesome4': {
        'styles': [
            '//maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css'
        ]
    },
    'fontawesome': {
        'styles': [
            '//use.fontawesome.com/releases/v5.0.6/css/all.css'
        ]
    },
    'fontawesome-svg': {
        'libs': [
            '//use.fontawesome.com/releases/v5.0.6/js/all.js'
        ]
    },
}


def load(pathname):
    """Load a packages file into a dict"""
    if os.path.isfile(pathname):
        with open(pathname, 'r', encoding='utf-8') as data:
            return json.load(data)
    return {}


def get_registered_packages():
    """Returns the list of packages known to the site

    >>> request = zoom.request.Request(dict(PATH_INFO='/'))
    >>> zoom.system.site = zoom.site.Site(request)

    >>> packages = get_registered_packages()
    >>> 'c3' in packages
    True
    """
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
    """Inform framework of the packages required for rendering

    >>> request = zoom.request.Request(dict(PATH_INFO='/'))
    >>> zoom.system.site = zoom.site.Site(request)

    >>> requires('c3')
    >>> libs = zoom.component.composition.parts.parts['libs']
    >>> list(libs)[0]
    'https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js'

    >>> try:
    ...     requires('d4')
    ... except Exception as e:
    ...     'Missing required' in str(e) and 'raised!'
    'raised!'

    """

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
