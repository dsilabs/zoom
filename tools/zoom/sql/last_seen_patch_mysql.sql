alter table users add column `last_seen` datetime default NULL AFTER `updated`;
alter table users add KEY `last_seen` (`last_seen`);
