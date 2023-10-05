import mysql.connector


def get_database_connection():
    # Define your database connection parameters here
    db_config = {
        'host': "srv509.hstgr.io",
        'user': "u450827651_bot",
        'password': "Riniko123",
        'database': "u450827651_bot"
    }

    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        return None
