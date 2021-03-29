# README

[![Build Status](https://travis-ci.org/dsilabs/zoom.svg?branch=master)](https://travis-ci.org/dsilabs/zoom)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ZoomFoundry is a dynamic Python Web framework written specifically for Python 3 that
promotes modularity and rapid prototyping for building and maintaining useful
web sites quickly and easily.


## Requirements
ZoomFoundry requires Python 3 and MySQL to run, along with a host of other
3rd party library requirements listed in the requirements.txt file.  It is
currently tested and used on various flavours of GNU/Linux, Mac and Windows.


## Getting started with ZoomFoundry
The best way to get started with ZoomFoundry is to try it.  By following along with
this guide step by step you'll create a simple blog ZoomFoundry app.  Before you can
start building the app, you need to make sure that you have ZoomFoundry installed.


### Installing ZoomFoundry
Open up a terminal window and follow along with the following steps.  The
dollar sign $ in the following examples is the command prompt.

ZoomFoundry is a Python 3 framework so you'll need to have Python 3 installed to run it.  We
recommend the latest version which you can download from [python.org](https://www.python.org/downloads/).

All set?  Okay, here we go!

1. Install ZoomFoundry
    ```shell
    $ pip install ZoomFoundry
    ```

    This will install a new Python package and corresponding CLI command; `zoom`.

1. Once you have ZoomFoundry installed, you'll first want to create and populate a
    ZoomFoundry *instance directory*.<br><br> ZoomFoundry is multi-tenant, meaning
    it can serve multiple sites at the same time; an instance directory contains a
    set of ZoomFoundry *sites* and resources shared between them. Run:
    ```shell
    $ zoom init ~/my-zoom-instance
    ```

    This will walk you through setting up your instance, including creating a
    default site and database.

    *Don't like wizards?* Every option zoom commands prompt you with have a
    corresponding command line option: see the help with `zoom -h`.

1. Serve the created instance. <br><br>
    Run the following to start the built-in server, pointed at the instance you just
    created.
    ```shell
    $ zoom serve ~/my-zoom-instance
    ```

### Creating the Blog App
To create a new app with ZoomFoundry, just run:
```shell
zoom new app blog ~/my-zoom-instance
```

*Don't mind a `cd`?* ZoomFoundry commands only require you to specify the path to an instance
directory if you aren't already inside one. You could replace the above with:
```shell
cd ~/my-zoom-instance && zoom new app blog
```

You've just created an app called `blog` at `~/my-zoom-instance/apps/blog`. Take a second to check it out.
To see the app in action, check out `http://localhost/blog` after running:
```shell
zoom serve ~/my-zoom-instance
```

This is the most basic app, which basically takes a request object as the sole parameter and returns a response, in this case, a page response.

To do a more advanced app, ZoomFoundry provides an App class that handles basic routing, other services, and calls other parts of your app.  To use it just create an instance of it in your `app.py` file, like this:

```python
"""
    zoom app v 0.2
"""

import zoom

app = zoom.App()
```

Now when you run your app you should get a "Page Not Found" status 404 page.  This is happening because we haven't provided any pages for the app.  To do that create an `index.py` file to provided the app content.

With our blog app, we're going to use a ZoomFoundry collection.  A ZoomFoundry collection is a quick way of creating an app to manager any type of field related data that you would like to store.  It provides all the things you would typically expect of a basic data collection app including browsing records, searching, editing and displaying information.

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
    url=zoom.get_app().url,
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
    url=zoom.get_app().url,
)
```

Now, run it and try adding some data.

What, what?!  Where's the data model step?  How do I create my tables?!  Where is my data stored?  What about migrations?

For now, ZoomFoundry will handle all of this for you.  Rest assured, your data is being stored in the MySQL database, but it's being stored in an entity store with a dynamic schema so you can add and remove fields from your collection at will and ZoomFoundry will just take care of it.

ZoomFoundry can use traditional tables as well, of course, but for prototyping and many other types of work a dynamic schema works very well.

That's as far as we'll go with the app right now.  In the future we'll provide more of the features people have come to expect from a blog app.


## Contributing
To contribute your own code to ZoomFoundry you'll need to setup a development environment.

### Setting Up The Easy way
The simplest way to hack on ZoomFoundry is to use one of our
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

This will run the unittests, doctests and webtests.  If your box is not
setup for sidetests (which uses webdriver, and various other libraries) you
can skip them by specifying only the other directories for tests.
```shell
$ nosetests zoom tests/unittests
```
