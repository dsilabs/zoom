# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- add site timezone attribute
- add site time zone auto adjustments
- recongize fa prefix as fontawesome icons
- add config menu
- add app badges

## [6.22.0] - 2023-11-20
- add support for custom MySQL port
- supress autocomplete by default on date fields
- add Group methods to get subgroups and supergroups
- limit path column being inserted to size of column
- add top level db function
- add request environment variables to admin environment view
- add audit logging to Group add_user method
- add Group remove_user method

## [6.21.0] - 2023-05-01
- add quiet logging completion of ajax requests
- update admin overview to use quiet logging
- add support for multiple groups in User.is_member
- speed up admin index page
- add message id and date to email headers
- produce page title when search is empty
- use content template by default for content pages
- fix images manager of content app
- refactor module loading for Python 3.9
- promote locate_user to top level function

## [6.20.0] - 2022-05-27
- refactor and enhance icons app
- add new standard apps location to apps paths
- add support for multiple values in table find parameters
- add support for 'limit' clause in RecordStore

## [6.19.2] - 2022-05-13
- fix assign method for FilesField to handle single files

## [6.19.1] - 2022-05-13
- add missing multipart for method to FilesField

## [6.19.0] - 2022-05-11
- refactor profiler middleware
- add html.code
- handle config file read errors
- add error page for unauthorized access status 403
- fix bug causing background process crash
- add db Result value property
- add db Result map function
- add FilesField
- set crsf token lifespan to session

## [6.18.0] - 2022-03-02
- add additional chromedriver options to stabilize automated testing
- add stop impersonation support for sessions with user override
- add error log entry for low level errors
- allow packages to be included before an app has been loaded
- add support for bootstrap icons
- add app.theme_path member
- add load_component and get_components functions
- add support for http HEAD method
- fix dropzone component
- add support for Windows username domains in impersonation
- set app theme to site theme if not specified

## [6.17.0] - 2022-01-01
- autofocus on username on login
- add support for HTTP HEAD method
- promote link_to_page to top level
- add online users metric to admin app
- improve performance of admin app
- add changelog page to admin app
- show 14 days as 2 weeks in how_long function
- use webdriver find_element instead of legacy methods
- add set method to Record, RecordStore and EntityStore

## [6.16.1] - 2021-09-02
- fix bug in get_user()

## [6.16.0] - 2021-08-26
- add tab_title helper
- add 500 error template
- add created_by and updated_by to records created by User.add method
- add purge_old_job_results function
- fix bug in IntegerField zero values
- add get_users and locate_user
- add SameSite cookie morsel

## [6.15.0] - 2021-02-06
- add installed path to admin environment info page
- add support for custom themed email templates
- add ability to test email attachments in admin app
- make send_as use passed sender
- add links to paths in admin app
- remove use of fstrings to maintain v3.5 compatibility
- minor tweaks for custom collections
- return status 500 for application exceptions
- add get_db function
- add set_site function
- increase size of group name column
- increase size of audit_log app name column
- add key parameter to get_user to get specific users
- use locate for user operations to accomodate morphed usernames
- update tests to run against python 3.8 and 3.9
- add collection_of
- add users.can
- add uuid to browse table
- add name parameter to store_of
- trap NameError when logging database close at shutdown

## [6.14.0] - 2020-12-21
- add api module
- add support for nested Record attributes
- provide more informative template rendering messages

## [6.13.0] - 2020-11-27
- add support for date and datetime in sqltools query builder
- fix bug in migration revert logging
- add missing jquery requirement for datatables package
- fix bug in collection preventing image deletion in record stores
- fix bug in number field validator
- escape reserved words in store find methods
- render CheckboxField inputs with unique ids
- set database logging off by default
- make how_log_ago work with dates and datetimes

## [6.12.0] - 2020-10-29
- improve formatting of id columns in printed output
- fix bug in database.execute_many when passed single dict arg
- add support for select elements in web tests

## [6.11.0] - 2020-10-14
- use default theme as fallback for get_template
- update pivottable data serialization and styling

## [6.10.0] - 2020-10-13
- refactor Metric widget
- add support for bootstrap 4.5 pulldowns in system menu
- add profile app
- add site.system property and system helper tag
- fix json iso date encoding bug

## [6.9.0] - 2020-10-07
- add email template support
- add TimezoneField
- update bcrypt support to latest

## [6.8.0] - 2020-08-30
- add partial response
- add cards
- add progress widget
- add metric widget
- update chosen package to latest version 1.8.7

## [6.7.4] - 2020-08-30
- return str responses as content in a page
- return Component responses as content in a page
- return dict responses as JSONResponse

## [6.7.3] - 2020-08-26
- add pytz requirement for timezone support
- add order_by support for RecordStore
- adjust ID format in browse

## [6.7.2] - 2020-08-02
- Fix bug in url constructor for login redirects

## [6.7.1] - 2020-08-02
- Add login page template support
- Add level to how_long formatter

## [6.7.0] - 2020-08-02
- Add auto pug and sass compilation to DynamicComponents
- Add apps_menu helper
- Add support for Widgets
- Refine collection styling

## [6.6.0] - 2020-06-04
- Add app boilerplate
- Add DynamicComponent
- Add metadata to content overview
- Replace px with rem in default theme
- Update display of configuration settings in admin app
- Automatically fallback to default theme if specified theme is missing

## [6.5.0] - 2020-05-10
- Add user impersonation
- Add support for sass response type
- Move default instance into _assets
- Add more detailed audit logging

## [6.4.0] - 2020-04-21
- Add pug content rendering
- Add libsass support
- Add support for email addresses as usernames
- Add screenshot artifact saving for tests
- Add callable app menus
- Tighten up CLI

## [6.3.0] - 2020-04-06
- Add support for timedetla formatting
- Fix PyPi build
- Add zoom init to CLI
- Add support for more form attribute overrides
- Bundle fontawesome4
- Add ztag helper

## [6.2.2] - 2019-12-23
- Add background processing
- Enable reading of JSON request bodies

## [6.1.0] - 2019-11-26
- Add support for pip install
- Refactor and enhance CLI
- Add ability to for pages to accept multiple content items
- Add database information page to admin app
- Add confirmation emails to register app
- Add snippets
- Add support for including templates from app specific themes.
- Add content comments for missing template includes.
- Add support for WOFF2 static repsonses.
- Add db.database property.
- Add configuration options for profiler.
- Promote DynamicView to top level class.
- Add ability to support both helper tags and python format tags in templates.
- This CHANGELOG file.

## [6.0.0] - 2018-10-12
### Added
- First official tagged release
- Python 3 only
- MySQL / MariaDB support
- Linux / Mac / Windows
### Changed
- some modules ported from DataZoomer (https://github.com/dsilabs/datazoomer) which is considered the predecessor to Zoom.

