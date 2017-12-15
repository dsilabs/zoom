create user testuser identified by 'password';
grant all on *.* to testuser@'%';
create database zoomtest;  
