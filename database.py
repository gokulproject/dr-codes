"""
Database operations - Simple wrapper matching Robot Framework DatabaseLibrary
"""
import pymysql
from typing import List, Dict, Any


class Database:
    """Simple database wrapper - matches Robot Framework DatabaseLibrary"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect_to_database(self, db_module, db_name, db_user, db_pass, db_host, db_port):
        """
        Connect To Database - Exact match to Robot Framework
        Robot: DatabaseLibrary.Connect To Database ${db_module_name} ${db_name} ${db_username} ${db_password} ${db_host} ${db_port}
        """
        try:
            self.connection = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_pass,
                database=db_name,
                port=int(db_port),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            print(f"✅ Connected to database: {db_name}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def disconnect_from_database(self):
        """
        Disconnect From Database
        Robot: DatabaseLibrary.Disconnect From Database
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✅ Disconnected from database")
    
    def query(self, sql_query):
        """
        Query - Execute SELECT and return results
        Robot: DatabaseLibrary.Query SELECT ...
        Returns: List of dictionaries
        """
        try:
            self.cursor.execute(sql_query)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ Query failed: {e}")
            print(f"   SQL: {sql_query}")
            raise
    
    def execute_sql_string(self, sql_query):
        """
        Execute Sql String - Execute INSERT/UPDATE/DELETE/TRUNCATE
        Robot: DatabaseLibrary.Execute Sql String INSERT INTO ...
        """
        try:
            self.cursor.execute(sql_query)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Execute failed: {e}")
            print(f"   SQL: {sql_query}")
            raise
    
    def get_length(self, query_result):
        """Get length of query result"""
        return len(query_result) if query_result else 0