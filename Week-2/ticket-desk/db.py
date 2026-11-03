"""connect the desk to mysql database"""
import os
import mysql.connector

def connect():
    """returns a connection object to ticket_desl at the root account"""
    return  mysql.connector.connect(
        host="127.0.0.1",
        port="3306",
        user="root",
        password=os.environ["DESK_DB_PASSWORD"],
        database="ticket_desk"
    )
