"""
Database module for Drug Intelligence Automation
Handles all database connections and operations
"""

import pymysql
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from logger import get_logger


class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.connection = None
        self.cursor = None
        self.logger = get_logger()
    
    def connect(self) -> bool:
        """
        Establish database connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info("Connecting to database...")
            self.connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            self.logger.info("Database connection established successfully")
            return True
        except Exception as e:
            self.logger.log_exception(e, "Database connection")
            return False
    
    def disconnect(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.log_exception(e, "Database disconnection")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            yield self
            self.connection.commit()
            self.logger.debug("Transaction committed successfully")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Transaction rolled back due to error: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        Execute SELECT query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            List of dictionaries containing query results
        """
        try:
            self.logger.log_database_operation("SELECT", "multiple", query[:100])
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.logger.debug(f"Query returned {len(results)} rows")
            return results
        except Exception as e:
            self.logger.log_exception(e, f"Query execution: {query[:100]}")
            raise
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Number of affected rows
        """
        try:
            operation = query.strip().split()[0].upper()
            self.logger.log_database_operation(operation, "table", query[:100])
            
            if params:
                affected_rows = self.cursor.execute(query, params)
            else:
                affected_rows = self.cursor.execute(query)
            
            self.connection.commit()
            self.logger.debug(f"{operation} affected {affected_rows} rows")
            return affected_rows
        except Exception as e:
            self.connection.rollback()
            self.logger.log_exception(e, f"Update execution: {query[:100]}")
            raise
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute INSERT query and return last insert ID
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Last inserted ID
        """
        try:
            self.logger.log_database_operation("INSERT", "table", query[:100])
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            last_id = self.cursor.lastrowid
            self.logger.debug(f"INSERT successful, last ID: {last_id}")
            return last_id
        except Exception as e:
            self.connection.rollback()
            self.logger.log_exception(e, f"Insert execution: {query[:100]}")
            raise
    
    def truncate_table(self, table_name: str) -> bool:
        """
        Truncate a table
        
        Args:
            table_name: Name of table to truncate
        
        Returns:
            bool: True if successful
        """
        try:
            query = f"TRUNCATE TABLE {table_name}"
            self.logger.log_database_operation("TRUNCATE", table_name, "")
            self.execute_update(query)
            self.logger.info(f"Table {table_name} truncated successfully")
            return True
        except Exception as e:
            self.logger.log_exception(e, f"Truncate table: {table_name}")
            return False
    
    def get_max_id(self, table_name: str, id_column: str, 
                   where_clause: str = "") -> Optional[int]:
        """
        Get maximum ID from a table
        
        Args:
            table_name: Table name
            id_column: ID column name
            where_clause: Optional WHERE clause
        
        Returns:
            Maximum ID or None
        """
        try:
            query = f"SELECT MAX({id_column}) as max_id FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            result = self.execute_query(query)
            if result and result[0]['max_id']:
                return int(result[0]['max_id'])
            return None
        except Exception as e:
            self.logger.log_exception(e, f"Get max ID from {table_name}")
            return None
    
    def insert_log_entry(self, table_name: str, log_data: Dict[str, Any]) -> Optional[int]:
        """
        Insert log entry and return log ID
        
        Args:
            table_name: Log table name
            log_data: Dictionary of log data
        
        Returns:
            Log ID or None
        """
        try:
            columns = ', '.join(log_data.keys())
            placeholders = ', '.join(['%s'] * len(log_data))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            self.cursor.execute(query, tuple(log_data.values()))
            self.connection.commit()
            
            log_id = self.cursor.lastrowid
            self.logger.info(f"Log entry inserted with ID: {log_id}")
            return log_id
        except Exception as e:
            self.connection.rollback()
            self.logger.log_exception(e, f"Insert log entry to {table_name}")
            return None
    
    def update_process_status(self, process_status_table: str, process_id: int, 
                             status: str, error_message: str = None) -> bool:
        """
        Update process status
        
        Args:
            process_status_table: Process status table name
            process_id: Process ID
            status: New status
            error_message: Optional error message
        
        Returns:
            bool: True if successful
        """
        try:
            if error_message:
                query = f"""
                    UPDATE {process_status_table} 
                    SET process_status=%s, error_message=%s, end_datetime=NOW() 
                    WHERE process_id=%s
                """
                params = (status, error_message, process_id)
            else:
                query = f"""
                    UPDATE {process_status_table} 
                    SET process_status=%s 
                    WHERE process_id=%s
                """
                params = (status, process_id)
            
            self.execute_update(query, params)
            self.logger.log_process_status(status, f"Process ID: {process_id}")
            return True
        except Exception as e:
            self.logger.log_exception(e, "Update process status")
            return False
    
    def get_variable_value(self, variable_table: str, variable_name: str) -> Optional[str]:
        """
        Get variable value from configuration table
        
        Args:
            variable_table: Variable table name
            variable_name: Variable name
        
        Returns:
            Variable value or None
        """
        try:
            query = f"SELECT value FROM {variable_table} WHERE name=%s"
            result = self.execute_query(query, (variable_name,))
            if result:
                return result[0]['value']
            return None
        except Exception as e:
            self.logger.log_exception(e, f"Get variable: {variable_name}")
            return None
    
    def get_customers(self, customer_table: str) -> List[Dict]:
        """
        Get active customers
        
        Args:
            customer_table: Customer table name
        
        Returns:
            List of customer dictionaries
        """
        try:
            query = f"SELECT customer_id, customer_name FROM {customer_table} WHERE status=1"
            return self.execute_query(query)
        except Exception as e:
            self.logger.log_exception(e, "Get customers")
            return []
    
    def get_excluded_salts(self, salt_table: str) -> List[str]:
        """
        Get list of excluded salt names
        
        Args:
            salt_table: Salt exclusion table name
        
        Returns:
            List of salt names
        """
        try:
            query = f"SELECT saltname FROM {salt_table} WHERE status=1"
            results = self.execute_query(query)
            return [row['saltname'] for row in results]
        except Exception as e:
            self.logger.log_exception(e, "Get excluded salts")
            return []
