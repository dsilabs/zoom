"""
    zoom.packages

    Provide a simple shorthand way to include external components in projects.
"""

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


def get_registered_packages():
    """Returns the list of packages known to the site"""
    return default_packages


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
