"""
Logger module - Simple logging for Drug Intelligence Automation
"""
import os
from datetime import datetime


class Logger:
    """Simple logger for console and file output"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.log_file = None
        self._setup()
    
    def _setup(self):
        """Setup log directory and file"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        self.log_file = os.path.join(self.log_dir, f"drug_intelligence_{timestamp}.log")
    
    def log(self, message, level="INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {level} - {message}"
        
        # Print to console
        print(log_message)
        
        # Write to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"⚠️  Failed to write to log file: {e}")
    
    def info(self, message):
        """Log INFO message"""
        self.log(message, "INFO")
    
    def error(self, message):
        """Log ERROR message"""
        self.log(message, "ERROR")
    
    def warning(self, message):
        """Log WARNING message"""
        self.log(message, "WARNING")
    
    def debug(self, message):
        """Log DEBUG message"""
        self.log(message, "DEBUG")


# Global logger instance
_logger = None


def get_logger():
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger