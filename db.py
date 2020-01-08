import sqlite3

# create a default path to connect to and create (if necessary) a database
# called 'database.sqlite3' in the same directory as this script

def db_connect(db_path='database/db.sqlite3'):
	con = sqlite3.connect(db_path)
	return con

con = db_connect() # connect to the database
cur = con.cursor() # instantiate a cursor obj
customers_sql = """
CREATE TABLE customers (
	user_id integer PRIMARY KEY,
	first_name  text NOT NULL)"""
cur.execute(customers_sql)

customers_sql = """
CREATE TABLE tokens (
	user_id integer PRIMARY KEY,
	type text NOT NULL,
	token text NOT NULL)"""
cur.execute(customers_sql)

observations_sql = """
CREATE TABLE observations (
	user_id integer PRIMARY KEY,
	unixtime REAL NOT NULL,
	metric real NOT NULL)"""
cur.execute(observations_sql)

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())
