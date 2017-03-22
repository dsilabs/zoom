--
-- Zoom Database Structure - utf8
--


--
-- Table structure for table `log`
--
DROP TABLE IF EXISTS `log`;
CREATE TABLE `log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(30) DEFAULT NULL,
  `route` varchar(80) DEFAULT NULL,
  `status` char(1) DEFAULT NULL,
  `user` varchar(30) DEFAULT NULL,
  `address` varchar(15) DEFAULT NULL,
  `login` varchar(30) DEFAULT NULL,
  `server` varchar(60) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `elapsed` int(10) DEFAULT NULL,
  `message` text,
  PRIMARY KEY (`id`),
  KEY `log_status` (`status`),
  KEY `log_app` (`app`),
  KEY `log_timestamp` (`timestamp`)
  KEY `log_user` (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `auditlog`
--
DROP TABLE IF EXISTS `audit_log`;
CREATE TABLE `audit_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(30) DEFAULT NULL,
  `user` varchar(30) DEFAULT NULL,
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
-- Table structure for table `storage_entities`
--
drop table if exists storage_entities;
create table if not exists storage_entities (
    id int not null auto_increment,
    kind      varchar(100),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `storage_values`
--
drop table if exists storage_values;
create table if not exists storage_values (
    id int not null auto_increment,
    kind      varchar(100),
    row_id    int not null,
    attribute varchar(100),
    datatype  varchar(30),
    value     text,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `entities`
--
drop table if exists entities;
create table if not exists entities (
    id int not null auto_increment,
    kind      varchar(100) NOT NULL,
    PRIMARY KEY (id),
    KEY `kind_key` (`kind`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `attributes`
--
drop table if exists attributes;
create table if not exists attributes (
    id int not null auto_increment,
    kind      varchar(100) NOT NULL,
    row_id    int not null,
    attribute varchar(100),
    datatype  varchar(30),
    value     mediumblob,
    PRIMARY KEY (id),
    KEY `row_id_key` (`row_id`),
    KEY `kind_key` (`kind`),
    KEY `kv` (`kind`, `attribute`, `value`(100))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `dz_groups`
--
DROP TABLE IF EXISTS `dz_groups`;
CREATE TABLE `dz_groups` (
  `groupid` int(11) NOT NULL auto_increment,
  `type` char(1) default NULL,
  `name` char(20) default NULL,
  `descr` char(60) default NULL,
  `admin` char(20) default NULL,
  PRIMARY KEY  (`groupid`),
  UNIQUE KEY `name` (`name`),
  KEY `name_2` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `dz_members`
--
DROP TABLE IF EXISTS `dz_members`;
CREATE TABLE `dz_members` (
  `userid` int(11) default NULL,
  `groupid` int(11) default NULL,
  UNIQUE KEY `contactid_2` (`userid`,`groupid`),
  KEY `contactid` (`userid`),
  KEY `groupid` (`groupid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `dz_sessions`
--
CREATE TABLE if not exists `dz_sessions` (
  `sesskey` varchar(32) NOT NULL default '',
  `expiry` int(11) NOT NULL default '0',
  `status` char(1) not null default 'D',
  `value` text NOT NULL,
  PRIMARY KEY  (`sesskey`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `dz_subgroups`
--
DROP TABLE IF EXISTS `dz_subgroups`;
CREATE TABLE `dz_subgroups` (
  `groupid` int(11) default NULL,
  `subgroupid` int(11) default NULL,
  UNIQUE KEY `groupid_2` (`groupid`,`subgroupid`),
  KEY `groupid` (`groupid`),
  KEY `subgroupid` (`subgroupid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Table structure for table `dz_users`
--
DROP TABLE IF EXISTS `dz_users`;
CREATE TABLE `dz_users` (
  `userid` int(5) NOT NULL auto_increment,
  `loginid` char(50) default NULL,
  `password` varchar(125) default NULL,
  `firstname` char(40) default NULL,
  `lastname` char(40) default NULL,
  `email` char(60) default NULL,
  `phone` char(30) default NULL,
  `fax` char(30) default NULL,
  `dtupd` datetime default NULL,
  `dtadd` datetime default NULL,
  `status` char(1) default NULL,
  PRIMARY KEY  (`userid`),
  UNIQUE KEY `userid` (`loginid`),
  KEY `userid_2` (`loginid`),
  KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



--
-- Dumping data for table `dz_groups`
--
LOCK TABLES `dz_groups` WRITE;
/*!40000 ALTER TABLE `dz_groups` DISABLE KEYS */;
INSERT INTO `dz_groups` VALUES
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
/*!40000 ALTER TABLE `dz_groups` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Dumping data for table `dz_subgroups`
--

LOCK TABLES `dz_subgroups` WRITE;
/*!40000 ALTER TABLE `dz_subgroups` DISABLE KEYS */;
INSERT INTO `dz_subgroups` VALUES

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

/*!40000 ALTER TABLE `dz_subgroups` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Dumping data for table `dz_users`
--

/*!40000 ALTER TABLE `dz_users` DISABLE KEYS */;
LOCK TABLES `dz_users` WRITE;
INSERT INTO `dz_users` VALUES
    (1,'admin','$bcrypt-sha256$2a,14$q4iT8GFWNrwfYDIMKaYI0e$KVxn8PWpzKbOgE/qfwG.IVhRIx.Pma6','Admin','User','admin@datazoomer.com','','',now(),now(),'A'),
    (2,'user','$bcrypt-sha256$2a,14$o6ySWvtBElcaqrnTzyx5o.$NIAMytGFktN2rgAUeTU/QY9lzTL6U0m','User','Known','user@datazoomer.com','','',now(),now(),'I'),
    (3,'guest','','Guest','User','guest@datazoomer.com','','',now(),now(),'A');
UNLOCK TABLES;
/*!40000 ALTER TABLE `dz_users` ENABLE KEYS */;

--
-- Dumping data for table `dz_members`
--

LOCK TABLES `dz_members` WRITE;
/*!40000 ALTER TABLE `dz_members` DISABLE KEYS */;
INSERT INTO `dz_members` VALUES
    (1,1),
    (2,2),
    (3,3);
/*!40000 ALTER TABLE `dz_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `storage_entities`
--
LOCK TABLES `storage_entities` WRITE;
/*!40000 ALTER TABLE `storage_entities` DISABLE KEYS */;
INSERT INTO `storage_entities` VALUES (1,'content_page');
/*!40000 ALTER TABLE `storage_entities` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Dumping data for table `storage_values`
--

LOCK TABLES `storage_values` WRITE;
/*!40000 ALTER TABLE `storage_values` DISABLE KEYS */;
INSERT INTO `storage_values` VALUES (1,'content_page',1,'keywords','str',''),(2,'content_page',1,'content','str','Welcome to <dz:domain>\r\n=============================\r\n\r\nThis web site is for the authorized use of <dz:owner_link> and our clients only. It may contain proprietary material, confidential information and/or be subject to legal privilege of <dz:owner_name>.\r\n\r\n<dz:set_template index>\r\n'),(3,'content_page',1,'page_name','str','index'),(4,'content_page',1,'description','str',''),(5,'content_page',1,'title','str','<dz:site_name>');
/*!40000 ALTER TABLE `storage_values` ENABLE KEYS */;
UNLOCK TABLES;
