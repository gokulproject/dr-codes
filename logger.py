"""
Logger module for Drug Intelligence Automation
Handles all logging operations with process-specific log files
"""

import logging
import os
from datetime import datetime
from typing import Optional


class DrugIntelligenceLogger:
    """Custom logger for Drug Intelligence project"""
    
    def __init__(self, process_id: Optional[str] = None, log_dir: str = "logs"):
        """
        Initialize logger
        
        Args:
            process_id: Unique process identifier
            log_dir: Directory to store log files
        """
        self.process_id = process_id or "INIT"
        self.log_dir = log_dir
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup and configure logger"""
        # Create logs directory if not exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(f"DrugIntelligence_{self.process_id}")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create file handler
        log_filename = self._generate_log_filename()
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - Process: %(process_name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def _generate_log_filename(self) -> str:
        """Generate log filename with timestamp and process ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"DrugIntelligence_{self.process_id}_{timestamp}.log"
        return os.path.join(self.log_dir, filename)
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with additional context"""
        extra = {'process_name': self.process_id}
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_context('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_context('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_context('WARNING', message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self._log_with_context('ERROR', message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message"""
        self._log_with_context('CRITICAL', message, exc_info=exc_info, **kwargs)
    
    def log_function_start(self, function_name: str, **params):
        """Log function start with parameters"""
        param_str = ', '.join([f"{k}={v}" for k, v in params.items()])
        self.info(f"Starting function: {function_name}({param_str})")
    
    def log_function_end(self, function_name: str, result: str = "Success"):
        """Log function end"""
        self.info(f"Completed function: {function_name} - Result: {result}")
    
    def log_database_operation(self, operation: str, table: str, details: str = ""):
        """Log database operations"""
        self.debug(f"DB Operation: {operation} on table '{table}' - {details}")
    
    def log_file_operation(self, operation: str, filepath: str, status: str = "Success"):
        """Log file operations"""
        self.info(f"File Operation: {operation} - {filepath} - Status: {status}")
    
    def log_email_sent(self, recipients: str, subject: str, status: str = "Success"):
        """Log email sending"""
        self.info(f"Email Sent - To: {recipients} - Subject: {subject} - Status: {status}")
    
    def log_process_status(self, status: str, details: str = ""):
        """Log process status updates"""
        self.info(f"Process Status Updated: {status} - {details}")
    
    def log_customer_processing(self, customer_name: str, customer_id: str, status: str):
        """Log customer processing status"""
        self.info(f"Customer Processing - Name: {customer_name}, ID: {customer_id} - Status: {status}")
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log exception with full traceback"""
        error_msg = f"Exception occurred{' in ' + context if context else ''}: {str(exception)}"
        self.error(error_msg, exc_info=True)
    
    def update_process_id(self, new_process_id: str):
        """Update process ID for logger"""
        self.process_id = new_process_id
        # Recreate logger with new process ID
        self.logger = self._setup_logger()


# Singleton instance for global access
_logger_instance: Optional[DrugIntelligenceLogger] = None


def get_logger(process_id: Optional[str] = None) -> DrugIntelligenceLogger:
    """
    Get logger instance (singleton pattern)
    
    Args:
        process_id: Process identifier
    
    Returns:
        DrugIntelligenceLogger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = DrugIntelligenceLogger(process_id)
    elif process_id and _logger_instance.process_id != process_id:
        _logger_instance.update_process_id(process_id)
    
    return _logger_instance
