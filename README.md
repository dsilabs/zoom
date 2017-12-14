# zoom

[![Build Status](https://travis-ci.org/dsilabs/zoom.svg?branch=master)](https://travis-ci.org/dsilabs/zoom)
[![Coverage Status](https://coveralls.io/repos/github/dsilabs/zoom/badge.svg?branch=master)](https://coveralls.io/github/dsilabs/zoom?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Zoom is a simple web application framework for building dynamic web sites quickly and easily.

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
* [Introduction](#introduction)
* [Getting Started with Zoom](#getting-started-with-zoom)
  * [Installing Zoom](#installing-zoom)
* [Contributing](#contributing)

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

Zoom is written for application developers in a hurry.  Optimized to minimize developer time, it is designed to make it very easy to get something developed, running and deployed very quickly.

It attempts to do this by adhering to the following key prinicples:

* Relentless Modularity

* Dynamic over Static

* Reasonable defaults for everything


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

Zoom is currently available only on GitHub.  The best way to get Zoom is to
clone it from here.  To do this you'll need git installed on
your system.

All set?  Okay, here we go!

1. clone zoom
```shell
git clone git@github.com:dsilabs/zoom.git
```

2. add zoom command to your path  
Ubuntu example:  
```
ln -s /path-to-libs/zoom/utils/zoom/zoom /usr/local/bin/zoom
```

3. install dependancies
```
pip3 install -r requirements.txt
```

4. configure zoom database  
Zoom requires a database to be run.  If you don't already have MySQL or
MariaDB installed follow the instructions for your operating system.  Once
that is installed create the database using the command:
```
$ zoom database create <db_name> -u <username> -p <password> -e mysql
```
Next, edit the site.ini file for the localhost site using your editor like
so:
```
$ vi web/sites/default/site.ini
```
Find the database section of the config file and set the values for the
database configuration to correspond to your database configuration.

5. Run zoom  
If you are currently in the zoom directory then you don't need to tell
zoom where to find your zoom instance.
```
$ zoom server
```

### Creating the Blog App
Zoom comes with a command line tool that can do number of useful things for
you.  One of the things it can do is create a basic starting appplication
which runs and has the building blocks of a well formed Zoom app.

To use the tool, open a terminal window, navigate to the directory where you
want to work on the app and type:
```
$ zoom new blog
```

Go to your Zoom instance in your browser and you should see your new Blog app.
To start with it doesn't do anything useful so we need to add our blogging
functionality.


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
Once your box is setup you can run the tests by switching to the directory
and running nosetests.  

    $ cd source/libs/zoom
    $ nosetests

This will run the unittests, doctests and sidetests.  If your box is not
setup for sidetests (which uses webdriver, and various other libraries) you
can skipthem by specifying only the other directories for tests.

    $ cd soure/libs/zoom
    $ nosetests zoom tests/unitttests
