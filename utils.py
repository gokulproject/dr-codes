"""
Drug Intelligence Module - Part 3
Report generation and final output methods
"""

# ADD THESE METHODS TO THE DrugIntelligenceWorkflow CLASS

    def generate_report(self) -> bool:
        """
        Generate final Excel reports with data
        Following RPA Robot Framework GENERATE_REPORT logic
        
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
            
            if self.logger:
                self.logger.info(f"⏳ Creating Excel report: {os.path.basename(di_excel_report)}")
            
            self.excel.create_excel_with_sheets(di_excel_report, sheet_list)
            
            if self.logger:
                self.logger.success(f"✅ Report file created: {os.path.basename(di_excel_report)}")
            
            # Generate Include/Exclude Count Report
            # Note: This will open/close Excel internally
            if not self.generate_include_exclude_count_report(di_excel_report):
                if self.logger:
                    self.logger.warning("⚠️ Include/Exclude count report generation had issues")
            
            # Generate Overall Report
            # Note: This will open/close Excel internally
            if not self.generate_overall_report(di_excel_report):
                if self.logger:
                    self.logger.warning("⚠️ Overall report generation had issues")
            
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
        Generate include/exclude count report with actual Excel data
        Following RPA Robot Framework GENERATE_INCLUDE_EXCLUDE_COUNT_REPORT logic
        
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
            
            # Open Excel file and get Include_Exclude_Count sheet
            sheet_name = 'Include_Exclude_Count'
            self.excel.open_excel(report_path, sheet_name)
            
            # Write headers
            headers = ['Customer Name', 'Include Count', 'Exclude Count', 'Total Count']
            self.excel.excel_handler.ws.append(headers)
            
            # Collect statistics and write to both DB and Excel
            row_num = 2  # Start from row 2 (after header)
            
            for table_key, customer_name in customer_tables:
                table_name = self.config.get_table_name(table_key)
                
                if not table_name:
                    continue
                
                try:
                    # Count include/exclude from database
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
                    
                    if result:
                        for row in result:
                            status = row[0]
                            count = row[1]
                            if status == 'include':
                                include_count = int(count)
                            elif status == 'exclude':
                                exclude_count = int(count)
                    
                    total_count = include_count + exclude_count
                    
                    # Insert into inclusion_exclusion_counts table
                    insert_query = f"""
                        INSERT INTO {inclusion_exclusion_table}
                        (process_id, customer_name, include_count, exclude_count, total_count, added_datetime)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """
                    
                    self.db.execute_update(insert_query, (
                        self.config.process_id,
                        customer_name,
                        include_count,
                        exclude_count,
                        total_count
                    ))
                    
                    # Write to Excel
                    row_data = [customer_name, include_count, exclude_count, total_count]
                    self.excel.excel_handler.ws.append(row_data)
                    row_num += 1
                    
                    if self.logger:
                        self.logger.info(f"  {customer_name}: Include={include_count}, Exclude={exclude_count}, Total={total_count}")
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not get stats for {customer_name}: {str(e)}")
            
            # Save and close Excel
            self.excel.save_excel()
            
            if self.logger:
                self.logger.success(f"✅ Include/Exclude count report generated with {len(customer_tables)} customers")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to generate include/exclude report: {str(e)}")
                self.logger.log_exception("generate_include_exclude_count_report", e)
            return False
    
    def generate_overall_report(self, report_path: str) -> bool:
        """
        Generate overall summary report with customer data
        Following RPA Robot Framework GENERTE_OVERALL_REPORT_GENERATOR logic
        
        Args:
            report_path: Path to report Excel file
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info("⏳ Generating Overall Report...")
            
            # Get overall count table
            overall_count_table = self.config.get_table_name('overall_count_report')
            
            # Open Excel file and get Overall_Report sheet
            sheet_name = 'Overall_Report'
            self.excel.open_excel(report_path, sheet_name)
            
            # Get customer configuration from database
            customer_table = self.config.get_table_name('customer_table')
            
            query = f"""
                SELECT customer_id, customer_name
                FROM {customer_table}
                WHERE status = 1
                ORDER BY customer_id
            """
            
            customers = self.db.execute_query(query)
            
            if not customers:
                if self.logger:
                    self.logger.warning("⚠️ No customers found for overall report")
                return False
            
            # Create headers: Product Name | Customer1 | Customer2 | ... | Comments
            headers = ['Product Name']
            customer_map = {}  # Map customer_id to column index
            
            col_index = 2  # Start from column 2 (column 1 is Product Name)
            for customer_id, customer_name in customers:
                headers.append(customer_name)
                customer_map[int(customer_id)] = col_index
                col_index += 1
            
            headers.append('Comments')
            
            # Write headers to Excel
            self.excel.excel_handler.ws.append(headers)
            
            # Get master tracker data (from master_tracker_updates table or read from file)
            # Following RPA logic: READ_MASTER_TRACKER
            master_tracker_path = self.config.paths.get('master_tracker_path')
            master_sheetname = self.config.master_tracker_config.get('master_sheetname')
            product_col = self.config.master_tracker_config.get('mater_tracker_productcol')
            comment_col = self.config.master_tracker_config.get('comment_colname')
            
            # Get column names for customers
            mt_columnnames_table = self.config.table_names.get('mt_columnnames_table')
            
            query = f"""
                SELECT excel_colname 
                FROM {mt_columnnames_table} 
                WHERE status = 1
                ORDER BY display_order
            """
            
            result = self.db.execute_query(query)
            customer_columns = [row[0] for row in result] if result else []
            
            # Combine: Product Name + Customer Columns + Comments
            all_columns = [product_col] + customer_columns + [comment_col]
            
            # Read master tracker file
            try:
                # Get starting row from config (default to 1)
                mt_starting_row = 1  # You can make this configurable
                
                mt_data = self.excel.read_excel_with_clean_columns(
                    master_tracker_path,
                    master_sheetname,
                    all_columns,
                    mt_starting_row - 1
                )
                
                if not mt_data:
                    if self.logger:
                        self.logger.warning("⚠️ No data found in master tracker")
                    return False
                
                # Write data to Overall_Report sheet
                for row_data in mt_data:
                    try:
                        # row_data format: [rowno, product_name, customer1_status, customer2_status, ..., comments]
                        # We need: [product_name, customer1_status, customer2_status, ..., comments]
                        
                        # Skip rowno (index 0), start from product name (index 1)
                        excel_row = row_data[1:]  # Remove rowno
                        
                        self.excel.excel_handler.ws.append(excel_row)
                        
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"⚠️ Error writing row to overall report: {str(e)}")
                        continue
                
                if self.logger:
                    self.logger.success(f"✅ Overall report generated with {len(mt_data)} products")
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"❌ Failed to read master tracker: {str(e)}")
                return False
            
            # Save and close Excel
            self.excel.save_excel()
            
            # Update overall_count_report table
            # Calculate total Y and N counts for each customer
            for customer_id, customer_name in customers:
                try:
                    # Get customer table
                    customer_table_key = None
                    customer_name_lower = customer_name.lower().replace(' ', '_')
                    
                    # Map customer name to table key
                    table_mapping = {
                        'caplin': 'caplin_master_report',
                        'bells': 'bells_master_report',
                        'relonchem': 'relonchem_master_report',
                        'marksans_usa': 'marksans_usa_master_report',
                        'padagis_usa': 'padagis_usa_master_report',
                        'padagis_israel': 'padagis_israle_master_report'
                    }
                    
                    customer_table_key = table_mapping.get(customer_name_lower)
                    
                    if not customer_table_key:
                        continue
                    
                    customer_table_name = self.config.get_table_name(customer_table_key)
                    
                    if not customer_table_name:
                        continue
                    
                    # Count Y (include) and N (exclude)
                    count_query = f"""
                        SELECT 
                            include_exclude_status,
                            COUNT(*) as count
                        FROM {customer_table_name}
                        WHERE process_id = %s
                        GROUP BY include_exclude_status
                    """
                    
                    count_result = self.db.execute_query(count_query, (self.config.process_id,))
                    
                    y_count = 0
                    n_count = 0
                    
                    if count_result:
                        for status, count in count_result:
                            if status == 'include':
                                y_count = int(count)
                            elif status == 'exclude':
                                n_count = int(count)
                    
                    # Insert into overall_count_report
                    insert_query = f"""
                        INSERT INTO {overall_count_table}
                        (process_id, customer_id, customer_name, y_count, n_count, added_datetime)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """
                    
                    self.db.execute_update(insert_query, (
                        self.config.process_id,
                        customer_id,
                        customer_name,
                        y_count,
                        n_count
                    ))
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Could not update overall count for {customer_name}: {str(e)}")
            
            if self.logger:
                self.logger.success("✅ Overall report completed with customer data")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to generate overall report: {str(e)}")
                self.logger.log_exception("generate_overall_report", e)
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