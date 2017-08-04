"""
    zoom.packages

    Provide a simple shorthand way to include external components in projects.
"""

import zoom


default_packages = {
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
            missing = set(package_names) - registered_packages
            raise Exception('Missing required packages: {}'.format(missing))

    zoom.component.composition.parts += parts
