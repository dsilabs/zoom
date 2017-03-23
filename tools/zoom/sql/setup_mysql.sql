--
-- Zoom Database Structure - utf8
--


--
-- Table structure for table `log`
--
DROP TABLE IF EXISTS `log`;
CREATE TABLE `log` (
  `id` unsigned int NOT NULL AUTO_INCREMENT,
  `app` varchar(30) DEFAULT NULL,
  `path` varchar(80) DEFAULT NULL,
  `status` char(1) DEFAULT NULL,
  `user_id` unsigned int DEFAULT NULL,
  `address` varchar(15) DEFAULT NULL,
  `login` varchar(50) DEFAULT NULL,
  `server` varchar(60) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `elapsed` int(10) DEFAULT NULL,
  `message` longtext,
  PRIMARY KEY (`id`),
  KEY `log_app` (`app`),
  KEY `log_path` (`path`),
  KEY `log_username` (`username`),
  KEY `log_address` (`address`),
  KEY `log_status` (`status`),
  KEY `log_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `auditlog`
--
DROP TABLE IF EXISTS `audit_log`;
CREATE TABLE `audit_log` (
  `id` unsigned int NOT NULL AUTO_INCREMENT,
  `app` varchar(30) DEFAULT NULL,
  `user_id` unsigned int DEFAULT NULL,
  `activity` varchar(30) DEFAULT NULL,
  `subject1` varchar(30) DEFAULT NULL,
  `subject2` varchar(30) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auditlog_app` (`app`),
  KEY `auditlog_subject2` (`subject2`),
  KEY `auditlog_subject1` (`subject1`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `entities`
--
drop table if exists entities;
create table if not exists entities (
  `id` unsigned int NOT NULL AUTO_INCREMENT,
  `kind` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `kind_key` (`kind`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `attributes`
--
drop table if exists attributes;
create table if not exists attributes (
  `id` unsigned int NOT NULL AUTO_INCREMENT,
  `kind` varchar(100) NOT NULL,
  `row_id` int not null,
  `attribute` varchar(100),
  `datatype` varchar(30),
  `value` mediumblob,
  PRIMARY KEY (`id`),
  KEY `row_id_key` (`row_id`),
  KEY `kind_key` (`kind`),
  KEY `kv` (`kind`, `attribute`, `value`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `groups`
--
DROP TABLE IF EXISTS `groups`;
CREATE TABLE `groups` (
  `id` unsigned int NOT NULL AUTO_INCREMENT,
  `type` char(1) default NULL,
  `name` char(20) default NULL,
  `description` char(60) default NULL,
  `admin_group_id` unsigned int default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `members`
--
DROP TABLE IF EXISTS `members`;
CREATE TABLE `members` (
  `user_id` unsigned int NOT NULL,
  `group_id` unsigned int NOT NULL,
  UNIQUE KEY `user_group` (`user_id`,`group_id`),
  KEY `user_id` (`user_id`),
  KEY `group_id` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `sessions`
--
CREATE TABLE if not exists `sessions` (
  `id` varchar(32) NOT NULL,
  `expiry` unsigned int NOT NULL,
  `status` char(1) not null default 'D',
  `value` text NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `subgroups`
--
DROP TABLE IF EXISTS `subgroups`;
CREATE TABLE `subgroups` (
  `group_id` unsigned int NOT NULL,
  `subgroup_id` unsigned int NOT NULL,
  UNIQUE KEY `group_subgroup` (`group_id`,`subgroup_id`),
  KEY `group_id` (`group_id`),
  KEY `subgroup_id` (`subgroup_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `users`
--
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` unsigned int NOT NULL AUTO_INCREMENT,
  `username` char(50) NOT NULL,
  `password` varchar(125) default NULL,
  `first_name` char(40) default NULL,
  `last_name` char(40) default NULL,
  `email` char(60) default NULL,
  `phone` char(30) default NULL,
  `created` datetime default NULL,
  `updated` datetime default NULL,
  `created_by` unsigned int default NULL,
  `updated_by` unsigned int default NULL,
  `status` char(1) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `id` (`username`),
  KEY `username` (`username`),
  KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



--
-- Dumping data for table `groups`
--
LOCK TABLES `groups` WRITE;
/*!40000 ALTER TABLE `groups` DISABLE KEYS */;
INSERT INTO `groups` VALUES
    (1, 'U','administrators','System Administrators','administrators'),
    (2, 'U','users','Registered Users','administrators'),
    (3, 'U','guests','Guests','administrators'),
    (4, 'U','everyone','All users including guests','administrators'),
    (5, 'U','managers','Site Content Managers','administrators'),
    (6, 'A','a_login','Login Application','administrators'),
    (7, 'A','a_passreset','Password Reset App','administrators'),
    (8, 'A','a_register','Registration App','administrators'),
    (9, 'A','a_hello','Hello World App','administrators'),
    (10,'A','a_logout','Logout application','administrators'),
    (12,'A','a_home','Home page','administrators'),
    (13,'A','a_signup','Sign-up Application','administrators'),
    (14,'A','a_content','Content Editor','administrators'),
    (16,'A','a_info','Info group','administrators'),
    (17,'A','a_apps','application manager group','administrators'),
    (19,'A','a_icons','icons application group','administrators'),
    (20,'A','a_profile','profile application group','administrators'),
    (21,'A','a_users','user admin application group','administrators'),
    (22,'A','a_testapp','testapp application group','administrators'),
    (26,'A','a_groups','Group application group','administrators'),
    (27,'A','a_forgot','Forgot Password','administrators'),
    (28,'A','a_blog','Blog','administrators'),
    (29,'A','a_flags','Flags','administrators'),
    (30,'A','a_settings','Settings','administrators');
/*!40000 ALTER TABLE `groups` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Dumping data for table `subgroups`
--

LOCK TABLES `subgroups` WRITE;
/*!40000 ALTER TABLE `subgroups` DISABLE KEYS */;
INSERT INTO `subgroups` VALUES

-- Admin
    ( 2,1),
    ( 5,1),
    ( 6,1),
    (12,1),
    (14,1),
    (16,1),
    (17,1),
    (20,1),
    (21,1),
    (22,1),
    (26,1),
    (30,1),

-- Users
    ( 4,2),
    (10,2),
    (12,2),
    (20,2),
    (29,2),
    (28,2),

-- Guests (anonymous)
    ( 4,3),
    ( 6,3),
    ( 7,3),
--    ( 8,3), -- register
    (13,3),
    (27,3),

-- Managers
     (2,5),
    (26,5),

-- Everyone
    (14,4);

/*!40000 ALTER TABLE `subgroups` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Dumping data for table `users`
--

/*!40000 ALTER TABLE `users` DISABLE KEYS */;
LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES
    (1,'admin','$bcrypt-sha256$2a,14$q4iT8GFWNrwfYDIMKaYI0e$KVxn8PWpzKbOgE/qfwG.IVhRIx.Pma6','Admin','User','admin@datazoomer.com','',now(),now(),'','','A'),
    (2,'user','$bcrypt-sha256$2a,14$o6ySWvtBElcaqrnTzyx5o.$NIAMytGFktN2rgAUeTU/QY9lzTL6U0m','User','Known','user@datazoomer.com','',now(),now(),'','','I'),
    (3,'guest','','Guest','User','guest@datazoomer.com','',now(),now(),'','','A');
UNLOCK TABLES;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;

--
-- Dumping data for table `members`
--

LOCK TABLES `members` WRITE;
/*!40000 ALTER TABLE `members` DISABLE KEYS */;
INSERT INTO `members` VALUES
    (1,1),
    (2,2),
    (3,3);
/*!40000 ALTER TABLE `members` ENABLE KEYS */;
UNLOCK TABLES;
