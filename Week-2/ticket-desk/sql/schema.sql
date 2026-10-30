-- Active: 1793208308507@@127.0.0.1@3306@ticket_desk
DROP DATABASE IF EXISTS ticket_desk;

CREATE DATABASE ticket_desk;

USE ticket_desk;

-- priroities table - the SLA hours and their associated priorities
CREATE TABLE priorities(
    priority VARCHAR(10) PRIMARY KEY, -- tells the database that prioirty has to be unique and not NULL
    sla_hours INT NOT NULL CHECK (sla_hours > 0)
);

CREATE TABLE customers(
    customer_id INT AUTO_INCREMENT PRIMARY KEY, -- now i don't have to supply the primary key when inserting
    name VARCHAR(100) NOT NULL, 
    email VARCHAR(255) NOT NULL UNIQUE, -- enforces uniwue emails for a customer
    country CHAR(2) NOT NULL DEFAULT 'CA',
    monthly_fee DECIMAL(8,2) NOT NULL DEFAULT(0) CHECK (monthly_fee >=0)
);

CREATE TABLE agents(
    agent_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- SETTING PRIMARY KEYS AND CONSTRAINTS 
-- NOW TICKETS TABLE 
CREATE TABLE tickets(
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    priority VARCHAR(10) NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'assigned', 'closed')), 
    customer_id INT NOT NULL,
    agent_id INT, 
    opened_at DATETIME NOT NULL,
    closed_at DATETIME,
    CHECK(closed_at IS NULL OR closed_at >= opened_at),
    FOREIGN KEY (priority) REFERENCES priorities(priority),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE SET NULL
);

CREATE TABLE tags(
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE ticket_tags(
    ticket_id INT,
    tag_id INT,
    PRIMARY KEY (ticket_id, tag_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

CREATE TABLE ticket_events(
    event_id BIGINT,
    ticket_id INT NOT NULL,
    kind VARCHAR(20) NOT NULL, 
    note VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
);


