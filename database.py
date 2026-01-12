"""
Database operations module for Drug Intelligence Automation
"""
import pymysql
from typing import List, Dict, Any, Optional, Tuple
from logger import get_logger


class DatabaseHandler:
    """Handle all database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.cursor = None
        self.logger = get_logger()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                port=self.config['port'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            self.logger.info(f"Connected to database: {self.config['database']}")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}", exc_info=True)
            raise
    
    def disconnect(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {str(e)}")
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute SELECT query and return results"""
        try:
            self.logger.debug(f"Executing query: {query[:100]}...")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.logger.debug(f"Query returned {len(results)} rows")
            return results
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}\nQuery: {query}", exc_info=True)
            raise
    
    def execute_insert(self, query: str, params: Tuple = None) -> int:
        """Execute INSERT query and return last insert ID"""
        try:
            self.logger.debug(f"Executing insert: {query[:100]}...")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            last_id = self.cursor.lastrowid
            self.logger.debug(f"Insert successful, last ID: {last_id}")
            return last_id
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Insert failed: {str(e)}\nQuery: {query}", exc_info=True)
            raise
    
    def execute_update(self, query: str, params: Tuple = None) -> int:
        """Execute UPDATE query and return affected rows"""
        try:
            self.logger.debug(f"Executing update: {query[:100]}...")
            if params:
                affected = self.cursor.execute(query, params)
            else:
                affected = self.cursor.execute(query)
            self.connection.commit()
            self.logger.debug(f"Update affected {affected} rows")
            return affected
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Update failed: {str(e)}\nQuery: {query}", exc_info=True)
            raise
    
    def execute_delete(self, query: str, params: Tuple = None) -> int:
        """Execute DELETE query and return affected rows"""
        try:
            self.logger.debug(f"Executing delete: {query[:100]}...")
            if params:
                affected = self.cursor.execute(query, params)
            else:
                affected = self.cursor.execute(query)
            self.connection.commit()
            self.logger.debug(f"Delete affected {affected} rows")
            return affected
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Delete failed: {str(e)}\nQuery: {query}", exc_info=True)
            raise
    
    def truncate_table(self, table_name: str):
        """Truncate a table"""
        try:
            query = f"TRUNCATE TABLE {table_name}"
            self.cursor.execute(query)
            self.connection.commit()
            self.logger.log_database_operation("TRUNCATE", table_name)
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Truncate failed for table {table_name}: {str(e)}", exc_info=True)
            raise
    
    def get_max_id(self, table_name: str, id_column: str, where_clause: str = "") -> Optional[int]:
        """Get maximum ID from a table"""
        try:
            query = f"SELECT MAX({id_column}) as max_id FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            result = self.execute_query(query)
            if result and result[0]['max_id']:
                return int(result[0]['max_id'])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get max ID: {str(e)}", exc_info=True)
            raise
    
    def insert_process_log(self, log_table: str, process_id: str, customer_id: str, 
                          customer_name: str, filename: str) -> int:
        """Insert process log entry"""
        query = f"""
            INSERT INTO {log_table} 
            (process_id, customer_id, initiated_sts, start_datetime, customer_name, filename)
            VALUES (%s, %s, %s, NOW(), %s, %s)
        """
        return self.execute_insert(query, (process_id, customer_id, '1', customer_name, filename))
    
    def update_process_status(self, status_table: str, process_id: str, 
                             status: str, error_msg: str = None):
        """Update process status"""
        if error_msg:
            query = f"""
                UPDATE {status_table} 
                SET process_status = %s, error_message = %s, end_datetime = NOW()
                WHERE process_id = %s
            """
            self.execute_update(query, (status, error_msg, process_id))
        else:
            query = f"""
                UPDATE {status_table}
                SET process_status = %s, end_datetime = NOW()
                WHERE process_id = %s
            """
            self.execute_update(query, (status, process_id))
    
    def get_customers(self, customer_table: str) -> List[Dict]:
        """Get active customers"""
        query = f"SELECT customer_id, customer_name FROM {customer_table} WHERE status = 1"
        return self.execute_query(query)
    
    def get_subprocess_info(self, subprocess_table: str, customer_id: str) -> Optional[Dict]:
        """Get subprocess information for a customer"""
        query = f"""
            SELECT suprocess_name, excel_sheetname, excel_startindex, column_names
            FROM {subprocess_table}
            WHERE customer_id = %s
        """
        results = self.execute_query(query, (customer_id,))
        return results[0] if results else None
    
    def get_excluded_salts(self, salt_table: str) -> List[str]:
        """Get list of excluded salt names"""
        query = f"SELECT saltname FROM {salt_table} WHERE status = 1"
        results = self.execute_query(query)
        return [row['saltname'] for row in results]
    
    def insert_drug_record(self, table_name: str, data: Dict[str, Any]):
        """Insert drug record into specified table"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_insert(query, tuple(data.values()))
    
    def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]):
        """Batch insert multiple records"""
        if not data_list:
            return
        
        try:
            columns = ', '.join(data_list[0].keys())
            placeholders = ', '.join(['%s'] * len(data_list[0]))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            values = [tuple(data.values()) for data in data_list]
            self.cursor.executemany(query, values)
            self.connection.commit()
            self.logger.info(f"Batch inserted {len(data_list)} records into {table_name}")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Batch insert failed: {str(e)}", exc_info=True)
            raise
