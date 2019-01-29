# README

[![Build Status](https://travis-ci.org/dsilabs/zoom.svg?branch=master)](https://travis-ci.org/dsilabs/zoom)
[![Coverage Status](https://coveralls.io/repos/github/dsilabs/zoom/badge.svg?branch=master)](https://coveralls.io/github/dsilabs/zoom?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Zoom is a dynamic Python Web framework written specifically for Python 3 that
promotes modularity and rapid prototyping for building and maintaining useful
web sites quickly and easily.


## Requirements
Zoom requires Python 3 and MySQL to run, along with a host of other 3rd party library requirements which are listed in the `requirements.txt` file.  It is currently tested and used on various flavours of GNU/Linux, Mac and Windows.


## Getting started with Zoom
The best way to get started with Zoom is to try it.  By following along with
this guide step by step you'll create a simple blog Zoom app.
Before you can start building the app, you need to make sure that you have Zoom
installed.


### Installing Zoom
Open up a terminal window and follow along with the following steps.  The
dollar sign $ in the following examples is the command prompt.

Zoom is a Python 3 framework so you'll need to have Python 3 installed to run it.  We
recommend the latest version which you can download from [python.org](https://www.python.org/downloads/).

Zoom is currently available only on GitHub.  The best way to get Zoom is to
clone it from here.  To do this you'll need git installed on
your system.

All set?  Okay, here we go!

1. Clone zoom
    ```shell
    $ git clone https://github.com/dsilabs/zoom.git
    ```

2. Install dependancies.
    ```shell
    $ pip3 install -r zoom/requirements.txt
    ```

3. Put the zoom directory on your pythonpath. <br><br>
There are several ways to do this, but the simplest is probably to add the zoom directory to your PYTHONPATH.  Inside the zoom repository you'll see the zoom library directory.  That's the directory that you'll need to add to your PYTHONPATH.  So, if you cloned zoom into /tmp/zoom then you'll set your PYTHONPATH like so:
    ```
    $ export PYTHONPATH=/tmp/zoom
    ```

4. Add zoom command to your path. <br><br>
Ubuntu example:
    ```shell
    $ ln -s /tmp/zoom/utils/zoom/bin/zoom /usr/local/bin/zoom
    ```

5. Configure the zoom database. <br><br>
Currently, Zoom requires a MySQL comptabile database to run.  If you don't already have MySQL or MariaDB installed follow the instructions for your operating system.  Alternatively you can use a Mariadb/MySQL instance inside a docker container. In either case make sure you set the port to -p 3306:3306. 
    ```shell 
    $ docker run --dbname zoom-mariadb -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD -p 3306:3306 -d mariadb:latest
    ```
Once that is installed create the database using the command:
    ```shell
    $ zoom database -e mysql -u root -p $MYSQL_ROOT_PASSWORD create <dbname>
    ```
   Next, edit the site.ini file for the localhost site using your editor like so:
    ```shell
    $ vi web/sites/localhost/site.ini
    ``` 

   Find the database section of the config file and set the values for the
database configuration to correspond to your database configuration. Typically:
    ```shell
    [monitoring]
    profiling=1
    logging=1
    app_database=1

    [database]
    user=<username>
    password=<password>

    ```

6. Run zoom. <br><br>
If you are currently in the zoom directory then you don't need to tell
zoom where to find your zoom instance or you can specify the directory and port.
    ```shell
    $ zoom server -p 8080 ~/work/web
    ```

### Creating the Blog App
First, you'll need a place to build your apps.  Make an apps directory and cd into it.
```shell
$ mkdir apps && cd apps
```

To let Zoom know where to find this apps directory add it to the `site.ini` file. In your `site.ini` file, which you'll find in the web/sites/localhost directory look for the path setting in the [apps] section of the and add the path to your apps directory.

Next, let's create the blog app.  Start by creating a blog directory in your apps.

```shell
$ mkdir blog && cd blog
```

Now we'll create a very simple hello world app, just to make sure it's all working correctly.  Create a file called `app.py` that contains this:

```python
"""
    zoom app v 0.1
"""

import zoom

def hello(request):
    return zoom.page('Hello, World!', title='Hello!')
```

Go to your Zoom instance (localhost) in your browser and you should see your new app.

This is the most basic app, which basically takes a request object as the sole parameter and returns a response, in this case, a page response.

To do a more advanced app, Zoom provides an App class that handles basic routing, other services, and calls other parts of your app.  To use it just create an instance of it in your `app.py` file, like this:

```python
"""
    zoom app v 0.2
"""

import zoom

app = zoom.App()
```

Now when you run your app you should get a "Page Not Found" status 404 page.  This is happening because we haven't provided any pages for the app.  To do that create an `index.py` file to provided the app content.

With our blog app, we're going to use a Zoom collection.  A Zoom collection is a collection of any type of field related data that you would like to store.  It provides all the things you would typically expect of a basic data collection app including browsing records, searching, editing and displaying information.

In our case, we'd like to store blog posts.  For this example, for each blog entry we'll store a name, a description, the blog post body, and a published date.

We start by defining a function that returns the fields we want to use in our app.  We then pass that function to the Collection class which will use the fields to create a collection.

```python
"""
    blog index v 0.1
"""

import zoom
import zoom.fields as f

def blog_fields():
    return f.Fields(
    f.TextField('Name'),
    f.MemoField('Description'),
    f.EditField('Body'),
    f.DateField('Date Published'),
    )

main = zoom.collect.Collection(
    blog_fields,
    url=zoom.system.app.url,
)
```

Now, when you run your app.  You should see a list where you can create blog entries.

Now, let's say, you realized you would like to add an Author field.  Just add the field to the list and re-run your app.  Like this:

```python
"""
    blog index v 0.1
"""

import zoom
import zoom.fields as f

def blog_fields():
    return f.Fields(
    f.TextField('Name'),
    f.TextField('Author'),
    f.MemoField('Description'),
    f.EditField('Body'),
    f.DateField('Date Published'),
    )

main = zoom.collect.Collection(
    blog_fields,
    url=zoom.system.app.url,
)
```

Now, run it and try adding some data.

What, what?!  Where's the data model step?  How do I create my tables?!  Where is my data stored?  What about migrations?

For now, Zoom will handle all of this for you.  Rest assured, your data is being stored in the MySQL database, but it's being stored in an entity store with a dynamic schema so you can add and remove fields from your collection at will and Zoom will just take care of it.

Zoom can use traditional tables as well, of course, but for prototyping and many other types of work a dynamic schema works very well.

That's as far as we'll go with the app right now.  In the future we'll provide more of the features people have come to expect from a blog app.


## Contributing
To contribute your own code to Zoom you'll need to setup a development
environment.

### Setting Up The Easy way
The simplest way to hack on Zoom is to use one of our
[Vagrant boxes](https://github.com/dsilabs/vagrant-zoom) or
[Docker containers](https://github.com/dsilabs/docker-zoom-tiny).

### Setting Up The Hard Way
If you can't use the prepared boxes then the best way to do that is to look
at the Dockerfile or Vagrantfile of the boxes and see how those are set up.

### Testing
Once your box is setup you can run the tests by switching to the zoom directory
and running nosetests.
```shell
$ nosetests
```

This will run the unittests, doctests and sidetests.  If your box is not
setup for sidetests (which uses webdriver, and various other libraries) you
can skip them by specifying only the other directories for tests.
```shell
$ nosetests zoom tests/unittests
```
