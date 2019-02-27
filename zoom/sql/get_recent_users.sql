
create temporary table last_seen as (
    select user_id, max(timestamp) as timestamp
    from log
    where timestamp >= %(recent)s
    group by 1
);

create temporary table recent_users as (
    select
        username, last_seen.timestamp
    from users left join last_seen on users.id = last_seen.user_id
);