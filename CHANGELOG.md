# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- add support for date and datetime in sqltools query builder

### Added

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

