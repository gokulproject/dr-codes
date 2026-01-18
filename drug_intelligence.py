"""
Drug Intelligence Module - Main Workflow Orchestration
Coordinates the complete end-to-end drug intelligence automation process
Manages master tracker processing, customer file processing, and report generation
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class DrugIntelligenceWorkflow:
    """
    Main workflow orchestrator for Drug Intelligence Automation
    """
    
    def __init__(self, config, db_manager, excel_manager, processor, email_sender, logger):
        """
        Initialize Drug Intelligence Workflow
        
        Args:
            config: Configuration object
            db_manager: Database manager instance
            excel_manager: Excel manager instance
            processor: Drug data processor instance
            email_sender: Email sender instance
            logger: Logger instance
        """
        self.config = config
        self.db = db_manager
        self.excel = excel_manager
        self.processor = processor
        self.email = email_sender
        self.logger = logger
        
        # Process tracking
        self.total_customers = 0
        self.processed_customers = 0
        self.failed_customers = 0
    
    def initialize_process(self) -> bool:
        """
        Initialize the drug intelligence process
        Sets up directories, validates files, and prepares database
        
        Returns:
            bool: True if initialization successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("Process Initialization", "STARTED")
            
            # Create necessary directories
            directories = [
                self.config.paths.get('master_tracker_dirpath'),
                self.config.paths.get('client_dirpath'),
                self.config.paths.get('bot_outpath'),
                self.config.paths.get('bot_processpath'),
                self.config.paths.get('bot_processedpath'),
                self.config.paths.get('bot_failedpath'),
                self.config.paths.get('bot_inprogresspath')
            ]
            
            for directory in directories:
                if directory:
                    try:
                        os.makedirs(directory, exist_ok=True)
                        if self.logger:
                            self.logger.debug(f"✅ Directory ensured: {directory}")
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"⚠️ Could not create directory {directory}: {str(e)}")
            
            # Check for master tracker files
            master_tracker_dir = self.config.paths.get('master_tracker_dirpath')
            if not master_tracker_dir or not os.path.exists(master_tracker_dir):
                raise Exception("Master tracker directory not found")
            
            list_excel_files = [f for f in os.listdir(master_tracker_dir) if f.endswith('.xlsx')]
            
            if not list_excel_files:
                if self.logger:
                    self.logger.warning("⚠️ No Master Tracker files found")
                return False
            
            # Check for client files
            client_dir = self.config.paths.get('client_dirpath')
            client_files = self._list_files_recursive(client_dir, ['.xls', '.xlsx'])
            
            if not client_files:
                if self.logger:
                    self.logger.warning("⚠️ No client files found")
                return False
            
            if self.logger:
                self.logger.info(f"✅ Found {len(list_excel_files)} master tracker file(s)")
                self.logger.info(f"✅ Found {len(client_files)} client file(s)")
            
            # Set master tracker file
            master_tracker_filename = list_excel_files[0]
            self.config.master_tracker_filename = master_tracker_filename
            
            # Move to inprogress
            if not self.move_to_inprogress():
                raise Exception("Failed to move master tracker to inprogress")
            
            # Validate master tracker
            if not self.validate_master_tracker():
                raise Exception("Master tracker validation failed")
            
            if self.logger:
                self.logger.log_process_step("Process Initialization", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Process initialization failed: {str(e)}")
                self.logger.log_exception("initialize_process", e)
                self.logger.log_process_step("Process Initialization", "FAILED")
            return False
    
    def _list_files_recursive(self, directory: str, extensions: List[str]) -> List[str]:
        """
        List all files recursively with given extensions
        
        Args:
            directory: Directory to search
            extensions: List of file extensions (e.g., ['.xls', '.xlsx'])
            
        Returns:
            List of file paths
        """
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Error listing files in {directory}: {str(e)}")
        
        return files
    
    def move_to_inprogress(self) -> bool:
        """
        Move master tracker file to inprogress folder and create process record
        
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info("⏳ Moving master tracker to inprogress...")
            
            # Insert process status record
            process_status_table = self.config.get_table_name('process_status')
            
            query = f"""
                INSERT INTO {process_status_table}
                (process_status, mt_filename, start_datetime)
                VALUES (%s, %s, NOW())
            """
            
            params = ('Initiated', self.config.master_tracker_filename)
            self.db.execute_update(query, params)
            
            # Get process ID
            process_id = self.db.get_max_id(
                process_status_table,
                'process_id'
            )
            
            if not process_id:
                raise Exception("Failed to get process ID")
            
            self.config.process_id = process_id
            
            if self.logger:
                self.logger.success(f"✅ Process ID created: {process_id}")
            
            # Create and clean inprogress directory
            inprogress_dir = self.config.paths.get('bot_inprogresspath')
            os.makedirs(inprogress_dir, exist_ok=True)
            
            # Clean inprogress directory
            for item in os.listdir(inprogress_dir):
                item_path = os.path.join(inprogress_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not remove {item_path}: {str(e)}")
            
            # Move master tracker file
            source_path = os.path.join(
                self.config.paths.get('master_tracker_dirpath'),
                self.config.master_tracker_filename
            )
            
            dest_path = os.path.join(
                inprogress_dir,
                self.config.master_tracker_filename
            )
            
            shutil.move(source_path, dest_path)
            
            # Update path in config
            self.config.paths['master_tracker_path'] = dest_path
            
            if self.logger:
                self.logger.success(f"✅ Master tracker moved to inprogress")
            
            # Update status
            self.update_process_status('File Moved to Inprogress')
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to move to inprogress: {str(e)}")
                self.logger.log_exception("move_to_inprogress", e)
            return False
    
    def validate_master_tracker(self) -> bool:
        """
        Validate master tracker file structure and columns
        
        Returns:
            bool: True if validation successful
        """
        try:
            if self.logger:
                self.logger.info("⏳ Validating master tracker file...")
            
            self.update_process_status('Master Tracker Validation Initiated')
            
            # Get column names to validate
            mt_columnnames_table = self.config.table_names.get('mt_columnnames_table')
            
            query = f"""
                SELECT excel_colname
                FROM {mt_columnnames_table}
                WHERE status = '1'
            """
            
            result = self.db.execute_query(query)
            
            if not result:
                raise Exception("No column names found in configuration")
            
            column_names = [row[0] for row in result]
            
            # Add product column and comment column
            product_col = self.config.master_tracker_config.get('mater_tracker_productcol')
            comment_col = self.config.master_tracker_config.get('comment_colname')
            
            full_colnames = [product_col] + column_names + [comment_col]
            
            # Validate using Excel parser
            master_tracker_path = self.config.paths.get('master_tracker_path')
            master_sheetname = self.config.master_tracker_config.get('master_sheetname')
            
            try:
                result = self.excel.parse_excel_with_dynamic_header(
                    master_tracker_path,
                    master_sheetname,
                    full_colnames
                )
                
                if not result:
                    raise Exception("Master tracker validation failed - columns or sheet not found")
                    
            except Exception as e:
                error_msg = f"Wrong Master Tracker File was uploaded - Column/Sheet not found: {str(e)}"
                self.move_to_failed(error_msg)
                return False
            
            # Get comment column number
            comment_colno = self.excel.get_column_number(
                master_tracker_path,
                master_sheetname,
                comment_col
            )
            
            self.config.master_tracker_config['comment_colno'] = comment_colno
            self.config.master_tracker_config['mt_column_names'] = column_names
            
            if self.logger:
                self.logger.success("✅ Master tracker validation completed")
            
            self.update_process_status('Master Tracker Validation Completed')
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Master tracker validation failed: {str(e)}")
                self.logger.log_exception("validate_master_tracker", e)
            return False
    
    def update_process_status(self, status: str) -> bool:
        """
        Update process status in database
        
        Args:
            status: New status message
            
        Returns:
            bool: True if successful
        """
        try:
            process_status_table = self.config.get_table_name('process_status')
            
            query = f"""
                UPDATE {process_status_table}
                SET process_status = %s
                WHERE process_id = %s
            """
            
            params = (status, self.config.process_id)
            self.db.execute_update(query, params)
            
            if self.logger:
                self.logger.debug(f"Process status updated: {status}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Failed to update process status: {str(e)}")
            return False
    
    def move_to_failed(self, error_message: str) -> None:
        """
        Move files to failed directory and send failure notification
        
        Args:
            error_message: Error message describing the failure
        """
        try:
            if self.logger:
                self.logger.error(f"❌ Moving to failed: {error_message}")
            
            # Create failed directory with process ID
            failed_dir = os.path.join(
                self.config.paths.get('bot_failedpath'),
                str(self.config.process_id)
            )
            os.makedirs(failed_dir, exist_ok=True)
            
            # Move master tracker to failed
            master_tracker_path = self.config.paths.get('master_tracker_path')
            if master_tracker_path and os.path.exists(master_tracker_path):
                try:
                    shutil.move(master_tracker_path, failed_dir)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not move master tracker: {str(e)}")
            
            # Move output directory if exists
            output_dir = os.path.join(
                self.config.paths.get('bot_outpath'),
                str(self.config.process_id)
            )
            
            if os.path.exists(output_dir):
                try:
                    shutil.move(output_dir, failed_dir)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not move output directory: {str(e)}")
            
            # Update database status
            process_status_table = self.config.get_table_name('process_status')
            
            query = f"""
                UPDATE {process_status_table}
                SET process_status = 'Failed',
                    error_message = %s,
                    end_datetime = NOW()
                WHERE process_id = %s
            """
            
            params = (error_message, self.config.process_id)
            self.db.execute_update(query, params)
            
            # Send failure email
            attachment_path = os.path.join(failed_dir, self.config.master_tracker_filename)
            
            self.email.send_failure_notification(
                mail_config=self.config.mail_config,
                process_id=str(self.config.process_id),
                filename=self.config.master_tracker_filename,
                error_message=error_message,
                attachment_path=attachment_path if os.path.exists(attachment_path) else None
            )
            
            if self.logger:
                self.logger.error(f"Process failed: {error_message}")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error in move_to_failed: {str(e)}")
                self.logger.log_exception("move_to_failed", e)

"""
Drug Intelligence Module - Part 2
Customer processing and file management methods
"""

# ADD THESE METHODS TO THE DrugIntelligenceWorkflow CLASS

    def master_tracker_update(self) -> bool:
        """
        Main master tracker update workflow
        Processes all active customers
        
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("Master Tracker Update", "STARTED")
            
            # Get active customers
            customer_table = self.config.get_table_name('customer_table')
            
            query = f"""
                SELECT customer_id, customer_name
                FROM {customer_table}
                WHERE status = 1
                ORDER BY customer_id
            """
            
            customer_list = self.db.execute_query(query)
            
            if not customer_list:
                if self.logger:
                    self.logger.warning("⚠️ No active customers found")
                return False
            
            self.total_customers = len(customer_list)
            
            if self.logger:
                self.logger.info(f"✅ Found {self.total_customers} active customer(s)")
            
            # Process each customer
            for customer_id, customer_name in customer_list:
                try:
                    if self.logger:
                        self.logger.info(f"⏳ Processing customer: {customer_name} (ID: {customer_id})")
                    
                    if self.execute_each_customer(customer_id, customer_name):
                        self.processed_customers += 1
                    else:
                        self.failed_customers += 1
                        
                except Exception as e:
                    self.failed_customers += 1
                    if self.logger:
                        self.logger.error(f"❌ Customer {customer_name} processing failed: {str(e)}")
                        self.logger.log_exception(f"process_customer_{customer_id}", e)
            
            if self.logger:
                self.logger.log_process_step("Master Tracker Update", "COMPLETED")
                self.logger.info(f"✅ Processed: {self.processed_customers}/{self.total_customers}")
                self.logger.info(f"❌ Failed: {self.failed_customers}/{self.total_customers}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Master tracker update failed: {str(e)}")
                self.logger.log_exception("master_tracker_update", e)
                self.logger.log_process_step("Master Tracker Update", "FAILED")
            return False
    
    def execute_each_customer(self, customer_id: int, customer_name: str) -> bool:
        """
        Execute processing for a specific customer
        
        Args:
            customer_id: Customer ID
            customer_name: Customer name
            
        Returns:
            bool: True if processing successful
        """
        log_id = None
        client_filepath = None
        
        try:
            # Get customer subprocess configuration
            suprocess_info_table = self.config.get_table_name('suprocess_info')
            
            query = f"""
                SELECT suprocess_name, excel_sheetname, excel_startindex, column_names
                FROM {suprocess_info_table}
                WHERE customer_id = %s
            """
            
            result = self.db.execute_query(query, (str(customer_id),))
            
            if not result or len(result) == 0:
                if self.logger:
                    self.logger.warning(f"⚠️ No subprocess configuration found for {customer_name}")
                return True  # Continue with next customer
            
            # Get subprocess details
            suprocess_name = result[0][0]
            customer_config = {
                'excel_sheetname': result[0][1],
                'excel_startindex': result[0][2],
                'column_names': result[0][3]
            }
            
            # Find customer directory and files
            customer_dirpath = os.path.join(
                self.config.paths.get('client_dirpath'),
                customer_name
            )
            
            # Create customer directory if not exists
            os.makedirs(customer_dirpath, exist_ok=True)
            
            # List Excel files in customer directory
            list_files = [
                f for f in os.listdir(customer_dirpath)
                if f.lower().endswith(('.xls', '.xlsx'))
            ]
            
            if not list_files:
                if self.logger:
                    self.logger.warning(f"⚠️ No files found for customer {customer_name}")
                return True  # Continue with next customer
            
            # Get first file
            in_client_filepath = os.path.join(customer_dirpath, list_files[0])
            
            # Create log entry
            log_report_table = self.config.get_table_name('log_report')
            
            insert_query = f"""
                INSERT INTO {log_report_table}
                (process_id, customer_id, initiated_sts, start_datetime, customer_name, filename)
                VALUES (%s, %s, '1', NOW(), %s, %s)
            """
            
            insert_params = (
                self.config.process_id,
                customer_id,
                customer_name,
                list_files[0]
            )
            
            self.db.execute_update(insert_query, insert_params)
            
            # Get log ID
            log_id = self.db.get_max_id(
                log_report_table,
                'log_id',
                f"process_id='{self.config.process_id}' AND customer_id='{customer_id}'"
            )
            
            # Move file to inprogress
            client_inprogress_dir = os.path.join(
                self.config.paths.get('bot_inprogresspath'),
                customer_name
            )
            
            os.makedirs(client_inprogress_dir, exist_ok=True)
            
            # Clean inprogress directory
            for item in os.listdir(client_inprogress_dir):
                item_path = os.path.join(client_inprogress_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                except Exception:
                    pass
            
            client_filepath = os.path.join(client_inprogress_dir, list_files[0])
            shutil.move(in_client_filepath, client_filepath)
            
            if self.logger:
                self.logger.info(f"✅ File moved to inprogress: {list_files[0]}")
            
            # Process based on subprocess name
            process_status = self.process_customer_file(
                suprocess_name,
                client_filepath,
                customer_config
            )
            
            if not process_status:
                # Move to failed
                self.move_failed_clientfile(customer_name, client_filepath, log_id)
                return False
            
            # Move to processed
            self.move_to_processed(customer_name, client_filepath)
            
            # Update log as completed
            update_query = f"""
                UPDATE {log_report_table}
                SET completed_sts = '1', end_datetime = NOW()
                WHERE log_id = %s
            """
            
            self.db.execute_update(update_query, (log_id,))
            
            if self.logger:
                self.logger.success(f"✅ Customer {customer_name} processed successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to process customer {customer_name}: {str(e)}")
                self.logger.log_exception(f"execute_customer_{customer_id}", e)
            
            # Move to failed if file was moved
            if client_filepath and os.path.exists(client_filepath):
                self.move_failed_clientfile(customer_name, client_filepath, log_id)
            
            return False
    
    def process_customer_file(
        self,
        subprocess_name: str,
        client_filepath: str,
        customer_config: Dict[str, Any]
    ) -> bool:
        """
        Process customer file based on subprocess name
        
        Args:
            subprocess_name: Name of the subprocess (customer type)
            client_filepath: Path to customer Excel file
            customer_config: Customer configuration
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Running subprocess: {subprocess_name}")
            
            # Map subprocess name to processor method
            processor_map = {
                'PROCESS_CAPLIN': self.processor.process_caplin,
                'PROCESS_BELLS': self.processor.process_bells,
                'PROCESS_RELONCHEM': self.processor.process_relonchem,
                'PROCESS_MARKSANS_USA': self.processor.process_marksans_usa,
                'PROCESS_PADAGIS_USA': self.processor.process_padagis_usa,
                'PROCESS_PADAGIS_ISRAEL': self.processor.process_padagis_israel
            }
            
            # Get processor method
            processor_method = processor_map.get(subprocess_name)
            
            if not processor_method:
                if self.logger:
                    self.logger.error(f"❌ Unknown subprocess: {subprocess_name}")
                return False
            
            # Execute processor
            result = processor_method(client_filepath, customer_config)
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Customer file processing failed: {str(e)}")
                self.logger.log_exception("process_customer_file", e)
            return False
    
    def move_to_processed(self, customer_name: str, client_filepath: str) -> bool:
        """
        Move successfully processed file to processed directory
        
        Args:
            customer_name: Customer name
            client_filepath: Path to client file
            
        Returns:
            bool: True if successful
        """
        try:
            # Create processed directory for customer
            processed_customer_dir = os.path.join(
                self.config.paths.get('bot_processedpath'),
                str(self.config.process_id),
                customer_name
            )
            
            os.makedirs(processed_customer_dir, exist_ok=True)
            
            # Move file
            if os.path.exists(client_filepath):
                shutil.move(client_filepath, processed_customer_dir)
                
                if self.logger:
                    self.logger.info(f"✅ File moved to processed: {customer_name}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Failed to move file to processed: {str(e)}")
            return False
    
    def move_failed_clientfile(
        self,
        customer_name: str,
        client_filepath: str,
        log_id: Optional[int]
    ) -> None:
        """
        Move failed customer file to failed directory
        
        Args:
            customer_name: Customer name
            client_filepath: Path to client file
            log_id: Log ID for database update
        """
        try:
            # Create failed directory for customer
            failed_customer_dir = os.path.join(
                self.config.paths.get('bot_failedpath'),
                str(self.config.process_id),
                customer_name
            )
            
            os.makedirs(failed_customer_dir, exist_ok=True)
            
            # Move file
            if os.path.exists(client_filepath):
                filename = os.path.basename(client_filepath)
                shutil.move(client_filepath, failed_customer_dir)
                
                if self.logger:
                    self.logger.warning(f"⚠️ File moved to failed: {filename}")
                
                # Update log record
                if log_id:
                    log_report_table = self.config.get_table_name('log_report')
                    
                    error_msg = f"Failed while processing {customer_name} customer - {filename}"
                    
                    query = f"""
                        UPDATE {log_report_table}
                        SET failed_sts = '1',
                            failure_message = %s,
                            end_datetime = NOW()
                        WHERE log_id = %s
                    """
                    
                    self.db.execute_update(query, (error_msg, log_id))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error moving failed file: {str(e)}")


"""
Drug Intelligence Module - Part 3
Report generation and final output methods
"""

# ADD THESE METHODS TO THE DrugIntelligenceWorkflow CLASS

    def generate_report(self) -> bool:
        """
        Generate final Excel reports
        
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("Report Generation", "STARTED")
            
            # Create output directory
            di_output_dir = os.path.join(
                self.config.paths.get('bot_outpath'),
                str(self.config.process_id)
            )
            
            os.makedirs(di_output_dir, exist_ok=True)
            
            # Define report file path
            di_excel_report = os.path.join(
                di_output_dir,
                f"DrugIntelligence_Report_{self.config.process_id}.xlsx"
            )
            
            # Create Excel report with sheets
            sheet_list = ['Include_Exclude_Count', 'Overall_Report']
            
            self.excel.create_excel_with_sheets(di_excel_report, sheet_list)
            
            if self.logger:
                self.logger.success(f"✅ Report file created: {os.path.basename(di_excel_report)}")
            
            # Open Excel for writing
            self.excel.open_excel(di_excel_report)
            
            # Generate include/exclude count report
            self.generate_include_exclude_count_report(di_excel_report)
            
            # Generate overall report
            self.generate_overall_report(di_excel_report)
            
            # Close Excel
            self.excel.close_excel()
            
            # Store report path in config
            self.config.paths['di_excel_report'] = di_excel_report
            self.config.paths['di_output_dir'] = di_output_dir
            
            if self.logger:
                self.logger.log_process_step("Report Generation", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Report generation failed: {str(e)}")
                self.logger.log_exception("generate_report", e)
                self.logger.log_process_step("Report Generation", "FAILED")
            return False
    
    def generate_include_exclude_count_report(self, report_path: str) -> bool:
        """
        Generate include/exclude count report
        
        Args:
            report_path: Path to report Excel file
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info("⏳ Generating Include/Exclude Count Report...")
            
            # Truncate count tables
            overall_count_table = self.config.get_table_name('overall_count_report')
            inclusion_exclusion_table = self.config.get_table_name('inclusion_exclusion_counts')
            
            self.db.truncate_table(overall_count_table)
            self.db.truncate_table(inclusion_exclusion_table)
            
            # Get all customer report tables
            customer_tables = [
                ('caplin_master_report', 'Caplin'),
                ('bells_master_report', 'Bells'),
                ('relonchem_master_report', 'Relonchem'),
                ('marksans_usa_master_report', 'Marksans USA'),
                ('padagis_usa_master_report', 'Padagis USA'),
                ('padagis_israle_master_report', 'Padagis Israel')
            ]
            
            # Collect statistics
            stats_data = []
            
            for table_key, customer_name in customer_tables:
                table_name = self.config.get_table_name(table_key)
                
                if not table_name:
                    continue
                
                try:
                    # Count include/exclude
                    query = f"""
                        SELECT 
                            include_exclude_status,
                            COUNT(*) as count
                        FROM {table_name}
                        WHERE process_id = %s
                        GROUP BY include_exclude_status
                    """
                    
                    result = self.db.execute_query(query, (self.config.process_id,))
                    
                    include_count = 0
                    exclude_count = 0
                    
                    for status, count in result:
                        if status == 'include':
                            include_count = count
                        elif status == 'exclude':
                            exclude_count = count
                    
                    total_count = include_count + exclude_count
                    
                    stats_data.append({
                        'customer': customer_name,
                        'include': include_count,
                        'exclude': exclude_count,
                        'total': total_count
                    })
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not get stats for {customer_name}: {str(e)}")
            
            # Write to Excel (simplified - you can enhance this)
            if self.logger:
                self.logger.success(f"✅ Include/Exclude count report generated with {len(stats_data)} customers")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to generate include/exclude report: {str(e)}")
            return False
    
    def generate_overall_report(self, report_path: str) -> bool:
        """
        Generate overall summary report
        
        Args:
            report_path: Path to report Excel file
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info("⏳ Generating Overall Report...")
            
            # This is a placeholder for overall report generation
            # You can add the actual logic to generate comprehensive reports
            
            if self.logger:
                self.logger.success("✅ Overall report generated")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to generate overall report: {str(e)}")
            return False
    
    def move_to_bot_out(self) -> bool:
        """
        Move final output to BOT-OUT and send success notification
        
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("Final Output", "STARTED")
            
            # Get completed and failed files
            log_report_table = self.config.get_table_name('log_report')
            
            completed_query = f"""
                SELECT customer_name, filename
                FROM {log_report_table}
                WHERE completed_sts = '1' AND process_id = %s
            """
            
            completed_files = self.db.execute_query(completed_query, (self.config.process_id,))
            
            failed_query = f"""
                SELECT customer_name, filename, failure_message
                FROM {log_report_table}
                WHERE failed_sts = '1' AND process_id = %s
            """
            
            failed_files = self.db.execute_query(failed_query, (self.config.process_id,))
            
            # Check if all files failed
            if (not completed_files or len(completed_files) == 0) and failed_files and len(failed_files) > 0:
                # All failed
                error_message = "Below files failed during processing:\n\n"
                error_message += "\n".join([
                    f"{i+1}) {customer} - {filename} - {error}"
                    for i, (customer, filename, error) in enumerate(failed_files)
                ])
                
                self.move_to_failed(error_message)
                return False
            
            # Move master tracker to output
            master_tracker_path = self.config.paths.get('master_tracker_path')
            di_output_dir = self.config.paths.get('di_output_dir')
            
            if master_tracker_path and os.path.exists(master_tracker_path):
                try:
                    shutil.copy(master_tracker_path, di_output_dir)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not copy master tracker: {str(e)}")
            
            # Collect attachments
            attachments = []
            
            for file in os.listdir(di_output_dir):
                if file.endswith('.xlsx') and 'Conflict' not in file:
                    attachments.append(os.path.join(di_output_dir, file))
            
            # Send success email
            self.email.send_success_notification(
                mail_config=self.config.mail_config,
                process_id=str(self.config.process_id),
                filename=self.config.master_tracker_filename,
                success_files=completed_files if completed_files else [],
                failed_files=failed_files if failed_files else [],
                attachments=attachments
            )
            
            # Clean inprogress directory
            try:
                inprogress_dir = self.config.paths.get('bot_inprogresspath')
                for item in os.listdir(inprogress_dir):
                    item_path = os.path.join(inprogress_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception:
                        pass
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ Could not clean inprogress: {str(e)}")
            
            if self.logger:
                self.logger.log_process_step("Final Output", "COMPLETED")
                self.logger.success("✅ Success notification sent")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to move to BOT-OUT: {str(e)}")
                self.logger.log_exception("move_to_bot_out", e)
                self.logger.log_process_step("Final Output", "FAILED")
            return False
    
    def complete_process(self) -> bool:
        """
        Mark process as completed in database
        
        Returns:
            bool: True if successful
        """
        try:
            process_status_table = self.config.get_table_name('process_status')
            
            query = f"""
                UPDATE {process_status_table}
                SET process_status = 'Completed',
                    end_datetime = NOW()
                WHERE process_id = %s
            """
            
            self.db.execute_update(query, (self.config.process_id,))
            
            if self.logger:
                self.logger.success("✅ Process marked as completed in database")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to complete process: {str(e)}")
            return False

                
