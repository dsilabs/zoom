
drop table if exists run_test_table;

create table run_test_table (
    name char(10),
    phone char(20),
    created date
);

insert into run_test_table values (
    'joe smith',
    '250-123-4567',
    '1995-02-10'
);

insert into run_test_table values (
    'pat jones',
    '250-123-4567',
    '1991-04-05'
);
