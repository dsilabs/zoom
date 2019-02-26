--
-- Sqlite3 Create Test Tables
--

create table if not exists person (
    id integer not null primary key autoincrement,
    name varchar(100),
    age smallint,
    kids smallint,
    birthdate date
);

create table if not exists account (
    account_id integer not null primary key autoincrement,
    name varchar(100),
    added date
);