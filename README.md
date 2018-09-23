# Zoom

[![Build Status](https://travis-ci.org/dsilabs/zoom.svg?branch=master)](https://travis-ci.org/dsilabs/zoom)
[![Coverage Status](https://coveralls.io/repos/github/dsilabs/zoom/badge.svg?branch=master)](https://coveralls.io/github/dsilabs/zoom?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Zoom is a dynamic Python Web framework written specifically for Python 3 that
promotes modularity and rapid prototyping for building and maintaining useful
web sites quickly and easily.

Create an app:
```python
# app.py
def app(_):
    return 'Hello World!'
```

Run it:
```shell
$ zoom server
```

View at: http://localhost


----

## Table of Contents
* [Requirements](#requirements)
* [Introduction](#introduction)
* [Getting Started with Zoom](#getting-started-with-zoom)
  * [Installing Zoom](#installing-zoom)
* [Contributing](#contributing)

## Requirements
Zoom requires Python 3 and MySQL to run, along with a host of other 3rd party library requirements which are listed in the requirements.txt file.  It is currently tested and used on Various flavours of GNU/Linux, Mac and Windows.

## Introduction
This guide provides a 60,000 foot view of Zoom, it's purpose and philosopy.

After reading this guide, you will know:
* what Zoom is
* why Zoom exists
* what sorts of projects you might want to use Zoom for

### What is it?
Zoom is a web application platform that aims to provide enough out-of-the-box functionality to get your idea up and running quickly with all of the bits that it is likely to need without locking you into the framework itself.

### Why Zoom exists
While many web application frameworks have been developed for Python, these frameworks primarily fall into two camps:

1. minimalistic micro-frameworks for building quick and dirty web applications leaving most of the work to the developer, and;

1. full-stack frameworks which take care of a lot of the details commonly required by web applications but requiring substantial up-front infrastructure decisions and configuration.

The great part about the minimalistic approach is that you're not committed to a huge stack of code that you don't need.  The challenge is that it leaves a lot out.  You end up  having to re-write the same basic supporting models and supporting administrative apps and over and over again.  How many times do you really want to write your /login, /logout and and I /forgot my password apps?

The great thing about the full-stack frameworks is that they come with all the bells and whistles that you need to support your core app.  The challenge though is that to do this they often require the use of very specific components, you are really expected to do things their way and you have to make a lot of configuration decisions up front that require thoughtful decision.  While taking a lot of the decision making out of the hands of the developer can be a good thing, sometimes developers end up working around these frameworks as much as they work with them.

Zoom is written for application developers in a hurry.  Optimized to minimize developer time, it is designed to make it easy to get something developed, running and deployed very quickly.

It attempts to do this by adhering to the following key prinicples:

* Relentless Modularity

* Dynamic over Static

* Reasonable defaults for everything

Because of the modularity it encourages parts of your app can often be re-used in other projects so that the more you use it, the more productive you get.

As user requirements change and your app inevitably evolves, the dynamic and modular approach encourages you to make changes quickly and easily.


### When would you use it?
Zoom is ideally suited to web developers that just want to get something up and running quickly without committing a lot of code to things they may want to change later. This is it's sweet spot. Because of this it is great for prototyping and rapid iterations of applications under active development.


## Getting started with Zoom
The best way to get started with Zoom is to try it.  By following along with
this guide step by step you'll create a Zoom app called blog, a simple weblog.
Before you can start building the app, you need to make sure that you have Zoom
installed.


### Installing Zoom
Open up a terminal window and follow along with the following steps.  The
dollar sign $ in the following examples is the command prompt.

Zoom is a Python 3 framework so you'll need to have Python 3 installed to run it.  We
recommend the latest version which you can from [python.org](https://www.python.org/downloads/).

Zoom is currently available only on GitHub.  The best way to get Zoom is to
clone it from here.  To do this you'll need git installed on
your system.

All set?  Okay, here we go!

1. clone zoom
    ```shell
    $ git clone https://github.com/dsilabs/zoom.git
    ```

2. install dependancies
    ```shell
    $ pip3 install -r zoom/requirements.txt
    ```

3. put the zoom directory on your pythonpath
There are several ways to do this, but the simplest is probably to add the zoom directory to your PYTHONPATH.  Inside the zoom repository you'll see the zoom library directory.  That's the directory that you'll need to add to your PYTHONPATH.  So, if you cloned zoom into /tmp/zoom then you'll set your PYTHONPATH like so:
    ```
    $ export PYTHONPATH=/tmp/zoom
    ```

3. add zoom command to your path
Ubuntu example:
    ```shell
    $ ln -s /tmp/zoom/utils/zoom/bin/zoom /usr/local/bin/zoom
    ```

4. configure zoom database
Currently, Zoom requires a MySQL comptabile database to run.  If you don't already have MySQL or MariaDB installed follow the instructions for your operating system.  Once
that is installed create the database using the command:
    ```shell
    $ zoom database create <db_name> -u <username> -p <password> -e mysql
    ```
   Next, edit the site.ini file for the localhost site using your editor like so:
    ```shell
    $ vi web/sites/localhost/site.ini
    ```
   Find the database section of the config file and set the values for the
database configuration to correspond to your database configuration.

5. Run zoom
If you are currently in the zoom directory then you don't need to tell
zoom where to find your zoom instance.
    ```shell
    $ zoom server
    ```

### Creating the Blog App
First, you'll need a place to build your apps.  Make it and cd into it.
```shell
$ mkdir apps && cd apps
```

To let Zoom know where to find this apps directory add it to the site.ini file in your `site.ini` file which you'll find in the web/sites/localhost directory.  Look for the path setting in the [apps] section of the site.ini file and add the path to your apps directory.

Next, let's create the blog app.  Start by creating a directory in your apps directory for the blog.

```shell
$ mkdir blog
```

Now we'll create a very simple hello world app, just to make sure it's all working correctly.  Create a file called app.py that contains this:

```python
"""
    zoom app v 0.1
"""

imoprt zoom

def hello(request):
    return zoom.page('Hello, World!', title='Hello!')
```

Go to your Zoom instance in your browser and you should see your new app.

This is the most basic app, which basically takes a request object as the sole parameter and returns a response, in this case, a page response.

To do a more advanced app, Zoom provides a App class that handles basic routing and other services and calls other parts of your app.  To use it just create an instance of it in your app.py file, like this:

```python
"""
    zoom app v 0.2
"""

import zoom

app = zoom.App()
```

Now when you run your app you should get a "Page Not Found" status 404 page.  This is happening because we haven't provided any pages for the app.  To do that create an index.py file to provided the app content.

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

Now, when you run your app.  You should see a list where you can enter blog entries.

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

For now, Zoom will handle all of this for you.  Rest assured, your data is being stored in the MySQL database, but it's being stored in an entity store with a dynamic schema so you can add and remove fields from your collection at will and it will just take care of it.

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
