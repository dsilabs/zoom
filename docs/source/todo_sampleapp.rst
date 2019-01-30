==================
Tutorial: Todo App
==================

This tutorial will walk you through creating a new application and cover aspects from basic application structure, controllers and storage, to generating fake data and model properties. At the end you will have a functioning Todo application.

- Part 1: Creation and Basic structure
- Part 2: Controllers and storage
- Part 3: Fake Data, Model Properties, and Deleting


Part 1: Creation and Basic structure
------------------------------------

Zoom comes with a built in command to create all the files necessary to create a new application complete with a default template. 

1. ``cd`` to the directory where you want to create your app.
    ``cd ~work``

2. Run the ``zoom new my_app`` utility that will generate all the files necessary to get your app up and running.
    ``zoom new <my_app>``

Zoom has now created a directory for your app and all the boilerplate code to get started. Inspecting the contents of that directory you will see (at a minimum) the files:

    - app.py
        Every Zoom application is required to provide a module called ``app.py`` stored in the main folder for the application, which, when called, returns content for the browser.

        Through this single python program, your program will be able to provide everything from simple pages to complex visualizations and dashboards. Zoom provides many convenient tools to accomplish this with very little programming.

    - config.ini
        The config.ini file contains application settings which might include things like the application title.

    - index.py
        The index.py file contains the index or default views for the application.

3. Open ``app.py``, this is where you will see your main application menu. We want to add a new menu item, a Task page. 

    ``app.menu = 'Overview', 'About', 'Tasks'``

If you click on our new menu item you will get a 404, this is expected as we haven't built any content yet! We are now done working with the ``app.py`` module.

Part 2: MVC
-----------

4. Open ``index.py`` to get an idea of the application functionality. Zoom works by first searching index.py for the ``main`` dispatcher, the dispatcher will call anything in the list being passed to it, in this case we're calling the view. The dispatcher is responsible for creating the view and calling it. 

Zoom gives several ways to implement views, you can either:
    - Use a method on main view of application (index.py). This works fine for things that are not very complicated (i.e. require only a few lines of code), like the about page.

    - Zoom will look for a module of the same name before it looks for a view, which provides greater flexibility and is great for something more complicated like our tasks page.

Let's go ahead and make a ``tasks.py`` module and give it the basics of what zoom will look for: a view, an index method, and add a main dispatch statement. We can give our page a title and then we will likely want to display some content, a list of tasks on this page. The logic of how tasks are stored and retrived will go in ``model.py`` and ``tasks.py`` will control the presentation of the model. Let's go ahead and import zoom as well as the model. We can then add some content to our page, a browsable list of our tasks. We will also want to indlude a 'New Task' Button which we can do by using an action in our index method. Clicking our new button will result in a 404 because we haven't created the method for it yet. The ``new`` method will take care of this.   :: 


    """
        todo tasks
    """

    import zoom
    import model

    class TaskController(zoom.Controller):
    """
        We will use a controller here instead of a view because we will
        eventually want to maniputlate the underlying model instead of a read only view. 
        A controller gives us access to the ability for zoom to interpret for us.
    """

        form = model.get_task_form(self)
    """
        We will create the form outside of a method and make it act like a class so we 
        can access the form in multiple places.
    """


        def index(self):
            actions = 'New',
            content = zoom.browse(model.get_tasks())
            return zoom.page(content, title="Tasks", actions=actions)


        def new(self):
        """
            New will display an empty form that you can fill in task info and save. 
            Use the model for the form logic. The next thing we need to do is edit
            the 'new' method to return the form, so we need to pass in the form 
            data and initialize the form with the data. 
            If form validation fails, the invalid data that is coming back 
            will be passed to the new routine plus the valid data and we 
            will get an error that tells us what required field is missing.
        """

            self.form.initialize(data)
            content = self.form.edit()
            return zoom.page(content, title='New Task')

    main = zoom.dispatch(TaskController)



