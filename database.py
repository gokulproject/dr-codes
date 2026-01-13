"""
Database operations - Complete wrapper matching Robot Framework DatabaseLibrary
Includes comprehensive logging
"""
import pymysql
from typing import List, Dict, Any, Optional


class Database:
    """
    Complete database wrapper - matches Robot Framework DatabaseLibrary
    All operations logged for debugging and audit trail
    """
    
    def __init__(self):
        """Initialize database connection variables"""
        self.connection = None
        self.cursor = None
        self.logger = None
        
        # Try to get logger (optional dependency)
        try:
            from logger import get_logger
            self.logger = get_logger()
        except:
            self.logger = None
    
    def _log(self, message, level="INFO"):
        """Internal logging helper"""
        if self.logger:
            if level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.warning(message)
            elif level == "DEBUG":
                self.logger.debug(message)
            else:
                self.logger.info(message)
        else:
            print(f"{level}: {message}")
    
    def connect_to_database(self, db_module, db_name, db_user, db_pass, db_host, db_port):
        """
        Connect To Database - Exact match to Robot Framework
        
        Robot: DatabaseLibrary.Connect To Database ${db_module_name} ${db_name} 
               ${db_username} ${db_password} ${db_host} ${db_port}
        
        Args:
            db_module: Database module name (e.g., 'pymysql')
            db_name: Database name
            db_user: Database username
            db_pass: Database password
            db_host: Database host
            db_port: Database port
        """
        try:
            self._log(f"Connecting to database: {db_name}@{db_host}:{db_port}", "INFO")
            
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
            
            self._log(f"✅ Connected to database: {db_name}", "INFO")
            
            # Test connection with simple query
            self.cursor.execute("SELECT 1 as test")
            result = self.cursor.fetchone()
            
            if result and result['test'] == 1:
                self._log("Database connection verified", "DEBUG")
            
        except pymysql.Error as e:
            error_msg = f"Database connection failed: {e}"
            self._log(error_msg, "ERROR")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during database connection: {e}"
            self._log(error_msg, "ERROR")
            raise Exception(error_msg)
    
    def disconnect_from_database(self):
        """
        Disconnect From Database
        
        Robot: DatabaseLibrary.Disconnect From Database
        """
        try:
            if self.cursor:
                self.cursor.close()
                self._log("Cursor closed", "DEBUG")
            
            if self.connection:
                self.connection.close()
                self._log("✅ Disconnected from database", "INFO")
            
        except Exception as e:
            self._log(f"Error during disconnect: {e}", "WARNING")
    
    def query(self, sql_query):
        """
        Query - Execute SELECT and return results
        
        Robot: DatabaseLibrary.Query SELECT ...
        
        Args:
            sql_query: SQL SELECT query
        
        Returns:
            List of dictionaries containing query results
        """
        try:
            # Log query (truncated if too long)
            if self.logger:
                self.logger.log_sql(sql_query)
            else:
                query_display = sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                self._log(f"Executing query: {query_display}", "DEBUG")
            
            # Execute query
            self.cursor.execute(sql_query)
            results = self.cursor.fetchall()
            
            self._log(f"Query returned {len(results)} row(s)", "DEBUG")
            
            return results
            
        except pymysql.Error as e:
            error_msg = f"Query failed: {e}\nSQL: {sql_query}"
            self._log(error_msg, "ERROR")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during query: {e}\nSQL: {sql_query}"
            self._log(error_msg, "ERROR")
            raise Exception(error_msg)
    
    def execute_sql_string(self, sql_query):
        """
        Execute Sql String - Execute INSERT/UPDATE/DELETE/TRUNCATE
        
        Robot: DatabaseLibrary.Execute Sql String INSERT INTO ...
        
        Args:
            sql_query: SQL query to execute
        """
        try:
            # Log query (truncated if too long)
            if self.logger:
                self.logger.log_sql(sql_query)
            else:
                query_display = sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                self._log(f"Executing SQL: {query_display}", "DEBUG")
            
            # Execute query
            affected_rows = self.cursor.execute(sql_query)
            self.connection.commit()
            
            self._log(f"SQL executed successfully, affected rows: {affected_rows}", "DEBUG")
            
        except pymysql.Error as e:
            self.connection.rollback()
            error_msg = f"Execute SQL failed: {e}\nSQL: {sql_query}"
            self._log(error_msg, "ERROR")
            raise Exception(error_msg)
        except Exception as e:
            self.connection.rollback()
            error_msg = f"Unexpected error during execute: {e}\nSQL: {sql_query}"
            self._log(error_msg, "ERROR")
            raise Exception(error_msg)
    
    def get_length(self, query_result):
        """
        Get length of query result
        
        Args:
            query_result: Result from query()
        
        Returns:
            Number of rows in result
        """
        length = len(query_result) if query_result else 0
        self._log(f"Result length: {length}", "DEBUG")
        return length
    
    def truncate_table(self, table_name):
        """
        Truncate table - Delete all rows
        
        Args:
            table_name: Name of table to truncate
        """
        try:
            if self.logger:
                self.logger.log_database_operation("TRUNCATE", table_name)
            
            self.execute_sql_string(f"TRUNCATE TABLE {table_name}")
            self._log(f"✅ Table truncated: {table_name}", "INFO")
            
        except Exception as e:
            self._log(f"Failed to truncate table {table_name}: {e}", "ERROR")
            raise
    
    def insert_record(self, table_name, data_dict):
        """
        Insert record using dictionary
        
        Args:
            table_name: Name of table
            data_dict: Dictionary of column_name: value
        
        Returns:
            Last insert ID
        """
        try:
            columns = ', '.join(data_dict.keys())
            placeholders = ', '.join(['%s'] * len(data_dict))
            values = tuple(data_dict.values())
            
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            self.cursor.execute(query, values)
            self.connection.commit()
            
            last_id = self.cursor.lastrowid
            
            if self.logger:
                self.logger.log_database_operation("INSERT", table_name, f"ID: {last_id}")
            
            return last_id
            
        except Exception as e:
            self.connection.rollback()
            self._log(f"Insert failed on table {table_name}: {e}", "ERROR")
            raise
    
    def update_record(self, table_name, data_dict, where_clause):
        """
        Update records
        
        Args:
            table_name: Name of table
            data_dict: Dictionary of column_name: value to update
            where_clause: WHERE condition (e.g., "id = 123")
        
        Returns:
            Number of affected rows
        """
        try:
            set_clause = ', '.join([f"{k} = %s" for k in data_dict.keys()])
            values = tuple(data_dict.values())
            
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            affected = self.cursor.execute(query, values)
            self.connection.commit()
            
            if self.logger:
                self.logger.log_database_operation("UPDATE", table_name, f"Affected: {affected}")
            
            return affected
            
        except Exception as e:
            self.connection.rollback()
            self._log(f"Update failed on table {table_name}: {e}", "ERROR")
            raise
    
    def delete_record(self, table_name, where_clause):
        """
        Delete records
        
        Args:
            table_name: Name of table
            where_clause: WHERE condition (e.g., "id = 123")
        
        Returns:
            Number of affected rows
        """
        try:
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            affected = self.cursor.execute(query)
            self.connection.commit()
            
            if self.logger:
                self.logger.log_database_operation("DELETE", table_name, f"Affected: {affected}")
            
            return affected
            
        except Exception as e:
            self.connection.rollback()
            self._log(f"Delete failed on table {table_name}: {e}", "ERROR")
            raise
    
    def get_max_id(self, table_name, id_column, where_clause=""):
        """
        Get maximum ID from table
        
        Args:
            table_name: Name of table
            id_column: Name of ID column
            where_clause: Optional WHERE condition
        
        Returns:
            Maximum ID value or None
        """
        try:
            query = f"SELECT MAX({id_column}) as max_id FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            result = self.query(query)
            
            if result and result[0]['max_id']:
                return int(result[0]['max_id'])
            
            return None
            
        except Exception as e:
            self._log(f"Get max ID failed: {e}", "ERROR")
            raise
    
    def table_exists(self, table_name):
        """
        Check if table exists
        
        Args:
            table_name: Name of table
        
        Returns:
            True if table exists, False otherwise
        """
        try:
            query = f"SHOW TABLES LIKE '{table_name}'"
            result = self.query(query)
            exists = len(result) > 0
            
            self._log(f"Table '{table_name}' exists: {exists}", "DEBUG")
            return exists
            
        except Exception as e:
            self._log(f"Table exists check failed: {e}", "ERROR")
            return False
    
    def get_row_count(self, table_name, where_clause=""):
        """
        Get row count from table
        
        Args:
            table_name: Name of table
            where_clause: Optional WHERE condition
        
        Returns:
            Number of rows
        """
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            result = self.query(query)
            count = result[0]['count'] if result else 0
            
            self._log(f"Row count in {table_name}: {count}", "DEBUG")
            return count
            
        except Exception as e:
            self._log(f"Get row count failed: {e}", "ERROR")
            raise
    
    def execute_many(self, sql_query, data_list):
        """
        Execute same query multiple times with different data
        
        Args:
            sql_query: SQL query with placeholders
            data_list: List of tuples containing data
        
        Returns:
            Number of affected rows
        """
        try:
            self._log(f"Executing batch insert: {len(data_list)} rows", "DEBUG")
            
            affected = self.cursor.executemany(sql_query, data_list)
            self.connection.commit()
            
            self._log(f"Batch execute completed: {affected} rows affected", "DEBUG")
            return affected
            
        except Exception as e:
            self.connection.rollback()
            self._log(f"Batch execute failed: {e}", "ERROR")
            raise
    
    def begin_transaction(self):
        """Begin database transaction"""
        try:
            self.connection.begin()
            self._log("Transaction started", "DEBUG")
        except Exception as e:
            self._log(f"Begin transaction failed: {e}", "ERROR")
            raise
    
    def commit_transaction(self):
        """Commit database transaction"""
        try:
            self.connection.commit()
            self._log("Transaction committed", "DEBUG")
        except Exception as e:
            self._log(f"Commit failed: {e}", "ERROR")
            raise
    
    def rollback_transaction(self):
        """Rollback database transaction"""
        try:
            self.connection.rollback()
            self._log("Transaction rolled back", "WARNING")
        except Exception as e:
            self._log(f"Rollback failed: {e}", "ERROR")
            raise
    
    def is_connected(self):
        """
        Check if database is connected
        
        Returns:
            True if connected, False otherwise
        """
        try:
            if self.connection and self.cursor:
                self.cursor.execute("SELECT 1")
                return True
            return False
        except:
            return False
    
    def get_connection(self):
        """Get raw database connection object"""
        return self.connection
    
    def get_cursor(self):
        """Get raw database cursor object"""
        return self.cursor