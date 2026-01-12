# database.py
import pymysql
from Config import Config
from Logger import LOGGER

def connect_to_db():
    """Connect to MySQL database."""
    LOGGER.info("Attempting to connect to database.")
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USERNAME,
            password=Config.DB_PASSWORD,
            db=Config.DB_NAME,
            port=Config.DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        LOGGER.info("Database connection established successfully.")
        return connection
    except Exception as e:
        LOGGER.error(f"Database connection failed: {e}")
        raise e

def execute_query(connection, query, params=None, fetch=None):
    """Execute SQL query.
    - fetch: None for commit, 'all' for fetchall, 'one' for fetchone
    """
    LOGGER.info(f"Executing query: {query}")
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if fetch == 'all':
            result = cursor.fetchall()
        elif fetch == 'one':
            result = cursor.fetchone()
        else:
            connection.commit()
            result = cursor.lastrowid if 'INSERT' in query.upper() else None
        LOGGER.info(f"Query executed successfully: {query}")
        return result
    except Exception as e:
        LOGGER.error(f"Query failed: {query} - {e}")
        raise e
    finally:
        cursor.close()

def disconnect_from_db(connection):
    """Disconnect from database."""
    if connection:
        LOGGER.info("Closing database connection.")
        connection.close()
        LOGGER.info("Database connection closed successfully.")