5. Next create a ``model.py`` module where we will write the logic for our application like how tasks are stored and retreived. In ``model.py`` import zoom. Zoom comes equipped with a variety of methods including fields and validators that we can use in our application. ::

    model.py

    """
    model
    """

    import zoom
    import zoom.fields as f
    import zoom.validators as v

    """
    tools we will use later

    import faker 
    import random
    """

    def get_tasks():
        return[]


6. Now we will use the model to create a form. Zoom provides a number of convenient tools for creating forms. A form object will give you the form itself and it can be cusomized using a variety of fields. We can go ahead and import these tools now. Then create a basic form with a title, description, and let's assign a category, and priority as well. Zoom has built-in date and time tools. We can set a default due date as one week from today as the due date for the task. We can also use the built in validator tool on any field indicating they are required. For now we'll make the title the only requirement. ::

    ...
   
    import zoom.fields as f
    import zoom.validators as v

    def get_task_form():
     """Return Task Form"""
     return zoom.Form(
         f.TextField('Title', v.required, hint='required'),
         f.MemoField('Description'),
         f.ChosenMultiselectField('Categories', options=get_category_options()),
         f.DateField('Due Date', default=zoom.tools.today() +   zoom.tools.one_week),
         f.RadioField('Priority', values=PRIORITY_OPTIONS),
         f.ButtonField('Create'),
     )

Once our form is created we can go ahead and fill in our definitions. For category options and priority options we can define the variables we used in our ``get_task_form()`` method. ::

    ...

    PRIORITY_OPTIONS = ['Low', 'Medium', 'High']
    CATEGORY_OPTIONS = ['One', 'Two', 'Three']

    def get_category_options():
        """Return a category"""
        return CATEGORY_OPTIONS

