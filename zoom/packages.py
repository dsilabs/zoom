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
    'd3': {
        'libs': [
            'https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js',
        ],
    },
    'c3': {
        'libs': [
            'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.js'
            ],
        'styles': [
            'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.css',
        ],
        'requires': [
            'd3',
        ]
    },
    'cookieconsent': {
        'libs': [
            '/static/zoom/cookieconsent.js',
            '//cdn.jsdelivr.net/npm/cookieconsent@3/build/cookieconsent.min.js'
        ],
        'styles': [
            '//cdn.jsdelivr.net/npm/cookieconsent@3/build/cookieconsent.min.css'
        ]
    },
    'datatables': {
        'libs': [
            '//cdn.datatables.net/1.10.16/js/jquery.dataTables.min.js',
            ],
        'styles': [
            '//cdn.datatables.net/1.10.16/css/jquery.dataTables.min.css',
        ]
    },
    'datatables.buttons': {
        'libs': [
            '//cdn.datatables.net/buttons/1.5.1/js/dataTables.buttons.min.js',
            '//cdn.datatables.net/buttons/1.5.1/js/buttons.bootstrap.min.js',
            '//cdn.datatables.net/buttons/1.5.1/js/buttons.html5.min.js',
            '//cdn.datatables.net/buttons/1.5.1/js/buttons.jqueryui.min.js',
            '//cdn.datatables.net/buttons/1.5.1/js/buttons.print.min.js',
            ],
        'styles': [
            '//cdn.datatables.net/buttons/1.5.1/css/buttons.bootstrap.min.css',
            '//cdn.datatables.net/buttons/1.5.1/css/buttons.dataTables.min.css',
            '//cdn.datatables.net/buttons/1.5.1/css/buttons.jqueryui.min.css'
            ]
    },
    'dropzone': {
        'libs': [
            '//cdnjs.cloudflare.com/ajax/libs/dropzone/5.4.0/dropzone.js',
            '/static/zoom/dropzone.js'
        ],
        'styles': [
            '//cdnjs.cloudflare.com/ajax/libs/dropzone/5.4.0/dropzone.css'
        ]
    },
    'fontawesome4': {
        'styles': [
            '/static/zoom/fontawesome4/css/font-awesome.min.css'
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
    'images-field': {
        'libs': [
            '/static/zoom/images-field.js',
        ]
    },
    'jquery': {
        'libs': [
            '//code.jquery.com/jquery-3.3.1.min.js'
        ],
    },
    'jquery-ui': {
        'libs': [
            '//code.jquery.com/ui/1.12.1/jquery-ui.min.js'
        ],
        'styles': [
            '//code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css'
        ],
        'requires': [
            'jquery'
        ],
    },
    'spin': {
        'libs': [
            '//cdnjs.cloudflare.com/ajax/libs/spin.js/2.3.2/spin.min.js',
            '/static/zoom/spin.js',
        ]
    },
    "vue": {
        "libs":
            ["//cdn.jsdelivr.net/npm/vue/dist/vue.js"]
    },
    "bootstrap4": {
        "libs": [
            "/js/bootstrap.bundle.min.js"
        ],
        "styles": [
            "/css/bootstrap.min.css"
        ],
        "requires": [
            "jquery", "jquery-ui"
        ],
    },
    "standard-zoom-assets": {
        "styles":
            [
                "/css/content.css",
                "/css/navigation.css",
                "/css/containers.css",
                "/css/widget.css",
                "/css/print.css",
                "/css/style.css",
                "/css/social.css",
                "/css/buttons.css",
                "/css/components.css",
            ],
        "libs":
            [
                "/static/zoom/zoom.js",
            ]
    }
}


def load(pathname):
    """Load a packages file into a dict"""
    if os.path.isfile(pathname):
        with open(pathname, 'r', encoding='utf-8') as data:
            return json.load(data)
    return {}

def get_registered_packages():
    """Returns the list of packages known to the site

    >>> import zoom.request
    >>> zoom.system.request = zoom.request.Request(dict(PATH_INFO='/'))
    >>> zoom.system.site = zoom.site.Site(zoom.system.request)
    >>> zoom.system.request.app = zoom.utils.Bunch(packages={}, common_packages={})

    >>> packages = get_registered_packages()
    >>> 'c3' in packages
    True
    """
    registered = {}
    packages_list = [
        default_packages,
        zoom.system.site.packages,
        zoom.system.request.app.common_packages,
        zoom.system.request.app.packages,
    ]
    for packages in packages_list:
        registered.update(packages)
    return registered


def requires(*package_names):
    """Inform framework of the packages required for rendering

    >>> import zoom.request
    >>> request = zoom.request.Request(dict(PATH_INFO='/'))
    >>> zoom.system.site = zoom.site.Site(request)
    >>> zoom.system.parts = zoom.Component()

    >>> requires('c3')
    >>> libs = zoom.system.parts.parts['libs']
    >>> print('\\n'.join(list(libs)))
    https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js
    https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.js

    >>> zoom.system.parts = zoom.Component()
    >>> requires('jquery-ui')
    >>> libs = zoom.system.parts.parts['libs']
    >>> print('\\n'.join(list(libs)))
    //code.jquery.com/jquery-3.3.1.min.js
    //code.jquery.com/ui/1.12.1/jquery-ui.min.js

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
            requirements = package.get('requires')
            if requirements:
                requires(*requirements)
            parts += zoom.Component(**package)
        else:
            missing = set(package_names) - set(registered_packages)
            raise Exception('Missing required packages: {}'.format(missing))

    zoom.system.parts += parts
