PRAGMA synchronous = OFF;
PRAGMA journal_mode = MEMORY;
DROP TABLE if exists `log`;
CREATE TABLE `log` (
  `id` integer  NOT NULL PRIMARY KEY AUTOINCREMENT
,  `app` varchar(30) DEFAULT NULL
,  `path` varchar(80) DEFAULT NULL
,  `status` char(1) DEFAULT NULL
,  `user_id` integer  DEFAULT NULL
,  `address` varchar(15) DEFAULT NULL
,  `login` varchar(50) DEFAULT NULL
,  `server` varchar(60) DEFAULT NULL
,  `timestamp` datetime DEFAULT NULL
,  `elapsed` integer DEFAULT NULL
,  `message` longtext
);
DROP TABLE if exists `audit_log`;
CREATE TABLE `audit_log` (
  `id` integer  NOT NULL PRIMARY KEY AUTOINCREMENT
,  `app` varchar(30) DEFAULT NULL
,  `user_id` integer  DEFAULT NULL
,  `activity` varchar(30) DEFAULT NULL
,  `subject1` varchar(30) DEFAULT NULL
,  `subject2` varchar(30) DEFAULT NULL
,  `timestamp` datetime DEFAULT NULL
);
DROP TABLE if exists `entities`;
create table if not exists `entities` (
  `id` integer  NOT NULL PRIMARY KEY AUTOINCREMENT
,  `kind` varchar(100) NOT NULL
);
DROP TABLE if exists `attributes`;
create table if not exists `attributes` (
  `id` integer  NOT NULL PRIMARY KEY AUTOINCREMENT
,  `kind` varchar(100) NOT NULL
,  `row_id` integer  not null
,  `attribute` varchar(100)
,  `datatype` varchar(30)
,  `value` mediumtext
);
DROP TABLE if exists `groups`;
CREATE TABLE `groups` (
  `id` integer  NOT NULL PRIMARY KEY AUTOINCREMENT
,  `type` char(1) default NULL
,  `name` char(20) default NULL
,  `description` char(60) default NULL
,  `admin_group_id` integer  default NULL
,  UNIQUE (`name`)
);
DROP TABLE if exists `members`;
CREATE TABLE `members` (
  `user_id` integer  NOT NULL
,  `group_id` integer  NOT NULL
,  `expiry` datetime DEFAULT NULL
,  UNIQUE (`user_id`,`group_id`)
);
DROP TABLE if exists `sessions`;
CREATE TABLE `sessions` (
  `id` varchar(32) NOT NULL
,  `expiry` integer  NOT NULL
,  `status` char(1) not null default 'D'
,  `value` mediumblob NOT NULL
,  PRIMARY KEY  (`id`)
);
DROP TABLE if exists `subgroups`;
CREATE TABLE `subgroups` (
  `group_id` integer  NOT NULL
,  `subgroup_id` integer  NOT NULL
,  UNIQUE (`group_id`,`subgroup_id`)
);
DROP TABLE if exists `users`;
CREATE TABLE `users` (
  `id` integer  NOT NULL PRIMARY KEY AUTOINCREMENT
,  `username` char(50) NOT NULL
,  `password` varchar(125) default NULL
,  `first_name` char(40) default NULL
,  `last_name` char(40) default NULL
,  `email` char(60) default NULL
,  `phone` char(30) default NULL
,  `created` datetime default NULL
,  `updated` datetime default NULL
,  `last_seen` datetime default NULL
,  `created_by` integer  default NULL
,  `updated_by` integer  default NULL
,  `status` char(1) default NULL
,  UNIQUE (`username`)
);
INSERT INTO `groups` VALUES
    (1, 'U','administrators','System Administrators',1),
    (2, 'U','users','Registered Users',1),
    (3, 'U','guests','Guests',1),
    (4, 'U','everyone','All users including guests',1),
    (5, 'U','managers','Site Content Managers',1),
    (6, 'A','a_login','Login Application',1),
    (7, 'A','a_passreset','Password Reset App',1),
    (8, 'A','a_register','Registration App',1),
    (9, 'A','a_hello','Hello World App',1),
    (10,'A','a_logout','Logout application',1),
    (12,'A','a_home','Home page',1),
    (13,'A','a_signup','Sign-up Application',1),
    (14,'A','a_content','Content Editor',1),
    (16,'A','a_info','Info group',1),
    (17,'A','a_apps','application manager group',1),
    (19,'A','a_icons','icons application group',1),
    (20,'A','a_profile','profile application group',1),
    (21,'A','a_users','user admin application group',1),
    (22,'A','a_testapp','testapp application group',1),
    (26,'A','a_groups','Group application group',1),
    (27,'A','a_forgot','Forgot Password',1),
    (28,'A','a_blog','Blog',1),
    (29,'A','a_flags','Flags',1),
    (30,'A','a_settings','Settings',1);
