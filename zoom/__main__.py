"""
Entry point for package-level command-line invocation. 

Note that since there are namespace conflicts between modules in this package
and its dependencies, we need to initialize a few modules before adding the 
package directory to the import search path. Since these modules are used by 
existing usage code, we aren't able to simply rename them. Note that absolute
references to these conflicting symbols within Zoom always refer to the
associated external library.
"""

import os
import sys

# Search for and remove this packages directory within sys.path. This ensures
# that the following imports will be resolved from site-packages instead of
# here.
_package_path = os.path.abspath(os.path.dirname(__file__))
for path in list(sys.path):
    if os.path.abspath(path) == _package_path:
        sys.path.remove(path)

# Import the libraries with a namespace conflict.
import logging
import html

# Re-insert this package path into sys.path. Since conflicting symbols have
# already been resolved to the external libraries, everything will work
# properly now.
sys.path.insert(0, os.path.abspath('.'))

from zoom.cli.main import main

# Run the CLI.
if __name__ == '__main__':
    main()
