Configuration
====

Paths
----

Instance
: {{request.instance}}

Site
: {{request.site.path}}

Theme
: {{request.site.theme_path}}

App
: {{request.app.path}}

Apps
: {{request.site.apps_paths}}

Database
----

connect
: {{request.site.db.connect_string}}{{isolation}}


Mail
----

host
: {{request.site.smtp_host}}

port
: {{request.site.smtp_port}}

user
: {{request.site.smtp_user}}

password
: {{request.site.smtp_passwd}}


Packages
----
: {{packages}}