INSERT INTO `subgroups` VALUES
    (2,1),
    (5,1),
    (6,1),
    (12,1),
    (14,1),
    (16,1),
    (17,1),
    (20,1),
    (21,1),
    (22,1),
    (26,1),
    (30,1),
    (4,2),
    (10,2),
    (12,2),
    (20,2),
    (29,2),
    (28,2),
    (4,3),
    (6,3),
    (7,3),
    (13,3),
    (27,3),
    (2,5),
    (26,5),
    (14,4);
INSERT INTO `users` VALUES
    (1,'admin','$bcrypt-sha256$2a,14$q4iT8GFWNrwfYDIMKaYI0e$KVxn8PWpzKbOgE/qfwG.IVhRIx.Pma6','Admin','User','admin@datazoomer.com','',datetime('now'),datetime('now'),NULL,NULL,NULL,'A'),
    (2,'user','$bcrypt-sha256$2a,14$o6ySWvtBElcaqrnTzyx5o.$NIAMytGFktN2rgAUeTU/QY9lzTL6U0m','User','Known','user@datazoomer.com','',datetime('now'),datetime('now'),NULL,NULL,NULL,'I'),
    (3,'guest','','Guest','User','guest@datazoomer.com','',datetime('now'),datetime('now'),NULL,NULL,NULL,'A');
INSERT INTO `members` (user_id, group_id) VALUES
    (1,1),
    (2,2),
    (3,3);
CREATE INDEX "idx_subgroups_group_id" ON "subgroups" (`group_id`);
CREATE INDEX "idx_subgroups_subgroup_id" ON "subgroups" (`subgroup_id`);
CREATE INDEX "idx_log_log_app" ON "log" (`app`);
CREATE INDEX "idx_log_log_path" ON "log" (`path`);
CREATE INDEX "idx_log_log_user_id" ON "log" (`user_id`);
CREATE INDEX "idx_log_log_address" ON "log" (`address`);
CREATE INDEX "idx_log_log_server" ON "log" (`server`);
CREATE INDEX "idx_log_log_status" ON "log" (`status`);
CREATE INDEX "idx_log_log_timestamp" ON "log" (`timestamp`);
CREATE INDEX "idx_attributes_row_id_key" ON "attributes" (`row_id`);
CREATE INDEX "idx_attributes_kind_key" ON "attributes" (`kind`);
CREATE INDEX "idx_attributes_kv" ON "attributes" (`kind`, `attribute`, `value`);
CREATE INDEX "idx_audit_log_auditlog_app" ON "audit_log" (`app`);
CREATE INDEX "idx_audit_log_auditlog_subject2" ON "audit_log" (`subject2`);
CREATE INDEX "idx_audit_log_auditlog_subject1" ON "audit_log" (`subject1`);
CREATE INDEX "idx_members_user_id" ON "members" (`user_id`);
CREATE INDEX "idx_members_group_id" ON "members" (`group_id`);
CREATE INDEX "idx_users_username" ON "users" (`username`);
CREATE INDEX "idx_users_email" ON "users" (`email`);
CREATE INDEX "idx_entities_kind_key" ON "entities" (`kind`);
