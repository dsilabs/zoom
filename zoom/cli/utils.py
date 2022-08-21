"""CLI utilities. Differs from common logic in that these are operation-
agnostic helpers."""

import os
import sys
import shutil

from getpass import getpass

from zoom.tools import zoompath

# The path relative to the Zoom parent directory which boilerplate assets are
# packaged.
BOILERPLATE_DIR = 'zoom/_assets/boilerplates'

# Runtime helpers.
def finish(failure=False, *messages):
    """Finish a CLI invocation by outputting the given messages, optionally
    as an error."""
    for message in messages:
        print(message, file=sys.stderr if failure else sys.stdout)
    sys.exit(1 if failure else 0)

# Argument parsing helpers.
def which_argument(arguments, options):
    """Return which of the given constant options was specified in the given
    argument source parsed by docopt."""
    for check in options:
        if arguments[check]:
            return check

def legacy_command_argv(command):
    """Return the argument vector to be used by the ArgumentParser for the
    command with the given name. Used for legacy argument parsing system
    compatability."""
    return sys.argv[sys.argv.index(command) + 1:]

# Filesystem helpers.
def directories_exist(root, dirs):
    """Return whether each of the given directories exist relative to the given
    root path."""
    for dirname in dirs:
        if not os.path.isdir(os.path.join(root, dirname)):
            return False
    return True

def files_exist(root, files):
    """Return whether each of the given files exist relative to the given root
    path."""
    for filename in files:
        if not os.path.isfile(os.path.join(root, filename)):
            return False
    return True

def is_instance_dir(path):
    """Return whether the given path heuristically appears to be a Zoom
    instance directory."""
    return os.path.isdir(os.path.join(path, 'sites'))

def is_site_dir(path):
    """Return whether the given path heuristically appears to be a Zoom site
    directory."""
    return files_exist(path, ('site.ini',))

def copy_boilerplate(src_boilerplate, dest_path):
    """Copy the boilerplate contained in the given source directory to the
    given destination. The destination must be known to be an existing
    directory."""
    src_path = zoompath(BOILERPLATE_DIR, src_boilerplate)
    if not os.path.isdir(src_path):
        raise ValueError(src_boilerplate)

    # Copy each file and directory to the destination.
    for filename in os.listdir(src_path):
        filepath = os.path.join(src_path, filename)
        dest_filepath = os.path.join(dest_path, filename)
        if os.path.isdir(filepath):
            shutil.copytree(filepath, dest_filepath)
        else:
            shutil.copy(filepath, dest_filepath)

def resolve_path_with_context(path, path_ext=str(), instance=False, site=False):
    """Resolve the path and path extension based on parent directory context.
    If a context directory of one of the given types specified in kwargs isn't
    found, return only the path. If one is found, return it with the given path
    extension.

    Usage example: when creating a new site, if the destination path is an
    instance directory, create it in dest/sites instead. Also used to rely on
    CWD to determine sites/instances commands are supposed to be operating
    on."""
    dir_path = os.path.abspath(path)
    while True:
        # If the current directory is one of the types specified in kwargs,
        # return it...
        if (instance and is_instance_dir(dir_path)) \
                or (site and is_site_dir(dir_path)):
            return os.path.join(dir_path, path_ext)

        # ...otherwise move to the parent directory.
        next_dir_path = os.path.dirname(dir_path)
        if dir_path == next_dir_path:
            # We reached the filesystem root.
            break
        dir_path = next_dir_path

    # If we reach the filesystem root, there were no matches and the provided
    # path has no context (is the literal path).
    return path

# Options system helpers.
def describe_options(options):
    """Return a docopt-canonical description of the given options table. The
    returned result in indented to column 31 and has a line-length limit of
    80."""

    # Set up helpers.
    def is_boolean_flag(option):
        """Whether the given option tuple is a boolean flag (or a value
        key)."""
        return len(option) > 3 and (option[3] is False or option[3] is True)

    def format_description(description):
        """Format the given description string such that it is in sentence
        form and respects the line-length limit."""
        line_start =  ' '*30
        description = description[0].upper() + description[1:]

        lines = list((line_start,))
        for word in description.split(' '):
            line = lines[-1]
            if len(line + ' ' + word) > 80:
                lines.append(line_start + word)
            else:
                lines[-1] = line + ' ' + word

        return ('\n'.join(lines)).strip()

    # Transform options into string represenations and return the full set.
    return '\n'.join(('  -%s, --%s%s%s%s.'%(
        option[0], option[1], str() if is_boolean_flag(option) else '=<val>',
        ' '*(
            17 + (6 if is_boolean_flag(option) else 0) -
            (len(option[0]) + len(option[1]))
        ),
        format_description(option[2])
    )) for option in options)

def wizard_value_getter(argument_source):
    """Return a callable that can be used to retrieve values from either the
    given argument source parsed by docopt, or a command line wizard
    (prompt)."""
    # XXX: This could be encorperated into collect_options, but it's left here
    #      to allow future usage in other contexts.

    # Create and return the callable.
    def get_value(key, description, default=None, password=False):
        """Retrieve a value as described above."""
        # Prefer CLI options...
        option_value = argument_source.get('--%s'%key)
        if option_value:
            return option_value

        # ...then defaults...
        if default is not None:
            return default

        # ...finally, prompt for input appropriately.
        prompt = '%s (%s): '%(key, description)
        if password:
            return getpass(prompt)
        return input(prompt)
    return get_value

def collect_options(argument_source, options):
    """Collect the set of options tuples, prefering the given argument source
    and falling back to a provided wizard. If the default value (4th element)
    of an option starts with a "->", it references the resolved value of a
    previous option. Returns a dict."""
    # Create the value retriever.
    get_value = wizard_value_getter(argument_source)

    # Iterate each option, resolving their values.
    collected = dict()
    for option in options:
        # Comprehend the option tuple.
        shorthand, key, description, *rest = option
        default_value = rest[0] if rest else None

        # Handle default values that copy previous option values.
        if default_value and default_value.startswith('->'):
            default_value = collected[default_value[2:]]

        # Retrieve and store the collected value.
        collected[key] = get_value(
            key, description, default=default_value,
            password='password' in key
        )
    return collected
