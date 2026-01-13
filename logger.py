"""
Logger module - Complete logging for Drug Intelligence Automation
Stores all logs in project root folder
"""
import os
import sys
from datetime import datetime


class Logger:
    """
    Complete logger that writes to console and file
    All logs stored in project root folder
    """
    
    def __init__(self, log_dir="logs"):
        """
        Initialize logger
        log_dir: Directory name for logs (created in project root)
        """
        # Get project root directory (where main.py is located)
        self.project_root = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        # Create logs directory in project root
        self.log_dir = os.path.join(self.project_root, log_dir)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            print(f"Created log directory: {self.log_dir}")
        
        # Create log files
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Main log file
        self.log_file = os.path.join(self.log_dir, f"drug_intelligence_{timestamp}.log")
        
        # Error log file
        self.error_log_file = os.path.join(self.log_dir, f"errors_{timestamp}.log")
        
        # Debug log file
        self.debug_log_file = os.path.join(self.log_dir, f"debug_{timestamp}.log")
        
        # Write initial log entry
        self._write_header()
    
    def _write_header(self):
        """Write header to log file"""
        header = f"""
{'='*80}
Drug Intelligence Automation - Log Started
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Log Location: {self.log_file}
{'='*80}
"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(header + '\n')
    
    def _format_message(self, message, level):
        """Format log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"{timestamp} - {level:8} - {message}"
    
    def _write_to_file(self, filename, message):
        """Write message to specific log file"""
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            print(f"⚠️  Failed to write to log file {filename}: {e}")
    
    def log(self, message, level="INFO"):
        """
        Log message to console and file
        
        Args:
            message: Message to log
            level: Log level (INFO, ERROR, WARNING, DEBUG)
        """
        formatted_message = self._format_message(message, level)
        
        # Print to console
        if level == "ERROR":
            print(f"\033[91m{formatted_message}\033[0m")  # Red color for errors
        elif level == "WARNING":
            print(f"\033[93m{formatted_message}\033[0m")  # Yellow color for warnings
        elif level == "DEBUG":
            print(f"\033[90m{formatted_message}\033[0m")  # Gray color for debug
        else:
            print(formatted_message)
        
        # Write to main log file
        self._write_to_file(self.log_file, formatted_message)
        
        # Write to error log if ERROR
        if level == "ERROR":
            self._write_to_file(self.error_log_file, formatted_message)
        
        # Write to debug log if DEBUG
        if level == "DEBUG":
            self._write_to_file(self.debug_log_file, formatted_message)
    
    def info(self, message):
        """Log INFO message"""
        self.log(message, "INFO")
    
    def error(self, message, exception=None):
        """
        Log ERROR message
        
        Args:
            message: Error message
            exception: Optional exception object to log traceback
        """
        self.log(message, "ERROR")
        
        # If exception provided, log traceback
        if exception:
            import traceback
            tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            self.log(f"Traceback:\n{tb}", "ERROR")
    
    def warning(self, message):
        """Log WARNING message"""
        self.log(message, "WARNING")
    
    def debug(self, message):
        """Log DEBUG message"""
        self.log(message, "DEBUG")
    
    def log_separator(self, char="=", length=80):
        """Log a separator line"""
        self.info(char * length)
    
    def log_section(self, title):
        """Log a section header"""
        self.log_separator()
        self.info(title)
        self.log_separator()
    
    def log_process_start(self, process_name):
        """Log process start"""
        self.log_separator("=", 70)
        self.info(f"PROCESS STARTED: {process_name}")
        self.log_separator("=", 70)
    
    def log_process_end(self, process_name, status="SUCCESS"):
        """Log process end"""
        self.log_separator("=", 70)
        if status == "SUCCESS":
            self.info(f"PROCESS COMPLETED: {process_name} - Status: {status}")
        else:
            self.error(f"PROCESS FAILED: {process_name} - Status: {status}")
        self.log_separator("=", 70)
    
    def log_customer_start(self, customer_name):
        """Log customer processing start"""
        self.log_separator("-", 60)
        self.info(f"Processing Customer: {customer_name}")
        self.log_separator("-", 60)
    
    def log_customer_end(self, customer_name, status="SUCCESS"):
        """Log customer processing end"""
        if status == "SUCCESS":
            self.info(f"✅ {customer_name} processed successfully")
        else:
            self.error(f"❌ {customer_name} processing failed")
    
    def log_database_operation(self, operation, table_name="", details=""):
        """Log database operation"""
        msg = f"DB Operation: {operation}"
        if table_name:
            msg += f" on table '{table_name}'"
        if details:
            msg += f" - {details}"
        self.debug(msg)
    
    def log_file_operation(self, operation, filepath, details=""):
        """Log file operation"""
        msg = f"File Operation: {operation} - {filepath}"
        if details:
            msg += f" - {details}"
        self.info(msg)
    
    def log_sql(self, sql_query):
        """Log SQL query (debug level)"""
        # Truncate long queries
        if len(sql_query) > 200:
            sql_display = sql_query[:200] + "..."
        else:
            sql_display = sql_query
        self.debug(f"SQL: {sql_display}")
    
    def log_excel_operation(self, operation, filepath, details=""):
        """Log Excel operation"""
        msg = f"Excel Operation: {operation} - {os.path.basename(filepath)}"
        if details:
            msg += f" - {details}"
        self.info(msg)
    
    def log_email_operation(self, recipient, subject, status="Sent"):
        """Log email operation"""
        self.info(f"Email {status}: To={recipient}, Subject={subject}")
    
    def get_log_directory(self):
        """Get log directory path"""
        return self.log_dir
    
    def get_log_file(self):
        """Get main log file path"""
        return self.log_file
    
    def get_error_log_file(self):
        """Get error log file path"""
        return self.error_log_file


# Global logger instance
_global_logger = None


def get_logger(log_dir="logs"):
    """
    Get global logger instance
    
    Args:
        log_dir: Directory name for logs (default: 'logs')
    
    Returns:
        Logger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(log_dir)
    return _global_logger


def reset_logger():
    """Reset global logger (useful for testing)"""
    global _global_logger
    _global_logger = None


# Convenience functions
def log_info(message):
    """Quick info log"""
    get_logger().info(message)


def log_error(message, exception=None):
    """Quick error log"""
    get_logger().error(message, exception)


def log_warning(message):
    """Quick warning log"""
    get_logger().warning(message)


def log_debug(message):
    """Quick debug log"""
    get_logger().debug(message)