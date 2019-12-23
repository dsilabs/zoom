"""describe: Describe Zoom resources.

Usage:
    zoom describe [options] databases
    zoom describe [options] database <db_or_table>
    zoom describe [options] background [<path>]

Background options:
  -e, --events                Describe background events.
  -c, --count=<val>           When describing events, the number to display for
                              each job. Defaults to 10.

Options:
%s"""

import os

from docopt import docopt

from zoom.database import database
from zoom.sites import Site
from zoom.instances import Instance
from zoom.cli.common import DB_ACCESS_OPTIONS, DB_ENGINE_OPTION
from zoom.cli.utils import which_argument, describe_options, collect_options,\
    finish, resolve_path_with_context, is_site_dir, is_instance_dir

# The options used by all database-related description operations.
COMMAND_OPTIONS = (DB_ENGINE_OPTION, *DB_ACCESS_OPTIONS)

def describe():
    # Parse the provided arguments, resolving which command is running and
    # wizarding any missing options.
    arguments = docopt(doc=describe.__doc__)
    which = which_argument(arguments, ('databases', 'database', 'background'))
    
    def output(result):
        """Output a database query result with formatting."""
        print(str(result).join(('\n=======\n',)*2))

    # Connect to the database.
    collected = db = None
    if which.startswith('database'):
        collected = collect_options(arguments, COMMAND_OPTIONS)
        db = database(**collected)

    if which == 'databases':
        # Describe the set of databases.
        output(db('show databases;'))
    elif which == 'database':
        # Resolve whether an individual table is being referenced.
        db_name = arguments['<db_or_table>']
        table_name = None
        if '.' in db_name:
            db_name, table_name, *rest = db_name.split('.')
            if len(rest):
                finish(True, 'Error: invalid table reference "%s"'%(
                    arguments['<db_or_table>']
                ))
        
        # Switch to the requested database with safety.
        try:
            db('use %s;'%db_name)
        except:
            finish(True, 'Error: invalid database "%s"'%db_name)

        if table_name:
            # Describe an individual table.
            try:
                output(db('describe %s;'%table_name))
            except:
                finish(True, 'Error: invalid table "%s"'%table_name)
        else:
            # Describe the table set for this database.
            output(db('show tables;'))
    elif which == 'background':
        # Resolve the path to the site or instance target.
        target_path = os.path.join(resolve_path_with_context(
            arguments.get('<path>') or '.',
            site=True, instance=True
        ))

        count = None

        def list_site_jobs(site):
            """List background job functions for a site."""
            site.activate()
            for job in site.background_jobs:
                changed = job.has_changed_since_record()
                print('%s%s: %s'%(
                    job.qualified_name, ' [changed]' if changed else str(),
                    job.uow.__doc__
                ))

        def list_site_events(site):
            """List background job events for a site."""
            site.activate()
            for job in site.background_jobs:
                runtimes = job.get_runtimes()
                print('Job: %s'%job.qualified_name)
                for i, runtime in enumerate(runtimes):
                    if i >= count:
                        break
                    print('\t%s'%runtime.describe())

        # Decide which description function to use.
        is_events_query = arguments.get('--events')
        if is_events_query:
            count = arguments.get('--count') or 10
            try:
                count = int(count)
            except ValueError:
                finish(True, 'Error: invalid count')
        
        action_fn = list_site_events if is_events_query else list_site_jobs
        
        if is_site_dir(target_path):
            # Run on the given site only.
            action_fn(Site(target_path))
        elif is_instance_dir(target_path):
            # Run on each site in the instance.
            instance = Instance(target_path)
            for site in instance.get_sites(skip_fails=True).values():
                action_fn(site)
        else:
            finish(True, 'Error: "%s" is not a Zoom site or instance'%(
                target_path
            ))
    else:
        raise NotImplementedError()

    print('Described')
describe.__doc__ = __doc__%describe_options(COMMAND_OPTIONS)
