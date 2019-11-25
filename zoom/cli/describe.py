"""describe: Describe Zoom resources.

Usage:
    zoom describe [options] databases
    zoom describe [options] database <db_or_table>
    
Options:
%s"""

from docopt import docopt

from zoom.database import database
from zoom.cli.common import DB_ACCESS_OPTIONS, DB_ENGINE_OPTION
from zoom.cli.utils import which_argument, describe_options, collect_options,\
    finish

# The options used by all database-related description operations.
COMMAND_OPTIONS = (DB_ENGINE_OPTION, *DB_ACCESS_OPTIONS)

def describe():
    # Parse the provided arguments, resolving which command is running and
    # wizarding any missing options.
    arguments = docopt(doc=describe.__doc__)
    which = which_argument(arguments, ('databases', 'database'))
    collected = collect_options(arguments, COMMAND_OPTIONS)

    def output(result):
        """Output a database query result with formatting."""
        print(str(result).join(('\n=======\n',)*2))

    # Connect to the database.
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
    else:
        raise NotImplementedError()

    print('Described')
describe.__doc__ = __doc__%describe_options(COMMAND_OPTIONS)
