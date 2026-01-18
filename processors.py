"""
Processors Module - Drug Intelligence Automation
Customer-specific processing logic for different drug databases
Integrates DataProcessing and ExcelHandler classes
"""

import sys
import os
from typing import List, Dict, Any, Optional, Tuple


class DrugDataProcessor:
    """
    Handles customer-specific drug data processing
    Uses DataProcessing class for data transformations
    """
    
    def __init__(
        self,
        data_processing_path: str = "./DataProcessing",
        config=None,
        db_manager=None,
        excel_manager=None,
        logger=None
    ):
        """
        Initialize Drug Data Processor
        
        Args:
            data_processing_path: Path to DataProcessing folder
            config: Configuration object
            db_manager: Database manager instance
            excel_manager: Excel manager instance
            logger: Logger instance
        """
        self.config = config
        self.db = db_manager
        self.excel = excel_manager
        self.logger = logger
        self.data_processor = None
        
        try:
            # Import DataProcessing class
            if data_processing_path not in sys.path:
                sys.path.insert(0, data_processing_path)
            
            if self.logger:
                self.logger.info(f"⏳ Importing DataProcessing from {data_processing_path}...")
            
            from DataProcessing import DataProcessing
            
            # Create DataProcessing instance
            self.data_processor = DataProcessing()
            
            if self.logger:
                self.logger.success("✅ DataProcessing imported and initialized successfully")
                
        except ImportError as e:
            error_msg = f"Failed to import DataProcessing: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise ImportError(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to initialize DataProcessing: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def get_excluded_salt(self, drug_name: str) -> str:
        """
        Filter drug name by removing excluded salts
        Uses DataProcessing to clean drug names
        
        Args:
            drug_name: Original drug name
            
        Returns:
            str: Filtered drug name without excluded salts
        """
        try:
            if not drug_name or not isinstance(drug_name, str):
                return ""
            
            # Split drug name by common separators
            parts = drug_name.replace('/', ' / ').replace('+', ' + ').split()
            
            # Filter out excluded salt names
            filtered_parts = []
            for part in parts:
                part_lower = part.strip().lower()
                # Check if part is not in excluded salts
                if part_lower not in [salt.lower() for salt in self.config.excluded_saltnames]:
                    filtered_parts.append(part.strip())
            
            # Join back filtered parts
            filtered_name = ' '.join(filtered_parts)
            
            return filtered_name.strip()
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Error filtering salt from '{drug_name}': {str(e)}")
            return drug_name
    
    def process_caplin(self, client_filepath: str, customer_config: Dict[str, Any]) -> bool:
        """
        Process Caplin customer data
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration (sheet, columns, etc.)
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("CAPLIN Processing", "STARTED")
            
            # Get configuration
            customer_sheetname = customer_config.get('excel_sheetname')
            excel_colnames = customer_config.get('column_names')
            excel_row_startind = int(customer_config.get('excel_startindex', 1))
            
            # Get table name
            caplin_table = self.config.get_table_name('caplin_master_report')
            
            if not caplin_table:
                raise Exception("Caplin master report table name not found")
            
            # Truncate table
            if self.logger:
                self.logger.info(f"⏳ Truncating table: {caplin_table}...")
            
            self.db.truncate_table(caplin_table)
            
            # Parse column names
            colnames = [col.strip() for col in excel_colnames.split(';')]
            
            # Read Excel data
            if self.logger:
                self.logger.info(f"⏳ Reading Caplin data from {os.path.basename(client_filepath)}...")
            
            sheet_values = self.excel.read_excel_with_clean_columns(
                client_filepath,
                customer_sheetname,
                colnames,
                excel_row_startind
            )
            
            if not sheet_values:
                raise Exception(f"No data found in sheet '{customer_sheetname}'")
            
            if self.logger:
                self.logger.info(f"✅ Read {len(sheet_values)} rows from Caplin file")
            
            # Process each row
            remark_default = self.config.master_tracker_config.get('remark_default_value', '')
            processed_count = 0
            
            for row_data in sheet_values:
                try:
                    # row_data format: [rowno, productname, strength, unit, active_ingredients, withdrawn_date]
                    rowno = row_data[0]
                    productname = row_data[1] if len(row_data) > 1 else ''
                    strength = row_data[2] if len(row_data) > 2 else ''
                    unit = row_data[3] if len(row_data) > 3 else ''
                    active_ingredients = row_data[4] if len(row_data) > 4 else ''
                    withdrawn_date = row_data[5] if len(row_data) > 5 else ''
                    
                    # Get filtered name (remove excluded salts)
                    filtered_name = self.get_excluded_salt(active_ingredients)
                    
                    # Determine include/exclude status based on withdrawn date
                    if withdrawn_date and str(withdrawn_date).strip():
                        include_exclude_status = 'exclude'
                        remark = 'Withdrawn date is present'
                    else:
                        include_exclude_status = 'include'
                        remark = remark_default
                    
                    # Strip all string values
                    values_to_insert = [
                        str(v).strip() if isinstance(v, str) else v 
                        for v in [productname, strength, unit, active_ingredients, withdrawn_date]
                    ]
                    
                    # Insert into database
                    query = f"""
                        INSERT INTO {caplin_table} 
                        (process_id, rowno, productname, strength, unit, active_ingrediants, 
                         filtered_name, withdrawn_date, include_exclude_status, added_datetime, remark)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """
                    
                    params = (
                        self.config.process_id,
                        rowno,
                        values_to_insert[0],  # productname
                        values_to_insert[1],  # strength
                        values_to_insert[2],  # unit
                        values_to_insert[3],  # active_ingredients
                        filtered_name,
                        values_to_insert[4],  # withdrawn_date
                        include_exclude_status,
                        remark
                    )
                    
                    self.db.execute_update(query, params)
                    processed_count += 1
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Failed to process row {rowno}: {str(e)}")
                    continue
            
            if self.logger:
                self.logger.success(f"✅ Caplin: Processed {processed_count}/{len(sheet_values)} rows")
            
            # Process drug names (common processing step)
            self.process_drug_names(caplin_table)
            
            if self.logger:
                self.logger.log_process_step("CAPLIN Processing", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Caplin processing failed: {str(e)}")
                self.logger.log_exception("process_caplin", e)
                self.logger.log_process_step("CAPLIN Processing", "FAILED")
            return False
    
    def process_bells(self, client_filepath: str, customer_config: Dict[str, Any]) -> bool:
        """
        Process Bells customer data (with colored cells)
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("BELLS Processing", "STARTED")
            
            # Get configuration
            customer_sheetname = customer_config.get('excel_sheetname')
            excel_colnames = customer_config.get('column_names')
            excel_row_startind = int(customer_config.get('excel_startindex', 1))
            
            # Get table name
            bells_table = self.config.get_table_name('bells_master_report')
            
            if not bells_table:
                raise Exception("Bells master report table name not found")
            
            # Truncate table
            self.db.truncate_table(bells_table)
            
            # Color mapping for Bells
            color_map = {
                (204, 255, 255): "Marketed",
                (150, 150, 150): "Licence cancelled by MAH",
                (255, 204, 153): "Not Marketed"
            }
            
            # Parse colored cells from XLS file
            if self.logger:
                self.logger.info(f"⏳ Parsing Bells colored cells from {os.path.basename(client_filepath)}...")
            
            excel_values = self.excel.xls_parse_colored_cells(
                client_filepath,
                customer_sheetname,
                excel_colnames,
                excel_row_startind - 1,  # Adjust for 0-based index
                color_map
            )
            
            if not excel_values:
                raise Exception(f"No colored cells found in sheet '{customer_sheetname}'")
            
            if self.logger:
                self.logger.info(f"✅ Found {len(excel_values)} colored cells")
            
            # Process each row
            remark_default = self.config.master_tracker_config.get('remark_default_value', '')
            processed_count = 0
            
            for row_data in excel_values:
                try:
                    # row_data format: (rowno, cell_value, color_rgb, color_status)
                    rowno = row_data[0]
                    active_ingredients = row_data[1]
                    color_status = row_data[3]
                    
                    # Get filtered name
                    filtered_name = self.get_excluded_salt(active_ingredients)
                    
                    # Determine include/exclude based on color status
                    if color_status == "Licence cancelled by MAH":
                        include_exclude_status = 'exclude'
                        remark = 'Licence cancelled by MAH'
                    else:
                        include_exclude_status = 'include'
                        remark = remark_default
                    
                    # Insert into database
                    query = f"""
                        INSERT INTO {bells_table}
                        (process_id, rowno, active_ingrediants, color_status, 
                         include_exclude_status, remark, added_datetime, filtered_name)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                    """
                    
                    params = (
                        self.config.process_id,
                        rowno,
                        active_ingredients,
                        color_status,
                        include_exclude_status,
                        remark,
                        filtered_name
                    )
                    
                    self.db.execute_update(query, params)
                    processed_count += 1
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Failed to process row {rowno}: {str(e)}")
                    continue
            
            if self.logger:
                self.logger.success(f"✅ Bells: Processed {processed_count}/{len(excel_values)} rows")
            
            # Process drug names
            self.process_drug_names(bells_table)
            
            if self.logger:
                self.logger.log_process_step("BELLS Processing", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Bells processing failed: {str(e)}")
                self.logger.log_exception("process_bells", e)
                self.logger.log_process_step("BELLS Processing", "FAILED")
            return False
    
    def process_drug_names(self, table_name: str) -> bool:
        """
        Common drug name processing logic
        Apply additional processing/validation on drug names
        
        Args:
            table_name: Name of the customer table to process
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Processing drug names in table: {table_name}...")
            
            # This is a placeholder for common drug name processing
            # You can add additional validation, normalization, or matching logic here
            
            # Example: Update filtered names if needed
            # query = f"UPDATE {table_name} SET filtered_name = ... WHERE ..."
            
            if self.logger:
                self.logger.success(f"✅ Drug names processed in {table_name}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Drug name processing failed for {table_name}: {str(e)}")
            return False

"""
Processors Module Part 2 - Remaining Customer Processors
Additional customer-specific processing methods
"""

# ADD THESE METHODS TO THE DrugDataProcessor CLASS

    def process_relonchem(self, client_filepath: str, customer_config: Dict[str, Any]) -> bool:
        """
        Process Relonchem customer data (with colored cells in XLSX)
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("RELONCHEM Processing", "STARTED")
            
            # Get configuration
            customer_sheetname = customer_config.get('excel_sheetname')
            excel_colnames = customer_config.get('column_names')
            excel_row_startind = int(customer_config.get('excel_startindex', 1))
            
            # Get table name
            relonchem_table = self.config.get_table_name('relonchem_master_report')
            
            if not relonchem_table:
                raise Exception("Relonchem master report table name not found")
            
            # Truncate table
            self.db.truncate_table(relonchem_table)
            
            # Color mapping for Relonchem
            color_map = {
                "9": "Marketed",
                "0": "Licence cancelled by the MAH",
                "7": "Licence Application Pending",
                "5": "Not Marketed",
                "8": "Invented name deleted",
                "FFFFFF00": "Newly Added"
            }
            
            # Parse colored cells from XLSX file
            if self.logger:
                self.logger.info(f"⏳ Parsing Relonchem colored cells from {os.path.basename(client_filepath)}...")
            
            excel_values = self.excel.xlsx_parse_colored_cells(
                client_filepath,
                customer_sheetname,
                excel_colnames,
                excel_row_startind,
                color_map
            )
            
            if not excel_values:
                raise Exception(f"No data found in sheet '{customer_sheetname}'")
            
            if self.logger:
                self.logger.info(f"✅ Found {len(excel_values)} rows")
            
            # Process each row
            remark_default = self.config.master_tracker_config.get('remark_default_value', '')
            processed_count = 0
            
            for row_data in excel_values:
                try:
                    # row_data format: [rowno, active_ingredients, color_code, color_status]
                    rowno = row_data[0]
                    active_ingredients = row_data[1]
                    color_status = row_data[3]
                    
                    # Get filtered name
                    filtered_name = self.get_excluded_salt(active_ingredients)
                    
                    # Determine include/exclude based on color status
                    include_statuses = ["Marketed", "Not Marketed", "Newly Added", "Invented name deleted"]
                    if color_status in include_statuses:
                        include_exclude_status = 'include'
                        remark = remark_default
                    else:
                        include_exclude_status = 'exclude'
                        remark = color_status
                    
                    # Insert into database
                    query = f"""
                        INSERT INTO {relonchem_table}
                        (process_id, rowno, active_ingrediants, color_status,
                         include_exclude_status, remark, added_datetime, filtered_name)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                    """
                    
                    params = (
                        self.config.process_id,
                        rowno,
                        active_ingredients,
                        color_status,
                        include_exclude_status,
                        remark,
                        filtered_name
                    )
                    
                    self.db.execute_update(query, params)
                    processed_count += 1
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Failed to process row {rowno}: {str(e)}")
                    continue
            
            if self.logger:
                self.logger.success(f"✅ Relonchem: Processed {processed_count}/{len(excel_values)} rows")
            
            # Process drug names
            self.process_drug_names(relonchem_table)
            
            if self.logger:
                self.logger.log_process_step("RELONCHEM Processing", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Relonchem processing failed: {str(e)}")
                self.logger.log_exception("process_relonchem", e)
                self.logger.log_process_step("RELONCHEM Processing", "FAILED")
            return False
    
    def process_marksans_usa(self, client_filepath: str, customer_config: Dict[str, Any]) -> bool:
        """
        Process Marksans USA customer data
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("MARKSANS USA Processing", "STARTED")
            
            # Get configuration
            customer_sheetname = customer_config.get('excel_sheetname')
            excel_colnames = customer_config.get('column_names')
            excel_row_startind = int(customer_config.get('excel_startindex', 1))
            
            # Get table name
            marksans_table = self.config.get_table_name('marksans_usa_master_report')
            
            if not marksans_table:
                raise Exception("Marksans USA master report table name not found")
            
            # Truncate table
            self.db.truncate_table(marksans_table)
            
            # Parse column names
            colnames = [col.strip() for col in excel_colnames.split(';')]
            
            # Read Excel data
            if self.logger:
                self.logger.info(f"⏳ Reading Marksans USA data from {os.path.basename(client_filepath)}...")
            
            rowvalues = self.excel.read_excel_with_clean_columns(
                client_filepath,
                customer_sheetname,
                colnames,
                excel_row_startind - 1
            )
            
            if not rowvalues:
                raise Exception(f"No data found in sheet '{customer_sheetname}'")
            
            if self.logger:
                self.logger.info(f"✅ Read {len(rowvalues)} rows")
            
            # Process each row
            remark_default = self.config.master_tracker_config.get('remark_default_value', '')
            processed_count = 0
            
            for row_data in rowvalues:
                try:
                    # row_data format: [rowno, active_ingredients, approval_status, withdrawn_date]
                    rowno = row_data[0]
                    active_ingredients = row_data[1] if len(row_data) > 1 else ''
                    approval_status = row_data[2] if len(row_data) > 2 else ''
                    withdrawn_date = row_data[3] if len(row_data) > 3 else ''
                    
                    # Clean newlines from active ingredients
                    drugname = active_ingredients.replace('\n', ' ').strip()
                    
                    # Get filtered name
                    filtered_name = self.get_excluded_salt(drugname)
                    
                    # Determine include/exclude status
                    approval_lower = str(approval_status).strip().lower()
                    withdrawn_clean = str(withdrawn_date).strip()
                    
                    if approval_lower not in ['approved', '']:
                        include_exclude_status = 'exclude'
                        remark = 'Approval Status is not Approved'
                    elif withdrawn_clean:
                        include_exclude_status = 'exclude'
                        remark = 'Withdrawn Date is not empty'
                    else:
                        include_exclude_status = 'include'
                        remark = remark_default
                    
                    # Insert into database
                    query = f"""
                        INSERT INTO {marksans_table}
                        (process_id, rowno, active_ingrediants, filtered_name,
                         approval_status, withdrawn_date, include_exclude_status, remark, added_datetime)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    
                    params = (
                        self.config.process_id,
                        rowno,
                        drugname,
                        filtered_name,
                        approval_status,
                        withdrawn_date,
                        include_exclude_status,
                        remark
                    )
                    
                    self.db.execute_update(query, params)
                    processed_count += 1
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Failed to process row {rowno}: {str(e)}")
                    continue
            
            if self.logger:
                self.logger.success(f"✅ Marksans USA: Processed {processed_count}/{len(rowvalues)} rows")
            
            # Process drug names
            self.process_drug_names(marksans_table)
            
            if self.logger:
                self.logger.log_process_step("MARKSANS USA Processing", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Marksans USA processing failed: {str(e)}")
                self.logger.log_exception("process_marksans_usa", e)
                self.logger.log_process_step("MARKSANS USA Processing", "FAILED")
            return False
    
    def process_padagis_usa(self, client_filepath: str, customer_config: Dict[str, Any]) -> bool:
        """
        Process Padagis USA customer data (multi-sheet with colored cells)
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("PADAGIS USA Processing", "STARTED")
            
            # Get configuration
            customer_sheetnames = customer_config.get('excel_sheetname')
            excel_colnames = customer_config.get('column_names')
            excel_row_startind = int(customer_config.get('excel_startindex', 1))
            
            # Get table name
            padagis_usa_table = self.config.get_table_name('padagis_usa_master_report')
            
            if not padagis_usa_table:
                raise Exception("Padagis USA master report table name not found")
            
            # Truncate table
            self.db.truncate_table(padagis_usa_table)
            
            # Parse sheet names and column names
            sheetnames = [s.strip() for s in customer_sheetnames.split(';')]
            colnames = [c.strip() for c in excel_colnames.split(';')]
            
            # Color mapping
            color_map = {'FFFF5050': 'Red'}
            
            # Parse multi-sheet colored cells
            if self.logger:
                self.logger.info(f"⏳ Parsing Padagis USA multi-sheet data from {os.path.basename(client_filepath)}...")
            
            rowvalues = self.excel.xlsx_parse_colored_multicells(
                client_filepath,
                sheetnames,
                colnames,
                excel_row_startind,
                color_map
            )
            
            if not rowvalues:
                raise Exception(f"No data found in sheets")
            
            if self.logger:
                self.logger.info(f"✅ Found {len(rowvalues)} rows across multiple sheets")
            
            # Process each row
            remark_default = self.config.master_tracker_config.get('remark_default_value', '')
            processed_count = 0
            
            for row_data in rowvalues:
                try:
                    # Expected format: [rowno, sheetname, ndc_no, ..., active_ingredients, ..., comment, color_code, color_status]
                    rowno = row_data[0]
                    sheetname = row_data[1]
                    ndc_no = row_data[2] if len(row_data) > 2 else ''
                    active_ingredients = row_data[5] if len(row_data) > 5 else ''
                    comment = row_data[8] if len(row_data) > 8 else ''
                    color_status = row_data[-1] if len(row_data) > 0 else ''
                    
                    # Clean comment
                    comment_clean = comment.replace('\n', ' ').replace("'", "''").strip()
                    
                    # Clean active ingredients
                    productname = active_ingredients.replace("'", "''").strip()
                    
                    # Get filtered name
                    filtered_name = self.get_excluded_salt(productname)
                    
                    # Determine include/exclude status
                    if sheetname == "Contract Manufactured Products":
                        include_exclude_status = 'exclude'
                        remark = 'Not MAH product'
                    elif color_status == 'Red':
                        include_exclude_status = 'exclude'
                        remark = 'Product Highlighted in Red'
                    elif 'discontinued' in comment_clean.lower():
                        include_exclude_status = 'exclude'
                        remark = comment_clean
                    else:
                        include_exclude_status = 'include'
                        remark = remark_default
                    
                    # Insert into database
                    query = f"""
                        INSERT INTO {padagis_usa_table}
                        (process_id, rowno, sheetname, ndc_no, active_ingrediants, comment,
                         filtered_name, color_status, include_exclude_status, remark, added_datetime)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    
                    params = (
                        self.config.process_id,
                        rowno,
                        sheetname,
                        ndc_no,
                        productname,
                        comment_clean,
                        filtered_name,
                        color_status,
                        include_exclude_status,
                        remark
                    )
                    
                    self.db.execute_update(query, params)
                    processed_count += 1
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Failed to process row {row_data[0] if row_data else 'unknown'}: {str(e)}")
                    continue
            
            if self.logger:
                self.logger.success(f"✅ Padagis USA: Processed {processed_count}/{len(rowvalues)} rows")
            
            # Process drug names
            self.process_drug_names(padagis_usa_table)
            
            if self.logger:
                self.logger.log_process_step("PADAGIS USA Processing", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Padagis USA processing failed: {str(e)}")
                self.logger.log_exception("process_padagis_usa", e)
                self.logger.log_process_step("PADAGIS USA Processing", "FAILED")
            return False
    
    def process_padagis_israel(self, client_filepath: str, customer_config: Dict[str, Any]) -> bool:
        """
        Process Padagis Israel customer data
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration
            
        Returns:
            bool: True if processing successful
        """
        try:
            if self.logger:
                self.logger.log_process_step("PADAGIS ISRAEL Processing", "STARTED")
            
            # Get configuration
            customer_sheetname = customer_config.get('excel_sheetname')
            excel_colnames = customer_config.get('column_names')
            excel_row_startind = int(customer_config.get('excel_startindex', 1))
            
            # Get table name
            padagis_israel_table = self.config.get_table_name('padagis_israle_master_report')
            
            if not padagis_israel_table:
                raise Exception("Padagis Israel master report table name not found")
            
            # Truncate table
            self.db.truncate_table(padagis_israel_table)
            
            # Parse column names
            colnames = [col.strip() for col in excel_colnames.split(';')]
            
            # Read Excel data
            if self.logger:
                self.logger.info(f"⏳ Reading Padagis Israel data from {os.path.basename(client_filepath)}...")
            
            rowvalues = self.excel.read_excel_with_clean_columns(
                client_filepath,
                customer_sheetname,
                colnames,
                excel_row_startind
            )
            
            if not rowvalues:
                raise Exception(f"No data found in sheet '{customer_sheetname}'")
            
            if self.logger:
                self.logger.info(f"✅ Read {len(rowvalues)} rows")
            
            # Process each row
            remark_default = self.config.master_tracker_config.get('remark_default_value', '')
            processed_count = 0
            
            for row_data in rowvalues:
                try:
                    # row_data format: [rowno, active_ingredients]
                    rowno = row_data[0]
                    active_ingredients = row_data[1] if len(row_data) > 1 else ''
                    
                    # Get filtered name
                    filtered_name = self.get_excluded_salt(active_ingredients)
                    
                    # All Padagis Israel entries are included by default
                    include_exclude_status = 'include'
                    remark = remark_default
                    
                    # Insert into database
                    query = f"""
                        INSERT INTO {padagis_israel_table}
                        (process_id, rowno, active_ingrediants, filtered_name,
                         include_exclude_status, remark, added_datetime)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """
                    
                    params = (
                        self.config.process_id,
                        rowno,
                        active_ingredients,
                        filtered_name,
                        include_exclude_status,
                        remark
                    )
                    
                    self.db.execute_update(query, params)
                    processed_count += 1
                    
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Failed to process row {rowno}: {str(e)}")
                    continue
            
            if self.logger:
                self.logger.success(f"✅ Padagis Israel: Processed {processed_count}/{len(rowvalues)} rows")
            
            # Process drug names
            self.process_drug_names(padagis_israel_table)
            
            if self.logger:
                self.logger.log_process_step("PADAGIS ISRAEL Processing", "COMPLETED")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Padagis Israel processing failed: {str(e)}")
                self.logger.log_exception("process_padagis_israel", e)
                self.logger.log_process_step("PADAGIS ISRAEL Processing", "FAILED")
            return False
