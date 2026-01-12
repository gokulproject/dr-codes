"""
Main Drug Intelligence processing module
"""
import os
import re
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import Config
from database import DatabaseHandler
from excel import ExcelHandler
from logger import get_logger
from email_sender import EmailSender
from scraper import WebScraper, DrugDatabaseScraper
from utils import DrugNameProcessor, MasterTrackerProcessor, ReportGenerator


class DrugIntelligence:
    """Main Drug Intelligence automation class"""
    
    def __init__(self, server_type: str = "DEV"):
        self.config = Config(server_type)
        self.logger = get_logger()
        self.db = None
        self.excel_handler = ExcelHandler()  # Changed from self.excel to self.excel_handler
        self.scraper = None  # Web scraper instance
        self.email_sender = None
        self.process_id = None
        self.excluded_saltnames = []
        self.master_tracker_path = None
        
    def initialize_process(self):
        """Initialize the process - connect DB, load config"""
        try:
            self.logger.log_process_start("Drug Intelligence Automation")
            
            # Connect to database
            self.db = DatabaseHandler(self.config.get_db_config())
            self.db.connect()
            
            # Load configuration from database
            self._load_db_configuration()
            
            # Initialize email sender
            self.email_sender = EmailSender(self.config.get_email_config())
            
            # Initialize web scraper (optional - if needed for data enrichment)
            self.scraper = WebScraper()
            
            # Create necessary directories
            self._create_directories()
            
            # Validate files exist
            if not self._validate_input_files():
                self.logger.warning("No Master Tracker or Client files found. Exiting.")
                return False
            
            # Load excluded salts
            self.excluded_saltnames = self.db.get_excluded_salts(
                self.config.get_table_name('salt_exclusion_list')
            )
            self.logger.info(f"Loaded {len(self.excluded_saltnames)} excluded salt names")
            
            # Initialize drug processor with excluded salts
            self.drug_processor = DrugNameProcessor(self.excluded_saltnames)
            
            # Initialize report generator
            self.report_generator = ReportGenerator(self.db, self.config, self.excel_handler)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}", exc_info=True)
            raise
    
    def _load_db_configuration(self):
        """Load configuration from database"""
        try:
            # Load base variables
            query = f"""
                SELECT name, value FROM {self.config.tables['variable_table']}
                WHERE name IN ('MTU Source Path', 'Customer Table', 'MT Sheetname', 
                              'MT Product Colname', 'Mail Configuration Table',
                              'MTU Table Names Table', 'MT Column Names Table',
                              'MT Comment Colname', 'MTU Default Remark Comment', 'MT SNo Colname')
            """
            results = self.db.execute_query(query)
            
            db_values = {row['name']: row['value'] for row in results}
            
            # Load table names
            table_query = f"""
                SELECT name, value FROM {db_values['MTU Table Names Table']}
                WHERE name IN ('process_status', 'suprocess_info', 'master_tracker_updates',
                              'overall_count_report', 'inclusion_exclusion_counts',
                              'salt_exclusion_list', 'caplin_master_report', 'bells_master_report',
                              'marksans_usa_master_report', 'relonchem_master_report',
                              'padagis_israle_master_report', 'padagis_usa_master_report', 'log_report')
                ORDER BY CASE name
                    WHEN 'process_status' THEN 1
                    WHEN 'suprocess_info' THEN 2
                    WHEN 'master_tracker_updates' THEN 3
                    WHEN 'overall_count_report' THEN 4
                    WHEN 'inclusion_exclusion_counts' THEN 5
                    WHEN 'salt_exclusion_list' THEN 6
                    WHEN 'caplin_master_report' THEN 7
                    WHEN 'bells_master_report' THEN 8
                    WHEN 'marksans_usa_master_report' THEN 9
                    WHEN 'relonchem_master_report' THEN 10
                    WHEN 'padagis_israle_master_report' THEN 11
                    WHEN 'padagis_usa_master_report' THEN 12
                    WHEN 'log_report' THEN 13
                    ELSE 14 END
            """
            table_results = self.db.execute_query(table_query)
            
            for row in table_results:
                db_values[row['name']] = row['value']
            
            # Load mail configuration
            mail_query = f"""
                SELECT name, value FROM {db_values['Mail Configuration Table']}
                WHERE name IN ('Success To Address', 'Success Cc Address', 
                              'Failure To Address', 'Failure Cc Address',
                              'Success Mail Subject', 'Failure Mai Subject',
                              'Success Mail Body', 'Failure Mail Body')
            """
            mail_results = self.db.execute_query(mail_query)
            
            for row in mail_results:
                db_values[row['name'].lower().replace(' ', '_')] = row['value']
            
            # Update config
            self.config.update_from_database(db_values)
            
            self.logger.info("Configuration loaded from database successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load database configuration: {str(e)}", exc_info=True)
            raise
    
    def _create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config.get_path('master_tracker_dirpath'),
            self.config.get_path('client_dirpath'),
            self.config.get_path('bot_outpath'),
            self.config.get_path('bot_processpath'),
            self.config.get_path('bot_processedpath'),
            self.config.get_path('bot_failedpath'),
            self.config.get_path('bot_inprogresspath')
        ]
        
        for directory in dirs:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                self.logger.info(f"Created directory: {directory}")
    
    def _validate_input_files(self) -> bool:
        """Validate that required input files exist"""
        mt_path = self.config.get_path('master_tracker_dirpath')
        client_path = self.config.get_path('client_dirpath')
        
        # Check for master tracker files
        mt_files = [f for f in os.listdir(mt_path) if f.endswith('.xlsx')] if os.path.exists(mt_path) else []
        
        # Check for client files
        client_files = []
        if os.path.exists(client_path):
            for root, dirs, files in os.walk(client_path):
                client_files.extend([f for f in files if f.endswith(('.xls', '.xlsx'))])
        
        if not mt_files or not client_files:
            return False
        
        # Set master tracker path
        self.master_tracker_path = os.path.join(mt_path, mt_files[0])
        self.logger.info(f"Found Master Tracker: {mt_files[0]}")
        self.logger.info(f"Found {len(client_files)} client files")
        
        return True
    
    def get_excluded_salt(self, product_name: str) -> str:
        """Remove excluded salts from product name"""
        return self.drug_processor.get_excluded_salt_2(product_name)
    
    def process_drug_names(self, table_name: str):
        """Process drug names - extract and clean drug information"""
        try:
            self.logger.info(f"Processing drug names from table: {table_name}")
            self.drug_processor.process_drug_names(self.db, table_name, self.process_id)
        except Exception as e:
            self.logger.error(f"Error processing drug names: {str(e)}", exc_info=True)
            raise
    
    def validate_master_tracker(self):
        """Validate Master Tracker file structure"""
        try:
            self.logger.info("Validating Master Tracker")
            self.update_status("Master Tracker Validation Initiated")
            
            # Get required column names from database
            query = f"""
                SELECT excel_colname FROM {self.config.get_table_name('mt_columnnames_table')}
                WHERE status = '1'
            """
            column_results = self.db.execute_query(query)
            column_names = [row['excel_colname'] for row in column_results]
            
            # Add product column at beginning
            product_col = self.config.master_tracker.get('product_colname', 'Product Name')
            full_colnames = [product_col] + column_names
            
            # Add comment column
            comment_col = self.config.master_tracker.get('comment_colname', 'Comment')
            full_colnames.append(comment_col)
            
            # Validate structure
            master_sheetname = self.config.master_tracker.get('sheetname', 'Master')
            is_valid, message = self.excel_handler.validate_excel_structure(
                self.master_tracker_path,
                master_sheetname,
                full_colnames
            )
            
            if not is_valid:
                error_msg = f"Wrong Master Tracker File - {message}"
                self.logger.error(error_msg)
                self.move_to_failed(error_msg)
                return False
            
            self.update_status("Master Tracker Validation Completed")
            self.logger.info("Master Tracker validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Master Tracker validation failed: {str(e)}", exc_info=True)
            self.move_to_failed(f"Validation failed: {str(e)}")
            return False
    
    def read_master_tracker(self):
        """Read and process Master Tracker data"""
        try:
            self.logger.info("Reading Master Tracker")
            
            # Get configuration
            mt_sheetname = self.config.master_tracker.get('sheetname', 'Master')
            mt_starting_row = 0  # Should be loaded from DB
            
            # Get customer column names
            query = f"""
                SELECT excel_column_name FROM {self.config.get_table_name('mt_columnnames_table')}
                WHERE status = 1 AND (is_customer = 1 OR mt_report_tableheader = 'product_name')
            """
            column_results = self.db.execute_query(query)
            pdt_and_customer_names = [row['excel_column_name'] for row in column_results]
            
            # Read Master Tracker
            mt_values = self.excel_handler.read_excel_with_clean_columns(
                self.master_tracker_path,
                mt_sheetname,
                pdt_and_customer_names,
                mt_starting_row
            )
            
            # Read synonyms if available
            synonyms_values = []
            # If synonyms sheet exists, read it
            # synonyms_values = self.excel_handler.read_excel_with_clean_columns(...)
            
            # Transform to dictionary
            customer_names = pdt_and_customer_names[1:]  # Remove product name column
            self.mt_dictval = self.mt_processor.transform_to_dict(mt_values, customer_names)
            
            # Get all drug names
            drugnames = []
            for item in self.mt_dictval:
                if 'productname' in item:
                    drugnames.extend(item['productname']['processed'])
            
            # Find synonyms
            self.collective_drugnames = self.mt_processor.find_synonyms(drugnames, synonyms_values)
            
            self.logger.info(f"Read {len(self.mt_dictval)} Master Tracker entries")
            self.logger.info(f"Total drug names (with synonyms): {len(self.collective_drugnames)}")
            
        except Exception as e:
            self.logger.error(f"Error reading Master Tracker: {str(e)}", exc_info=True)
            raise
    
    def generate_reports(self):
        """Generate all reports"""
        try:
            self.logger.info("Generating reports")
            
            # Generate overall count report
            self.report_generator.generate_overall_count_report(self.process_id)
            
            # Generate inclusion/exclusion report
            self.report_generator.generate_inclusion_exclusion_report(self.process_id)
            
            # Create Excel report file
            output_dir = os.path.join(self.config.get_path('bot_outpath'), self.process_id)
            os.makedirs(output_dir, exist_ok=True)
            
            report_filename = f"Drug_Intelligence_Report_{self.process_id}.xlsx"
            report_path = os.path.join(output_dir, report_filename)
            
            self.report_generator.create_excel_report(self.process_id, report_path)
            
            self.logger.info(f"Reports generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating reports: {str(e)}", exc_info=True)
            raise
    
    def move_to_bot_out(self):
        """Move processed files to BOT-OUT and send notifications"""
        try:
            self.logger.info("Moving to BOT-OUT")
            
            # Get completed and failed files
            completed_query = f"""
                SELECT customer_name, filename 
                FROM {self.config.get_table_name('log_report')}
                WHERE completed_sts = '1' AND process_id = '{self.process_id}'
            """
            completed_files = self.db.execute_query(completed_query)
            
            failed_query = f"""
                SELECT customer_name, filename, failure_message
                FROM {self.config.get_table_name('log_report')}
                WHERE failed_sts = '1' AND process_id = '{self.process_id}'
            """
            failed_files = self.db.execute_query(failed_query)
            
            # If only failures, move to failed
            if not completed_files and failed_files:
                error_msg = "Below files failed during processing:\\n\\n"
                for idx, file in enumerate(failed_files):
                    error_msg += f"{idx + 1}) {file['customer_name']} - {file['filename']}\\n"
                self.move_to_failed(error_msg)
                return
            
            # Move master tracker to output
            di_output_dir = os.path.join(self.config.get_path('bot_outpath'), self.process_id)
            os.makedirs(di_output_dir, exist_ok=True)
            
            dest_mt_path = os.path.join(di_output_dir, os.path.basename(self.master_tracker_path))
            shutil.move(self.master_tracker_path, dest_mt_path)
            
            # Collect report files
            attachments = []
            for filename in os.listdir(di_output_dir):
                if filename.endswith('.xlsx') and 'Conflict' not in filename:
                    attachments.append(os.path.join(di_output_dir, filename))
            
            # Send success email
            success_list = [(f['customer_name'], f['filename']) for f in completed_files]
            failed_list = [(f['customer_name'], f['filename'], f.get('failure_message', '')) for f in failed_files]
            
            self.email_sender.send_success_email(
                self.config.mail_settings['success_to_address'],
                self.config.mail_settings['success_cc_address'],
                self.config.mail_settings['success_mail_subject'],
                self.config.mail_settings['success_mail_body'],
                success_list,
                failed_list,
                attachments
            )
            
            # Clean in-progress directory
            inprogress_path = self.config.get_path('bot_inprogresspath')
            for item in os.listdir(inprogress_path):
                item_path = os.path.join(inprogress_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            self.logger.info("Successfully moved to BOT-OUT and sent notifications")
            
        except Exception as e:
            self.logger.error(f"Error moving to BOT-OUT: {str(e)}", exc_info=True)
            raise
    
    def move_to_failed(self, error_message: str):
        """Move files to failed folder and send failure notification"""
        try:
            self.logger.error(f"Moving to FAILED: {error_message}")
            
            # Create failed directory
            failed_dir = self.config.get_path('bot_failedpath')
            os.makedirs(failed_dir, exist_ok=True)
            
            # Move master tracker
            if os.path.exists(self.master_tracker_path):
                dest_path = os.path.join(failed_dir, os.path.basename(self.master_tracker_path))
                shutil.move(self.master_tracker_path, dest_path)
            
            # Move output directory if exists
            output_dir = os.path.join(self.config.get_path('bot_outpath'), self.process_id)
            if os.path.exists(output_dir):
                failed_output = os.path.join(failed_dir, self.process_id)
                shutil.move(output_dir, failed_output)
            
            # Update status
            self.db.update_process_status(
                self.config.get_table_name('process_status'),
                self.process_id,
                'Failed',
                error_message
            )
            
            # Send failure email
            filename = os.path.basename(self.master_tracker_path) if self.master_tracker_path else 'Unknown'
            attachment = os.path.join(failed_dir, filename) if os.path.exists(os.path.join(failed_dir, filename)) else None
            
            self.email_sender.send_failure_email(
                self.config.mail_settings['failure_to_address'],
                self.config.mail_settings['failure_cc_address'],
                self.config.mail_settings['failure_mail_subject'],
                self.config.mail_settings['failure_mail_body'],
                self.process_id,
                filename,
                error_message,
                attachment
            )
            
            self.logger.info("Moved to FAILED and sent notification")
            
        except Exception as e:
            self.logger.error(f"Error moving to failed: {str(e)}", exc_info=True)
    
    def move_to_inprogress(self):
        """Move master tracker to in-progress folder"""
        try:
            # Insert process status
            query = f"""
                INSERT INTO {self.config.get_table_name('process_status')}
                (process_status, mt_filename, start_datetime)
                VALUES ('Initiated', %s, NOW())
            """
            mt_filename = os.path.basename(self.master_tracker_path)
            self.db.execute_insert(query, (mt_filename,))
            
            # Get process ID
            self.process_id = self.db.get_max_id(
                self.config.get_table_name('process_status'),
                'process_id'
            )
            
            self.logger.info(f"Created process with ID: {self.process_id}")
            
            # Move file to in-progress
    
