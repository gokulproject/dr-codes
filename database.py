"""
Database Connection Manager - Drug Intelligence Automation
Handles all MySQL database operations using pymysql
Implements connection pooling, error handling, and auto-reconnect
"""

import pymysql
from pymysql.cursors import DictCursor
from typing import Optional, List, Tuple, Any, Dict
import time
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages MySQL database connections and operations
    Uses pymysql library for all database interactions
    """
    
    def __init__(self, config: Dict[str, Any], logger=None):
        """
        Initialize database manager with configuration
        
        Args:
            config: Database configuration dictionary
            logger: Logger instance for logging database operations
        """
        self.config = config
        self.logger = logger
        self.connection: Optional[pymysql.connections.Connection] = None
        self.is_connected = False
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def connect(self) -> bool:
        """
        Establish connection to MySQL database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.logger:
                self.logger.info("⏳ Attempting to connect to database...")
            
            # Close existing connection if any
            if self.connection:
                try:
                    self.connection.close()
                except Exception:
                    pass
            
            # Create new connection
            self.connection = pymysql.connect(
                host=self.config.get('host'),
                port=self.config.get('port', 3306),
                user=self.config.get('username'),
                password=self.config.get('password'),
                database=self.config.get('database'),
                charset=self.config.get('charset', 'utf8mb4'),
                cursorclass=DictCursor,
                autocommit=self.config.get('autocommit', False),
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30
            )
            
            # Test connection
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self.is_connected = True
            
            if self.logger:
                self.logger.success(f"✅ Database connected successfully to {self.config.get('database')}")
            
            return True
            
        except pymysql.MySQLError as e:
            self.is_connected = False
            error_msg = f"MySQL Error: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ Database connection failed - {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            self.is_connected = False
            error_msg = f"Unexpected error during database connection: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to database with retry logic
        
        Returns:
            bool: True if reconnection successful
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.logger:
                    self.logger.warning(f"⏳ Reconnection attempt {attempt}/{self.max_retries}...")
                
                if self.connect():
                    return True
                    
            except Exception as e:
                if attempt < self.max_retries:
                    if self.logger:
                        self.logger.warning(f"⚠️ Reconnection attempt {attempt} failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    if self.logger:
                        self.logger.error(f"❌ All reconnection attempts failed: {str(e)}")
                    return False
        
        return False
    
    def ensure_connection(self) -> bool:
        """
        Ensure database connection is active, reconnect if needed
        
        Returns:
            bool: True if connection is active
        """
        try:
            if not self.connection or not self.is_connected:
                return self.reconnect()
            
            # Ping to check if connection is alive
            self.connection.ping(reconnect=True)
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Connection lost, attempting to reconnect: {str(e)}")
            return self.reconnect()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch_results: bool = True) -> Optional[List]:
        """
        Execute SELECT query and return results
        
        Args:
            query: SQL SELECT query
            params: Query parameters for parameterized queries
            fetch_results: Whether to fetch and return results
            
        Returns:
            List of tuples containing query results, or None
        """
        cursor = None
        try:
            # Ensure connection is active
            if not self.ensure_connection():
                raise Exception("Database connection is not active")
            
            if self.logger:
                self.logger.debug(f"ℹ️ Executing query: {query[:100]}...")
            
            cursor = self.connection.cursor()
            
            # Execute query with or without parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results if needed
            if fetch_results:
                results = cursor.fetchall()
                
                if self.logger:
                    self.logger.debug(f"✅ Query executed successfully, {len(results)} rows fetched")
                
                # Convert DictCursor results to list of tuples for compatibility
                if results and isinstance(results[0], dict):
                    return [tuple(row.values()) for row in results]
                
                return results
            else:
                if self.logger:
                    self.logger.debug("✅ Query executed successfully (no fetch)")
                return None
            
        except pymysql.MySQLError as e:
            error_msg = f"MySQL query execution error: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
                self.logger.error(f"Query: {query}")
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during query execution: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute INSERT, UPDATE, DELETE queries
        
        Args:
            query: SQL query (INSERT/UPDATE/DELETE)
            params: Query parameters for parameterized queries
            
        Returns:
            int: Number of affected rows
        """
        cursor = None
        try:
            # Ensure connection is active
            if not self.ensure_connection():
                raise Exception("Database connection is not active")
            
            if self.logger:
                self.logger.debug(f"ℹ️ Executing update: {query[:100]}...")
            
            cursor = self.connection.cursor()
            
            # Execute query
            if params:
                affected_rows = cursor.execute(query, params)
            else:
                affected_rows = cursor.execute(query)
            
            # Commit the transaction
            self.connection.commit()
            
            if self.logger:
                self.logger.debug(f"✅ Update executed successfully, {affected_rows} rows affected")
            
            return affected_rows
            
        except pymysql.MySQLError as e:
            # Rollback on error
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            
            error_msg = f"MySQL update execution error: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
                self.logger.error(f"Query: {query}")
            raise Exception(error_msg)
            
        except Exception as e:
            # Rollback on error
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            
            error_msg = f"Unexpected error during update execution: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def execute_many(self, query: str, data: List[Tuple]) -> int:
        """
        Execute batch INSERT/UPDATE operations
        
        Args:
            query: SQL query template
            data: List of tuples containing parameter values
            
        Returns:
            int: Total number of affected rows
        """
        cursor = None
        try:
            if not self.ensure_connection():
                raise Exception("Database connection is not active")
            
            if self.logger:
                self.logger.debug(f"ℹ️ Executing batch operation with {len(data)} records...")
            
            cursor = self.connection.cursor()
            affected_rows = cursor.executemany(query, data)
            self.connection.commit()
            
            if self.logger:
                self.logger.debug(f"✅ Batch operation completed, {affected_rows} total rows affected")
            
            return affected_rows
            
        except pymysql.MySQLError as e:
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            
            error_msg = f"MySQL batch execution error: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            
            error_msg = f"Unexpected error during batch execution: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions
        Automatically commits on success, rolls back on error
        
        Usage:
            with db.transaction():
                db.execute_update(query1)
                db.execute_update(query2)
        """
        try:
            if not self.ensure_connection():
                raise Exception("Database connection is not active")
            
            if self.logger:
                self.logger.debug("ℹ️ Starting transaction...")
            
            yield self
            
            self.connection.commit()
            
            if self.logger:
                self.logger.debug("✅ Transaction committed successfully")
                
        except Exception as e:
            if self.connection:
                try:
                    self.connection.rollback()
                    if self.logger:
                        self.logger.warning("⚠️ Transaction rolled back due to error")
                except Exception:
                    pass
            raise e
    
    def truncate_table(self, table_name: str) -> bool:
        """
        Truncate a database table
        
        Args:
            table_name: Name of the table to truncate
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Truncating table: {table_name}")
            
            query = f"TRUNCATE TABLE {table_name}"
            self.execute_update(query)
            
            if self.logger:
                self.logger.success(f"✅ Table {table_name} truncated successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to truncate table {table_name}: {str(e)}")
            raise
    
    def get_max_id(self, table_name: str, id_column: str, where_clause: str = "") -> Optional[int]:
        """
        Get maximum ID from a table
        
        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            where_clause: Optional WHERE clause (without WHERE keyword)
            
        Returns:
            int: Maximum ID value or None
        """
        try:
            if where_clause:
                query = f"SELECT MAX({id_column}) FROM {table_name} WHERE {where_clause}"
            else:
                query = f"SELECT MAX({id_column}) FROM {table_name}"
            
            result = self.execute_query(query)
            
            if result and result[0] and result[0][0]:
                return int(result[0][0])
            else:
                return None
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to get max ID from {table_name}: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """
        Close database connection and cleanup resources
        """
        try:
            if self.connection:
                self.connection.close()
                self.is_connected = False
                
                if self.logger:
                    self.logger.info("✅ Database connection closed successfully")
                    
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Error while closing database connection: {str(e)}")
        finally:
            self.connection = None
            self.is_connected = False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False  # Don't suppress exceptions
    
    def __del__(self):
        """Destructor - ensure connection is closed"""
        try:
            self.disconnect()
        except Exception:
            pass
