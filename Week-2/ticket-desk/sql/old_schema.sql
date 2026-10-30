-- This is a comment in a sql file
/* This is a multi-line comment 
    they get ignored by the sql server interpreter 
    when this file is run */

-- We are starting with DDL: Data Definition Language
-- It is the subset of SQL commands all about defining, modifying, and managing
-- database structures and schemas rather than the data inside of them

CREATE DATABASE IF NOT EXISTS ticket_desk;
USE ticket_desk; -- we need to specify in our file, which database we want these commands to run against

CREATE TABLE IF NOT EXISTS customers(
    customer_id INT,
    name VARCHAR(100),
    email VARCHAR(255),
    country CHAR(2), -- if we try to insert something that isnt exactly two characters, we get an error
    monthly_fee DECIMAL(8,2) -- 8 position fp number with 2 after the decimal place. $xxx,xxx.XX
);

CREATE TABLE IF NOT EXISTS agents(
    agent_id INT,
    name VARCHAR(50),
    email VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id  INT,
    title VARCHAR(200),
    priority VARCHAR (10),
    status VARCHAR(10),
    customer_id INT, -- will correspond to a customer on the customer table 
    agent_id INT, -- will correspond to an agent in the agent table
    opened_at DATETIME,
    closed_at DATETIME
);