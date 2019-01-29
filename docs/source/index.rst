Zoom Documentation
==================




What is Zoom?
^^^^^^^^^^^^^

Zoom is a web application platform that aims to provide enough out-of-the-box functionality to get your idea up and running quickly with all of the bits that it is likely to need without locking you into the framework itself.

Why Zoom exists
^^^^^^^^^^^^^^^

While many web application frameworks have been developed for Python, these frameworks primarily fall into two camps:


#. 
   minimalistic micro-frameworks for building quick and dirty web applications leaving most of the work to the developer, and;

#. 
   full-stack frameworks which take care of a lot of the details commonly required by web applications but requiring substantial up-front infrastructure decisions and configuration.

The great part about the minimalistic approach is that you're not committed to a huge stack of code that you don't need.  The challenge is that it leaves a lot out.  You end up  having to re-write the same basic supporting models and supporting administrative apps and over and over again.  How many times do you really want to write your /login, /logout and and I /forgot my password apps?

The great thing about the full-stack frameworks is that they come with all the bells and whistles that you need to support your core app.  The challenge though is that to do this they often require the use of very specific components, you are really expected to do things their way and you have to make a lot of configuration decisions up front that require thoughtful decision.  While taking a lot of the decision making out of the hands of the developer can be a good thing, sometimes developers end up working around these frameworks as much as they work with them.

Zoom is written for application developers in a hurry.  Optimized to minimize developer time, it is designed to make it easy to get something developed, running and deployed very quickly.

It attempts to do this by adhering to the following key prinicples:


* 
  Relentless Modularity

* 
  Dynamic over Static

* 
  Reasonable defaults for everything

Because of the modularity it encourages parts of your app can often be re-used in other projects so that the more you use it, the more productive you get.

As user requirements change and your app inevitably evolves, the dynamic and modular approach encourages you to make changes quickly and easily.

When would you use Zoom?
^^^^^^^^^^^^^^^^^^^^^^^^

Zoom is ideally suited to web developers that just want to get something up and running quickly without committing a lot of code to things they may want to change later. This is it's sweet spot. Because of this it is great for prototyping and rapid iterations of applications under active development.

.. toctree::
   :caption: Further reading:
   :maxdepth: 1

   readme
   todo_sampleapp
   changelog