import sqlite3
import hashlib

# Create a database connection
def get_db_connection():
    return sqlite3.connect('users.db', check_same_thread=False)

# Create the user table if it doesn't exist
def create_user_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

# Add a new user to the database with a hashed password
def add_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()

# Verify the login credentials against the stored data
def verify_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_password))
        return c.fetchone()  # Returns None if no match is found
