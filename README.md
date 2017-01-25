# zoom

The python web platform that does less.

Zoom is a simple application platform for building dynamic web sites quickly and easily.

Create an app:
```python
# app.py
def app(request):
    return 'Hello World!'
```

Run it:
```shell
zoom server
```

View at: http://localhost


## Installation

clone zoom
```shell
git clone git@github.com:dsilabs/zoom.git
```

add zoom command to your path

Ubuntu example:
```
ln -s /path-to-libs/zoom/utils/zoom/zoom /usr/local/bin/zoom
```

----

## Table of Contents
* [Introduction](#introduction)

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

#### Relentless Modularity

#### Dynamic over Static

#### Reasonable defaults for everything

### When would you use it?
Zoom is ideally suited to web developers that just want to get something up and running quickly without committing a lot of code to things they may want to change later. This is it's sweet spot. Because of this it is great for prototyping and rapid iterations of applications under active development.