7. Now we'll get into the business of creating tasks. In Step 6 we added a ``Create`` button now we can add a task store to the TaskView Controller and create a method to be called when the button is clicked. But remember! We want to make sure the form data is valid. So we will add that logic here and then pass the evaluated data into the model. If the model returns true we will have an alert message and then return back to the 'Tasks' page. If the form fails it will return a 404 error ::

    ...

    def create_button(self, **data):
        if self.form.validate(data):
            if model.create_task(self.form.evaluate())
                zoom.alerts.success('Tasks created!')
                return zoom.home('tasks)

    ...
    

Head back to ``model.py`` and we'll add the logic to ``create_task()``. Several things will happen here. We will edit our ``get_task()`` method and then create a table schema to store our tasks. Our store will be a subtype of the class 'model' and we will store our data in a table called whatever you name your class, in this case we'll use 'Task'. Now we can edit our  ``get_task()`` method to return the Task store we just created. ::


    ...

    def create_task(data):
        tasks = get_tasks()
        tasks.put()
        return True


    
    def get_tasks():
        return zoom.store_of()


    class Task(zoom.models.Model):
        pass


    def get_tasks()
    """Return tasks"""
        return zoom.store_of(Task)


8. We'll probably want the ability to delete tasks so we can go ahead and create a 'Delete' button on our TaskController. Once we delete our tasks we can return back to the task page ::


    ...

     def zap(self):
        model.zap_tasks()
        zoom.alerts.warning('task deleted')
        return zoom.page('tasks')

In order to run the zap method we can add it to our list of actions by editing the new method  in our index. In Part 3. we will add the functionality to create a task at random so we can add 'I Feel Lucky' to our list of actions too. Let's also take this opportunity to clean up our labels. Start by specifying the columns you would like in your Task table, and then specify the labels. We can then add this to our content.  ::


    ...

    def index(self):
        columns = 'name', 'description', 'formatted_categories', 'due_date'
        labels = 'Name', 'Description', 'Categories', 'Due Date', 
        actions = 'New', 'Zap', 'I Feel Lucky'
        content = zoom.browse(model.get_tasks(), columns=columns, labels=labels)
        return zoom.page(content, title="Tasks", actions=actions)


Of course now we need to add the ``zap_task()`` logic to our model. Now that our app has basic functionality we can move on to generate tasks randomly. ::

    ...


    def zap_tasks():
    ***Zap the tasks store***
    get_tasks().zap()


Part 3: Fake Data, Model Properties, and Deleting
-------------------------------------------------

9. Let's add some functionality to create reasonable tasks at random. In ``model.py`` we can create a method to create a fake record ``add_random_task`` and create a dict to represent data. We will use the python module Faker, it's already a zoom requirment so all you need to do is import it and create an object called 'fake'. The faker package has a lot of default providers built in. We will use words, description, etc. For categories we can take a random sample of our category options using 'randint' from the zoom 'random' module. We can also use ``randint`` to pick a due date within a specified time frame. Priority will be a random choice of our ``PRIORITY_OPTIONS`` variable we declared previously. ::



    ...


    import faker
    import random

    fake = fake.Faker()

    def add_random_task():
    data = dict(
        name=' '.join(fake.words()),
        description=fake.paragraph(),
        categories=random.sample(get_category_options(), random.randint(1,3)),
        due_date=zoom.tools.today() + zoom.tools.one_day * random.randint(3,7),
        priority=random.choice(PRIORITY_OPTIONS),
    )
    form = get_task_form()
    if form.validate(data):
        create_task(form.evaluate())
    else:
        print('fail')
        zoom.utils.app(form.evaluate())

In our TaskController we will add the random task button and if the task succeeds we will return home. ::


    ...

    def i_feel_lucky(self):
        model.add_random_task()
        return zoom.home('tasks')


10. Now let's add an action to delete a single task from our list. First, we can create a column for the action in our index. ::

.. code-block:: python

    ...

    def index(self):
        columns = 'actions', 'name', 'description', 'formatted_categories', 'due_date'
        labels = 'Actions', 'Name', 'Description', 'Categories', 'Due Date', 
        actions = 'New', 'Zap', 'I Feel Lucky'
        content = zoom.browse(model.get_tasks(), columns=columns, labels=labels)
        return zoom.page(content, title="Tasks", actions=actions)



Then we can add an 'actions' property to our Task store and return a small form ``get_done_form()`` which will include a hidden field of the item key the person is clicking, and a button. In our actions property we can return the ``get_done_form()`` and initialie the key value for that particular record, then return the form in edit mode which will display the button. ::


    ...



    def get_done_form():
        return zoom.Form(
            f.Hidden('key', v.required, v.valid_number),
            f.Button('Done')
        )

    class Task(zoom.models.Model):
    
    @property
    def actions(self):
        form = get_done_form()
        form.initialize(key=self._id)
        return form.edit()  


11. Now we need to create a handler to delete the task once the button is clicled. In our TaskController our ``done_button()`` will get some data (our key) and we will get our form, and if the form validates we will get the model to complete the task for us. Just for fun let's add some affirmations once a task is completed. First create a variable AFFIRMATIONS and set it equal to a list of affirmations, then all we need to do is set an alert with a random choice of our affirmations, don't forget to import the random module! Finally we'll return back to our list of tasks. ::


.. code-block:: python

    ...


    import random
    

    AFFIRMATIONS = ['Great job!', 'Killin it!', 'You can do it!', 'Way to go!']

    def done_button(self, **data):
        form = model.get_done_form()
        if form.validate(data):
            if model.complete_task(form.evaluate()):
                zoom.alerts.success(random.choice(AFFIRMATIONS))
                return zoom.home('tasks')






Now we need to get the model to figure out how to complete the task. The data being passed in will have the key in it, so we want to grab that key, first make sure it is a valid key, then try and find a task that is associated with that key. If we get a task then we ar going to delete that task and return True. If none of this works we will return False and we won't get a success message. ::

    ...

    def complete_task(data):
        """Complete a task"""
        key = data.get('key')
        if key:
            tasks = get_tasks()
            task = tasks.get(key)
            if task:
                tasks.delete(task)
                return True

    
That's it! Now we have a fully functioning Todo application where we can create and delete tasks, and create random tasks using the Faker module. Stay tuned for more Zoom tutorials.
