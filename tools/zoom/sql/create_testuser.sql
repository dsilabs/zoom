drop user testuser;
create user testuser identified by 'password';
grant all on zoomtest.* to testuser@'%';
grant all on zoomtest2.* to testuser@'%';
