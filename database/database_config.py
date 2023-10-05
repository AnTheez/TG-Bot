import mysql.connector


def get_database_connection():
    # Define your database connection parameters here
    db_config = {
        'host': "127.0.0.1",
        'user': "root",
        'password': "",
        'database': "bot"
    }

    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        return None
