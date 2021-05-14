create database forum charset utf8mb4;

use forum;

create table user(
    id integer primary key auto_increment,
    username varchar(128),
    password varchar(32),
    email varchar(32),
    phone varchar(16),
    is_admin integer);

create table category(
    topic varchar(128) primary key
);


create table post(
    id integer primary key auto_increment,
    title varchar(128),
    author varchar(128),
    user_id integer references user(id),
    content text,
    category_topic varchar(128) references category(topic),
    post_date datetime default current_timestamp
);


create table comment(
    id integer primary key auto_increment,
    post_id integer references post(id),
    comment text,
    author varchar(128),
    user_id integer references user(id),
    date datetime default current_timestamp
);
