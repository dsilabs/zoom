Zoom CLI
========

Use the Zoom command line utility to set up a new Zoom instance, set up a Zoom http server, manage the database, and create a new Zoom app.

To see a list of available options for each command run ``zoom <command> -h``


zoom database
-------------
| usage: manage the database
| required: database name and command

| eg: ``zoom database -e mysql -u root -p $MYSQL_ROOT_PASSWORD create zoomdata``

| commands:
- create
- list
- show
- setup

| optional arguments:

-   -help, - -help

        - show this help message and exit

-   -e ENGINE, - -engine ENGINE

        - database engine (sqlite3 or mysql)
        - defaults to 'sqlite3'

-   -H HOST, - -host HOST

        - database host
        - defaults to 'localhost'

-   -d DATABASE, - -database DATABASE

        - database name
        - defaults to zoomdata

-   -P PORT, - -port PORT

        - database service port
        - defaults to '3306'

-   -u [USER], - -user [USER]

        - database username
        - defaults to 'zoomuser'


-   -p [PASSWORD], - -password [PASSWORD]

        - database password
        - defaults to 'zoompass'


-   -v, - -verbose

        - verbose console logging


-   -f, - -force

        - force database creation (drop existing)

zoom server
-----------
| usage: run a built-in zoom http server
| required: specify port and root directory

- zoom server - [options]
- eg: ``zoom server -p 8000 ~/work/web``

-  -n, - -noop            

        - use special debugging middleware stack

-  -u USER, - -user USER  
        
        - run site as specified user

-  -v, - -verbose         

        - verbose console logging

-  -f FILTER, - -filter FILTER


zoom setup
----------
| usage: set up a new zoom instance
| required: directory
| eg: ``zoom setup [options] directory``

zoom new
--------
| usage: create a new app
| required: command and app name
| eg: ``zoom new my_app``

- zoom new [project_name]