"""
Logging module for Drug Intelligence Automation
FINAL VERSION - Ready for Production
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    """Custom logger with file and console handlers"""
    
    def __init__(self, name: str = "DrugIntelligence", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with file and console handlers"""
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler (rotating) - detailed logs
        log_filename = os.path.join(
            self.log_dir, 
            f"drug_intelligence_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler - simple logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Error file handler - only errors
        error_log_filename = os.path.join(
            self.log_dir,
            f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_file_handler = RotatingFileHandler(
            error_log_filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_file_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def exception(self, message: str):
        """Log exception with traceback"""
        self.logger.exception(message)
    
    def log_process_start(self, process_name: str, process_id: str = None):
        """Log process start"""
        msg = f"{'='*50}\nProcess Started: {process_name}"
        if process_id:
            msg += f" (ID: {process_id})"
        msg += f"\n{'='*50}"
        self.info(msg)
    
    def log_process_end(self, process_name: str, status: str = "SUCCESS"):
        """Log process end"""
        msg = f"{'='*50}\nProcess Ended: {process_name} - Status: {status}\n{'='*50}"
        if status == "SUCCESS":
            self.info(msg)
        else:
            self.error(msg)
    
    def log_database_operation(self, operation: str, table: str, details: str = ""):
        """Log database operations"""
        msg = f"DB Operation: {operation} on table '{table}'"
        if details:
            msg += f" - {details}"
        self.debug(msg)
    
    def log_file_operation(self, operation: str, filepath: str, details: str = ""):
        """Log file operations"""
        msg = f"File Operation: {operation} - {filepath}"
        if details:
            msg += f" - {details}"
        self.info(msg)


# Global logger instance
_global_logger = None


def get_logger(name: str = "DrugIntelligence", log_dir: str = "logs") -> Logger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name, log_dir)
    return _global_logger
