"""
Logger Module - Drug Intelligence Automation
Comprehensive logging with dual output: File + Console
Includes colored console output with status indicators
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with color codes for console output
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[37m',       # White
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'SUCCESS': '\033[32m',    # Green
        'RESET': '\033[0m'        # Reset
    }
    
    # Status icons
    ICONS = {
        'DEBUG': 'ℹ️',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
        'SUCCESS': '✅',
        'PENDING': '⏳'
    }
    
    def format(self, record):
        """
        Format log record with colors and icons for console
        """
        # Add color based on level
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # Add icon if available
            icon = self.ICONS.get(record.levelname, '')
            
            # Create colored message
            record.levelname_colored = f"{color}{icon} {record.levelname}{reset}"
            record.msg_colored = f"{color}{record.msg}{reset}"
        
        return super().format(record)


class DrugIntelligenceLogger:
    """
    Custom logger for Drug Intelligence Automation
    Provides dual logging: File (detailed) + Console (formatted with colors)
    """
    
    def __init__(self, process_id: Optional[str] = None, log_dir: str = "./logs"):
        """
        Initialize logger with file and console handlers
        
        Args:
            process_id: Unique process identifier for log file naming
            log_dir: Directory to store log files
        """
        self.process_id = process_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path(log_dir)
        
        # Create log directory if not exists
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create log directory: {e}")
            self.log_dir = Path(".")
        
        # Generate log filename: ProcessID_DateTime.log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"Process_{self.process_id}_{timestamp}.log"
        self.log_filepath = self.log_dir / self.log_filename
        
        # Create logger
        self.logger = logging.getLogger(f"DrugIntelligence_{self.process_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers if any
        self.logger.handlers.clear()
        
        # Add custom SUCCESS level
        self._add_success_level()
        
        # Setup file handler
        self._setup_file_handler()
        
        # Setup console handler
        self._setup_console_handler()
        
        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info(f"Drug Intelligence Automation - Process ID: {self.process_id}")
        self.logger.info(f"Log File: {self.log_filepath}")
        self.logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 80)
    
    def _add_success_level(self):
        """
        Add custom SUCCESS logging level (between INFO and WARNING)
        """
        SUCCESS_LEVEL = 25
        logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
        
        def success(self, message, *args, **kwargs):
            if self.isEnabledFor(SUCCESS_LEVEL):
                self._log(SUCCESS_LEVEL, message, args, **kwargs)
        
        logging.Logger.success = success
    
    def _setup_file_handler(self):
        """
        Setup file handler for detailed logging
        """
        try:
            # File handler - detailed format
            file_handler = logging.FileHandler(
                self.log_filepath,
                mode='a',
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # File format: timestamp | level | function | message
            file_format = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(funcName)-25s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Error setting up file handler: {e}")
    
    def _setup_console_handler(self):
        """
        Setup console handler for colored real-time output
        """
        try:
            # Console handler - simple colored format
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Console format: icon + level + message
            console_format = ColoredFormatter(
                fmt='%(levelname_colored)-20s | %(msg_colored)s'
            )
            console_handler.setFormatter(console_format)
            
            self.logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"Error setting up console handler: {e}")
    
    def debug(self, message: str):
        """Log DEBUG level message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log INFO level message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log WARNING level message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log ERROR level message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log CRITICAL level message"""
        self.logger.critical(message)
    
    def success(self, message: str):
        """Log SUCCESS level message"""
        self.logger.success(message)
    
    def pending(self, message: str):
        """Log PENDING status (INFO level with pending icon)"""
        # Temporarily modify the message for pending status
        self.logger.info(f"⏳ {message}")
    
    def log_function_entry(self, func_name: str, **kwargs):
        """
        Log function entry with parameters
        
        Args:
            func_name: Name of the function
            **kwargs: Function parameters to log
        """
        params = ", ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else "No parameters"
        self.debug(f">>> ENTERING: {func_name}({params})")
    
    def log_function_exit(self, func_name: str, result: any = None):
        """
        Log function exit with result
        
        Args:
            func_name: Name of the function
            result: Return value or result status
        """
        result_str = f"Result: {result}" if result is not None else "Completed"
        self.debug(f"<<< EXITING: {func_name} - {result_str}")
    
    def log_exception(self, func_name: str, exception: Exception):
        """
        Log exception with details
        
        Args:
            func_name: Name of the function where exception occurred
            exception: Exception object
        """
        import traceback
        self.error(f"Exception in {func_name}: {type(exception).__name__}: {str(exception)}")
        self.debug(f"Traceback:\n{traceback.format_exc()}")
    
    def log_database_query(self, query: str, params: Optional[tuple] = None):
        """
        Log database query execution
        
        Args:
            query: SQL query string
            params: Query parameters if any
        """
        if params:
            self.debug(f"DB Query: {query} | Params: {params}")
        else:
            self.debug(f"DB Query: {query}")
    
    def log_file_operation(self, operation: str, filepath: str, status: str = "SUCCESS"):
        """
        Log file operations
        
        Args:
            operation: Type of operation (READ, WRITE, DELETE, MOVE)
            filepath: File path
            status: Operation status
        """
        icon = "✅" if status == "SUCCESS" else "❌"
        self.info(f"{icon} File {operation}: {filepath}")
    
    def log_email_status(self, recipient: str, subject: str, status: str):
        """
        Log email sending status
        
        Args:
            recipient: Email recipient
            subject: Email subject
            status: Send status
        """
        icon = "✅" if status == "SUCCESS" else "❌"
        self.info(f"{icon} Email {status}: To={recipient} | Subject={subject}")
    
    def log_process_step(self, step_name: str, status: str = "STARTED"):
        """
        Log major process steps
        
        Args:
            step_name: Name of the process step
            status: STARTED, COMPLETED, FAILED
        """
        separator = "-" * 60
        
        if status == "STARTED":
            self.info(separator)
            self.pending(f"STEP: {step_name}")
            self.info(separator)
        elif status == "COMPLETED":
            self.success(f"STEP COMPLETED: {step_name}")
            self.info(separator)
        elif status == "FAILED":
            self.error(f"STEP FAILED: {step_name}")
            self.info(separator)
    
    def log_summary(self, summary_data: dict):
        """
        Log summary report at end of execution
        
        Args:
            summary_data: Dictionary with summary information
        """
        self.info("=" * 80)
        self.info("EXECUTION SUMMARY")
        self.info("=" * 80)
        
        for key, value in summary_data.items():
            self.info(f"{key}: {value}")
        
        self.info("=" * 80)
    
    def close(self):
        """
        Close all handlers and cleanup
        """
        try:
            self.info("=" * 80)
            self.info(f"Logging ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.info(f"Log file saved: {self.log_filepath}")
            self.info("=" * 80)
            
            # Close all handlers
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
                
        except Exception as e:
            print(f"Error closing logger: {e}")


# Convenience function to create logger
def create_logger(process_id: Optional[str] = None, log_dir: str = "./logs") -> DrugIntelligenceLogger:
    """
    Create and return a DrugIntelligenceLogger instance
    
    Args:
        process_id: Unique process identifier
        log_dir: Directory to store log files
        
    Returns:
        DrugIntelligenceLogger instance
    """
    return DrugIntelligenceLogger(process_id=process_id, log_dir=log_dir)
