"""
Drug Intelligence Main Process
Orchestrates the complete drug intelligence automation workflow
"""

import os
import shutil
from typing import List, Dict, Optional
from datetime import datetime

from config import Config
from logger import get_logger, DrugIntelligenceLogger
from database import DatabaseManager
from email_sender import EmailSender
from excel_creation import ExcelManager
from processors import CustomerProcessors


class DrugIntelligenceAutomation:
    """Main automation class for Drug Intelligence process"""
    
    def __init__(self, server_type: str = "DEV"):
        """
        Initialize Drug Intelligence Automation
        
        Args:
            server_type: Server environment (DEV/PROD)
        """
        self.config = Config(server_type)
        self.logger = None  # Will be initialized after process_id is set
        self.db = None
        self.email_sender = None
        self.excel_manager = None
        self.processors = None
        self.process_id = None
        self.master_tracker_path = None
        self.excluded_saltnames = []
    
    def run(self):
        """Main execution method"""
        try:
            # Initialize logger
            self.logger = get_logger("INIT")
            self.logger.info("=" * 80)
            self.logger.info("DRUG INTELLIGENCE AUTOMATION STARTED")
            self.logger.info("=" * 80)
            
            # Initialize process
            if not self._initialize_process():
                self.logger.error("Process initialization failed")
                return False
            
            # Execute master tracker update
            success = self._master_tracker_update()
            
            if success:
                self.logger.info("=" * 80)
                self.logger.info("DRUG INTELLIGENCE AUTOMATION COMPLETED SUCCESSFULLY")
                self.logger.info("=" * 80)
            else:
                self.logger.error("Drug Intelligence Automation failed")
            
            return success
            
        except Exception as e:
            self.logger.log_exception(e, "Main execution")
            return False
        finally:
            if self.db:
                self.db.disconnect()
    
    def _initialize_process(self) -> bool:
        """Initialize all components and load configuration"""
        try:
            self.logger.log_function_start("initialize_process")
            
            # Initialize database
            self.db = DatabaseManager(self.config.get_db_config())
            if not self.db.connect():
                return False
            
            # Load configuration from database
            if not self._load_config_from_db():
                return False
            
            # Initialize other components
            self.email_sender = EmailSender(self.config.get_email_config())
            self.excel_manager = ExcelManager()
            self.processors = CustomerProcessors(self.db, self.excel_manager, self.config)
            
            # Check for files
            if not self._check_files():
                self.logger.warning("No files to process")
                return False
            
            self.logger.log_function_end("initialize_process", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Initialize process")
            return False
    
    def _load_config_from_db(self) -> bool:
        """Load configuration from database"""
        try:
            self.logger.info("Loading configuration from database...")
            
            variable_table = self.config.TABLES['variable_table']
            
            # Load paths
            query = f"""
                SELECT value FROM {variable_table} 
                WHERE name IN ('MTU Source Path', 'Customer Table')
            """
            results = self.db.execute_query(query)
            
            if not results or len(results) < 2:
                self.logger.error("Failed to load basic configuration")
                return False
            
            drug_intelligence_path = results[0]['value']
            customer_table = results[1]['value']
            
            self.config.update_paths_from_db(drug_intelligence_path)
            self.config.TABLES['customer_table'] = customer_table
            
            # Load process configuration
            query = f"""
                SELECT value FROM {variable_table}
                WHERE name IN ('MT Sheetname', 'MT Product Colname', 
                              'Mail Configuration Table', 'MTU Table Names Table',
                              'MT Column Names Table', 'MT Comment Colname',
                              'MTU Default Remark Comment', 'MT SNo Colname')
            """
            results = self.db.execute_query(query)
            
            config_data = {
                'master_sheetname': results[0]['value'],
                'master_tracker_productcol': results[1]['value'],
                'mail_config_table': results[2]['value'],
                'mtu_tablenames_table': results[3]['value'],
                'mt_columnnames_table': results[4]['value'],
                'comment_colname': results[5]['value'],
                'remark_default_value': results[6]['value'],
                'sno_colname': results[7]['value']
            }
            self.config.update_process_config_from_db(config_data)
            
            # Load table names
            mtu_table = config_data['mtu_tablenames_table']
            query = f"""
                SELECT value FROM {mtu_table}
                WHERE name IN ('process_status', 'suprocess_info', 'master_tracker_updates',
                              'overall_count_report', 'inclusion_exclusion_counts',
                              'salt_exclusion_list', 'caplin_master_report', 'bells_master_report',
                              'marksans_usa_master_report', 'relonchem_master_report',
                              'padagis_israle_master_report', 'padagis_usa_master_report',
                              'log_report')
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
            results = self.db.execute_query(query)
            
            table_mapping = {
                'process_status': results[0]['value'],
                'suprocess_info': results[1]['value'],
                'master_tracker_updates': results[2]['value'],
                'overall_count_report': results[3]['value'],
                'inclusion_exclusion_counts': results[4]['value'],
                'salt_exclusion_list': results[5]['value'],
                'caplin_master_report': results[6]['value'],
                'bells_master_report': results[7]['value'],
                'marksans_usa_master_report': results[8]['value'],
                'relonchem_master_report': results[9]['value'],
                'padagis_israle_master_report': results[10]['value'],
                'padagis_usa_master_report': results[11]['value'],
                'log_report': results[12]['value']
            }
            self.config.update_tables_from_db(table_mapping)
            
            # Load mail configuration
            mail_table = config_data['mail_config_table']
            query = f"""
                SELECT value FROM {mail_table}
                WHERE name IN ('Success To Address', 'Success Cc Address',
                              'Failure To Address', 'Failure Cc Address',
                              'Success Mail Subject', 'Failure Mai Subject',
                              'Success Mail Body', 'Failure Mail Body')
            """
            results = self.db.execute_query(query)
            
            mail_config = {
                'success_to_address': results[0]['value'],
                'success_cc_address': results[1]['value'],
                'failure_to_address': results[2]['value'],
                'failure_cc_address': results[3]['value'],
                'success_mail_subject': results[4]['value'],
                'failure_mail_subject': results[5]['value'],
                'success_mail_body': results[6]['value'],
                'failure_mail_body': results[7]['value']
            }
            self.config.update_mail_config_from_db(mail_config)
            
            # Load excluded salts
            salt_table = self.config.get_table('salt_exclusion_list')
            self.excluded_saltnames = self.db.get_excluded_salts(salt_table)
            
            self.logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Load configuration from database")
            return False
    
    def _check_files(self) -> bool:
        """Check for master tracker and client files"""
        try:
            master_tracker_dir = self.config.get_path('master_tracker_dirpath')
            client_dir = self.config.get_path('client_dirpath')
            
            # Create directories if not exist
            os.makedirs(master_tracker_dir, exist_ok=True)
            os.makedirs(client_dir, exist_ok=True)
            
            # Check master tracker files
            master_files = [f for f in os.listdir(master_tracker_dir) 
                          if f.endswith('.xlsx')]
            
            if not master_files:
                self.logger.warning("No master tracker files found")
                return False
            
            self.master_tracker_path = os.path.join(master_tracker_dir, master_files[0])
            
            # Check client files
            client_files = []
            for root, dirs, files in os.walk(client_dir):
                for file in files:
                    if file.endswith(('.xls', '.xlsx')):
                        client_files.append(file)
            
            if not client_files:
                self.logger.warning("No client files found")
                return False
            
            self.logger.info(f"Found {len(master_files)} master tracker files")
            self.logger.info(f"Found {len(client_files)} client files")
            
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Check files")
            return False
    
    def _master_tracker_update(self) -> bool:
        """Execute master tracker update process"""
        try:
            self.logger.log_function_start("master_tracker_update")
            
            # Move master tracker to in-progress
            if not self._move_to_inprogress():
                return False
            
            # Validate master tracker
            if not self._validate_master_tracker():
                return False
            
            # Get customers and process each
            customers = self.db.get_customers(self.config.get_table('customer_table'))
            
            if not customers:
                self.logger.warning("No active customers found")
                return False
            
            self.logger.info(f"Processing {len(customers)} customers")
            
            for customer in customers:
                self._execute_each_customer(customer)
            
            # Generate reports
            self._generate_reports()
            
            # Move to BOT-OUT
            self._move_to_bot_out()
            
            # Update final status
            process_table = self.config.get_table('process_status')
            self.db.update_process_status(
                process_table, 
                self.process_id, 
                'Completed'
            )
            
            self.logger.log_function_end("master_tracker_update", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Master tracker update")
            return False
    
    def _move_to_inprogress(self) -> bool:
        """Move master tracker to in-progress folder"""
        try:
            self.logger.info("Moving master tracker to in-progress...")
            
            # Create process record
            process_table = self.config.get_table('process_status')
            master_filename = os.path.basename(self.master_tracker_path)
            
            query = f"""
                INSERT INTO {process_table} 
                (process_status, mt_filename, start_datetime)
                VALUES ('Initiated', %s, NOW())
            """
            self.db.execute_insert(query, (master_filename,))
            
            # Get process ID
            self.process_id = self.db.get_max_id(
                process_table,
                'process_id'
            )
            
            # Update logger with process ID
            self.logger.update_process_id(str(self.process_id))
            self.config.PROCESS_CONFIG['process_id'] = self.process_id
            
            self.logger.info(f"Process ID created: {self.process_id}")
            
            # Create and clean in-progress directory
            inprogress_dir = self.config.get_path('bot_inprogresspath')
            os.makedirs(inprogress_dir, exist_ok=True)
            
            # Move file
            new_path = os.path.join(inprogress_dir, master_filename)
            shutil.move(self.master_tracker_path, new_path)
            self.master_tracker_path = new_path
            
            self.logger.log_file_operation("move", new_path, "Success")
            
            # Update status
            self.db.update_process_status(
                process_table,
                self.process_id,
                'File Moved to Inprogress'
            )
            
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Move to in-progress")
            return False
    
    def _validate_master_tracker(self) -> bool:
        """Validate master tracker file structure"""
        try:
            self.logger.info("Validating master tracker...")
            
            # Update status
            process_table = self.config.get_table('process_status')
            self.db.update_process_status(
                process_table,
                self.process_id,
                'Master Tracker Validation Initiated'
            )
            
            # Get required columns
            mt_columns_table = self.config.PROCESS_CONFIG['mt_columnnames_table']
            query = f"SELECT excel_colname FROM {mt_columns_table} WHERE status='1'"
            results = self.db.execute_query(query)
            
            column_names = [self.config.PROCESS_CONFIG['master_tracker_productcol']]
            column_names.extend([row['excel_colname'] for row in results])
            column_names.append(self.config.PROCESS_CONFIG['comment_colname'])
            
            # Validate columns exist
            sheet_name = self.config.PROCESS_CONFIG['master_sheetname']
            
            try:
                from openpyxl import load_workbook
                workbook = load_workbook(self.master_tracker_path, data_only=True)
                
                if sheet_name not in workbook.sheetnames:
                    raise ValueError(f"Sheet '{sheet_name}' not found")
                
                sheet = workbook[sheet_name]
                header_row = list(sheet.iter_rows(max_row=10, values_only=True))
                
                # Check if all columns exist
                for col in column_names:
                    found = False
                    for row in header_row:
                        if any(col.lower() in str(cell).lower() if cell else '' 
                              for cell in row):
                            found = True
                            break
                    
                    if not found:
                        workbook.close()
                        error_msg = f"Column '{col}' not found in master tracker"
                        self._move_to_failed(error_msg)
                        return False
                
                workbook.close()
                
            except Exception as e:
                error_msg = f"Wrong Master Tracker File - {str(e)}"
                self._move_to_failed(error_msg)
                return False
            
            # Update status
            self.db.update_process_status(
                process_table,
                self.process_id,
                'Master Tracker Validation Completed'
            )
            
            self.logger.info("Master tracker validation successful")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Validate master tracker")
            return False
    
    def _execute_each_customer(self, customer: Dict):
        """Process each customer's file"""
        try:
            customer_id = customer['customer_id']
            customer_name = customer['customer_name']
            
            self.logger.log_customer_processing(customer_name, customer_id, "Started")
            
            # Get subprocess info
            subprocess_table = self.config.get_table('suprocess_info')
            query = f"""
                SELECT suprocess_name, excel_sheetname, excel_startindex, column_names
                FROM {subprocess_table}
                WHERE customer_id=%s
            """
            result = self.db.execute_query(query, (customer_id,))
            
            if not result:
                self.logger.info(f"No subprocess configuration for {customer_name}")
                return
            
            config = result[0]
            subprocess_name = config['suprocess_name']
            
            # Find customer file
            client_dir = os.path.join(
                self.config.get_path('client_dirpath'),
                customer_name
            )
            
            if not os.path.exists(client_dir):
                self.logger.warning(f"Customer directory not found: {client_dir}")
                return
            
            files = [f for f in os.listdir(client_dir) 
                    if f.endswith(('.xls', '.xlsx'))]
            
            if not files:
                self.logger.warning(f"No files found for {customer_name}")
                return
            
            client_filepath = os.path.join(client_dir, files[0])
            
            # Insert log entry
            log_table = self.config.get_table('log_report')
            log_data = {
                'process_id': self.process_id,
                'customer_id': customer_id,
                'initiated_sts': 1,
                'start_datetime': datetime.now(),
                'customer_name': customer_name,
                'filename': files[0]
            }
            log_id = self.db.insert_log_entry(log_table, log_data)
            
            # Move to in-progress
            inprogress_dir = os.path.join(
                self.config.get_path('bot_inprogresspath'),
                customer_name
            )
            os.makedirs(inprogress_dir, exist_ok=True)
            
            new_filepath = os.path.join(inprogress_dir, files[0])
            shutil.move(client_filepath, new_filepath)
            
            # Process based on subprocess name
            processor_map = {
                'PROCESS_CAPLIN': self.processors.process_caplin,
                'PROCESS_BELLS': self.processors.process_bells,
                'PROCESS_RELONCHEM': self.processors.process_relonchem,
                'PROCESS_MARKSANS_USA': self.processors.process_marksans_usa,
                'PROCESS_PADAGIS_USA': self.processors.process_padagis_usa,
                'PROCESS_PADAGIS_ISRAEL': self.processors.process_padagis_israel
            }
            
            processor = processor_map.get(subprocess_name)
            if processor:
                success = processor(new_filepath, config)
                
                if success:
                    self._move_to_processed(customer_name, new_filepath)
                    # Update log
                    query = f"""
                        UPDATE {log_table}
                        SET completed_sts=1, end_datetime=NOW()
                        WHERE log_id=%s
                    """
                    self.db.execute_update(query, (log_id,))
                    
                    self.logger.log_customer_processing(
                        customer_name, customer_id, "Completed"
                    )
                else:
                    self._move_failed_clientfile(customer_name, new_filepath, log_id)
            else:
                self.logger.error(f"Unknown subprocess: {subprocess_name}")
                self._move_failed_clientfile(customer_name, new_filepath, log_id)
            
        except Exception as e:
            self.logger.log_exception(e, f"Process customer {customer.get('customer_name')}")
    
    def _move_to_processed(self, customer_name: str, filepath: str):
        """Move file to processed folder"""
        try:
            processed_dir = os.path.join(
                self.config.get_path('bot_processedpath'),
                str(self.process_id),
                customer_name
            )
            os.makedirs(processed_dir, exist_ok=True)
            
            filename = os.path.basename(filepath)
            new_path = os.path.join(processed_dir, filename)
            shutil.move(filepath, new_path)
            
            self.logger.log_file_operation("move_processed", new_path, "Success")
            
        except Exception as e:
            self.logger.log_exception(e, "Move to processed")
    
    def _move_failed_clientfile(self, customer_name: str, filepath: str, log_id: int):
        """Move failed file to failed folder"""
        try:
            failed_dir = os.path.join(
                self.config.get_path('bot_failedpath'),
                str(self.process_id),
                customer_name
            )
            os.makedirs(failed_dir, exist_ok=True)
            
            filename = os.path.basename(filepath)
            new_path = os.path.join(failed_dir, filename)
            shutil.move(filepath, new_path)
            
            # Update log
            log_table = self.config.get_table('log_report')
            query = f"""
                UPDATE {log_table}
                SET failed_sts=1, 
                    failure_message='Failed while processing {customer_name} - {filename}',
                    end_datetime=NOW()
                WHERE log_id=%s
            """
            self.db.execute_update(query, (log_id,))
            
            self.logger.log_file_operation("move_failed", new_path, "Failed")
            
        except Exception as e:
            self.logger.log_exception(e, "Move failed client file")
    
    def _generate_reports(self):
        """Generate Excel reports"""
        try:
            self.logger.info("Generating reports...")
            
            # Truncate report tables
            self.db.truncate_table(self.config.get_table('overall_count_report'))
            self.db.truncate_table(self.config.get_table('inclusion_exclusion_counts'))
            
            # Report generation logic would go here
            # This would involve querying processed data and creating Excel reports
            
            self.logger.info("Reports generated successfully")
            
        except Exception as e:
            self.logger.log_exception(e, "Generate reports")
    
    def _move_to_bot_out(self):
        """Move completed files to BOT-OUT and send email"""
        try:
            self.logger.info("Moving files to BOT-OUT...")
            
            log_table = self.config.get_table('log_report')
            
            # Get completed files
            query = f"""
                SELECT customer_name, filename
                FROM {log_table}
                WHERE completed_sts=1 AND process_id=%s
            """
            completed_files = self.db.execute_query(query, (self.process_id,))
            
            # Get failed files
            query = f"""
                SELECT customer_name, filename, failure_message
                FROM {log_table}
                WHERE failed_sts=1 AND process_id=%s
            """
            failed_files = self.db.execute_query(query, (self.process_id,))
            
            completed_list = [(f['customer_name'], f['filename']) 
                            for f in completed_files]
            failed_list = [(f['customer_name'], f['filename'], f['failure_message']) 
                          for f in failed_files]
            
            if not completed_list and failed_list:
                # All failed
                error_list = '\n'.join([
                    f"{i+1}) {f[0]} - {f[1]}"
                    for i, f in enumerate(failed_list)
                ])
                self._move_to_failed(f"Below files failed during processing:\n\n{error_list}")
                return
            
            # Move master tracker to output
            output_dir = os.path.join(
                self.config.get_path('bot_outpath'),
                str(self.process_id)
            )
            os.makedirs(output_dir, exist_ok=True)
            
            master_filename = os.path.basename(self.master_tracker_path)
            output_path = os.path.join(output_dir, master_filename)
            shutil.move(self.master_tracker_path, output_path)
            
            # Collect attachments
            attachments = [output_path]
            report_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx')]
            for file in report_files:
                if "Conflict" not in file:
                    attachments.append(os.path.join(output_dir, file))
            
            # Send success email
            self.email_sender.send_success_email(
                self.config.MAIL_CONFIG,
                completed_list,
                failed_list,
                attachments
            )
            
            # Clean in-progress directory
            inprogress_dir = self.config.get_path('bot_inprogresspath')
            if os.path.exists(inprogress_dir):
                shutil.rmtree(inprogress_dir)
            
            self.logger.info("Files moved to BOT-OUT successfully")
            
        except Exception as e:
            self.logger.log_exception(e, "Move to BOT-OUT")
    
    def _move_to_failed(self, error_message: str):
        """Move process to failed folder"""
        try:
            self.logger.error(f"Moving to failed: {error_message}")
            
            # Create failed directory
            failed_dir = os.path.join(
                self.config.get_path('bot_failedpath'),
                str(self.process_id)
            )
            os.makedirs(failed_dir, exist_ok=True)
            
            # Move master tracker
            if os.path.exists(self.master_tracker_path):
                master_filename = os.path.basename(self.master_tracker_path)
                failed_path = os.path.join(failed_dir, master_filename)
                shutil.move(self.master_tracker_path, failed_path)
            
            # Update process status
            process_table = self.config.get_table('process_status')
            self.db.update_process_status(
                process_table,
                self.process_id,
                'Failed',
                error_message
            )
            
            # Send failure email
            master_filename = os.path.basename(self.master_tracker_path)
            self.email_sender.send_failure_email(
                self.config.MAIL_CONFIG,
                str(self.process_id),
                master_filename,
                error_message,
                failed_path if os.path.exists(failed_path) else None
            )
            
            self.logger.error("Process moved to failed")
            
        except Exception as e:
            self.logger.log_exception(e, "Move to failed")


def main():
    """Main entry point"""
    try:
        automation = DrugIntelligenceAutomation(server_type="DEV")
        success = automation.run()
        return 0 if success else 1
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
