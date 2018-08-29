Sample
====
This application displays a sample of (almost) all of the widgets and application elements that the Zoom platform offers.

Links
----
This is a link to external site [Google](http://www.google.com).

This is a link to an internal app [Google](/home).

This is a wikilink to [[a content page]].

Here is our email address <support@dynamic-solutions.com>.

Paragraph of Text
----
<dz:lorem>

Paragraphs with a Photo
----

![Logo](http://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Einstein_1921_portrait2.jpg/192px-Einstein_1921_portrait2.jpg) <dz:lorem>

### Level Three

<dz:lorem>

<dz:lorem>

Blockquote Example
----

<dz:lorem>

> <dz:lorem>

<dz:lorem>


Emphasis
----

Some of these words *are emphasized*.
Some of these words _are emphasized also_.

Use two asterisks for **strong emphasis**.
Or, if you prefer, __use two underscores instead__.

Tables
----
This is a sample table:

One   | Two   | Three
----- | ----- | -------
One   | Two   | Three
One   | Two   | Three
One   | Two   | Three

Data Tables
----
This is a data table:
{{data}}

Lists
----

You can do either bulleted lists, like this:

* Level One
* Level One
    * Level Two
        * Level Three
        * Level Three
    * Level Two
* Level One

Or, you can do numbered lists, like this:

1. Level One Numeric
1. Level One Numeric
1. Level One Numeric
    1. Level Two Numeric
        1. Level Three Numeric
        1. Level Three Numeric
    1. Level Two Numeric
1. Level One Numeric
    * A list item.

        With multiple paragraphs.

        Just indent the paragraphs to add them to the list item.

    * Another item in the list.


List Paragraphs
----
This is a buletted paragraph list:

*   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
    Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
    viverra nec, fringilla in, laoreet vitae, risus.
*   Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
    Suspendisse id sem consectetuer libero luctus adipiscing.

And this is a numbered paragraph list:

1.  This is a list item with two paragraphs. Lorem ipsum dolor
    sit amet, consectetuer adipiscing elit. Aliquam hendrerit
    mi posuere lectus.

    Vestibulum enim wisi, viverra nec, fringilla in, laoreet
    vitae, risus. Donec sit amet nisl. Aliquam semper ipsum
    sit amet velit.

2.  Suspendisse id sem consectetuer libero luctus adipiscing.


Code
----
I strongly recommend against using any `<blink>` tags.

I wish SmartyPants used named entities like `&mdash;`
instead of decimal-encoded entites like `&#8212;`.


If you want your page to validate under XHTML 1.0 Strict,
you've got to put paragraph tags in your blockquotes:

    <blockquote>
        <p>For example.</p>
    </blockquote>

That's how we roll.

Horizontal Rules
----
You can produce a horizontal rule by using 3 * characters in a row like this.
***

Form In Edit Mode
----

<dz:form>
    {{form1}}
</form>

Form In Show Mode
----
<dz:form>
    {{form2}}
</form>


Form with Fieldset
----
Fieldsets are not explicity supported in Zoom yet, but we include the markup here in case
you want to future proof your theme.  Since fieldsets are supported in HTML5 we are likely
to provide support for them in the future.

<form>
  <fieldset>
     <legend>Personal</legend>
     {{form3}}
  </fieldset>
</form>

Substitution
----

Site name: **<dz:site_name>**

Username: **<dz:username>**

App Variable: **{{name}}**

Missing App Variable: **{{notaname}}**

Missing App Variable with Default: **{{notaname "a default value"}}**


Helpers
----
&lt;dz:site_name&gt; : "<dz:site_name>"

&lt;dz:slogan&gt; : "<dz:slogan>"

&lt;dz:owner_name&gt; : "<dz:owner_name>"

&lt;dz:owner_name&gt; : "<dz:owner_url>"

&lt;dz:owner_email&gt; : "<dz:owner_email>"

&lt;dz:owner_link&gt; : "<dz:owner_link>"

&lt;dz:admin_email&gt; : "<dz:admin_email>"

&lt;dz:protocol&gt; : "<dz:protocol>"

&lt;dz:domain&gt; : "<dz:domain>"

&lt;dz:host&gt; : "<dz:host>"

&lt;dz:username&gt; : "<dz:username>"

&lt;dz:user_first_name&gt; : "<dz:user_first_name>"

&lt;dz:user_last_name&gt; : "<dz:user_last_name>"

&lt;dz:user_full_name&gt; : "<dz:user_full_name>"

&lt;dz:user_id&gt; : "<dz:user_id>"

&lt;dz:elapsed&gt; : "<dz:elapsed>"

&lt;dz:upper "test"&gt; : "<dz:upper "test">"

&lt;dz:current_date&gt; : "<dz:current_date>"

&lt;dz:date&gt; : "<dz:date>"

&lt;dz:year&gt; : "<dz:year>"


Missing Substitutions
----
Missing: {{no_such_value}}

Missing with default: {{no_such_value "default value"}}



That's It
----
And that's about it!  <dz:lorem>.
