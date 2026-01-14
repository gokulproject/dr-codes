"""
Customer-specific data processors
Handles processing for different customer formats
"""

from typing import List, Dict, Any
from logger import get_logger
from database import DatabaseManager
from excel_creation import ExcelManager

# Import DataProcessing if available
try:
    from DataProcessing import DataProcessing
except ImportError:
    DataProcessing = None


class CustomerProcessors:
    """Handles customer-specific data processing"""
    
    def __init__(self, db_manager: DatabaseManager, excel_manager: ExcelManager, config):
        """
        Initialize customer processors
        
        Args:
            db_manager: Database manager instance
            excel_manager: Excel manager instance
            config: Configuration object
        """
        self.db = db_manager
        self.excel = excel_manager
        self.config = config
        self.logger = get_logger()
        self.data_processor = DataProcessing() if DataProcessing else None
    
    def process_caplin(self, client_filepath: str, customer_config: Dict) -> bool:
        """
        Process Caplin customer data
        
        Args:
            client_filepath: Path to client Excel file
            customer_config: Customer configuration
        
        Returns:
            bool: True if successful
        """
        try:
            self.logger.log_function_start("process_caplin", file=client_filepath)
            
            # Get configuration
            sheet_name = customer_config['excel_sheetname']
            col_names_str = customer_config['column_names']
            start_index = int(customer_config['excel_startindex'])
            
            col_names = col_names_str.split(';')
            
            # Truncate table
            table_name = self.config.get_table('caplin_master_report')
            self.db.truncate_table(table_name)
            
            # Read Excel data
            sheet_values = self.excel.read_excel_with_clean_columns(
                client_filepath, sheet_name, col_names, start_index
            )
            
            # Process each row
            process_id = self.config.PROCESS_CONFIG.get('process_id')
            remark_default = self.config.PROCESS_CONFIG.get('remark_default_value', '')
            
            for row_values in sheet_values:
                # row_values: [rowno, productname, strength, unit, active_ingredients, withdrawn_date]
                
                # Filter drug name
                filtered_name = self._filter_drug_name(row_values[5])  # active_ingredients
                
                # Determine include/exclude status
                if not row_values[-1] or row_values[-1].strip() == '':  # withdrawn_date empty
                    in_ex_status = 'include'
                    remark = remark_default
                else:
                    in_ex_status = 'exclude'
                    remark = 'Withdrawn date is present'
                
                # Insert into database
                insert_query = f"""
                    INSERT INTO {table_name} 
                    (process_id, rowno, productname, strength, unit, active_ingrediants, 
                     filtered_name, withdrawn_date, include_exclude_status, added_datetime, remark)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """
                
                self.db.cursor.execute(insert_query, (
                    process_id,
                    row_values[0],  # rowno
                    row_values[1],  # productname
                    row_values[2],  # strength
                    row_values[3],  # unit
                    row_values[4],  # active_ingredients
                    filtered_name,
                    row_values[5] if len(row_values) > 5 else '',  # withdrawn_date
                    in_ex_status,
                    remark
                ))
            
            self.db.connection.commit()
            
            # Process drug names
            self._process_drug_names(table_name)
            
            self.logger.log_function_end("process_caplin", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Process Caplin")
            return False
    
    def process_bells(self, client_filepath: str, customer_config: Dict) -> bool:
        """Process Bells customer data with colored cells"""
        try:
            self.logger.log_function_start("process_bells", file=client_filepath)
            
            # Configuration
            sheet_name = customer_config['excel_sheetname']
            col_names_str = customer_config['column_names']
            start_index = int(customer_config['excel_startindex'])
            
            col_names = col_names_str.split(';')
            table_name = self.config.get_table('bells_master_report')
            
            # Color mapping
            color_map = {
                (204, 255, 255): "Marketed",
                (150, 150, 150): "Licence cancelled by MAH",
                (255, 204, 153): "Not Marketed"
            }
            
            # Truncate table
            self.db.truncate_table(table_name)
            
            # Parse colored cells
            excel_values = self.excel.parse_colored_cells(
                client_filepath, sheet_name, col_names, start_index - 1, color_map
            )
            
            # Process each row
            process_id = self.config.PROCESS_CONFIG.get('process_id')
            remark_default = self.config.PROCESS_CONFIG.get('remark_default_value', '')
            
            for values in excel_values:
                # values: [rowno, active_ingredients, color_status]
                filtered_name = self._filter_drug_name(values[1])
                
                if values[2] == "Licence cancelled by MAH":
                    remark = "Licence cancelled by MAH"
                    inex_status = "exclude"
                else:
                    remark = remark_default
                    inex_status = "include"
                
                insert_query = f"""
                    INSERT INTO {table_name}
                    (process_id, rowno, active_ingrediants, color_status, 
                     include_exclude_status, remark, added_datetime, filtered_name)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                """
                
                self.db.cursor.execute(insert_query, (
                    process_id, values[0], values[1], values[2],
                    inex_status, remark, filtered_name
                ))
            
            self.db.connection.commit()
            self._process_drug_names(table_name)
            
            self.logger.log_function_end("process_bells", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Process Bells")
            return False
    
    def process_relonchem(self, client_filepath: str, customer_config: Dict) -> bool:
        """Process Relonchem customer data with colored cells"""
        try:
            self.logger.log_function_start("process_relonchem", file=client_filepath)
            
            sheet_name = customer_config['excel_sheetname']
            col_names_str = customer_config['column_names']
            start_index = int(customer_config['excel_startindex'])
            
            col_names = col_names_str.split(';')
            table_name = self.config.get_table('relonchem_master_report')
            
            # Color mapping
            color_map = {
                "9": "Marketed",
                "0": "Licence cancelled by the MAH",
                "7": "Licence Application Pending",
                "5": "Not Marketed",
                "8": "Invented name deleted",
                "FFFFFF00": "Newly Added"
            }
            
            self.db.truncate_table(table_name)
            
            excel_values = self.excel.parse_colored_cells(
                client_filepath, sheet_name, col_names, start_index, color_map
            )
            
            process_id = self.config.PROCESS_CONFIG.get('process_id')
            remark_default = self.config.PROCESS_CONFIG.get('remark_default_value', '')
            
            for values in excel_values:
                filtered_name = self._filter_drug_name(values[1])
                
                # Determine remark and status
                included_statuses = ["Marketed", "Not Marketed", "Newly Added", "Invented name deleted"]
                if values[2] in included_statuses:
                    remark = remark_default
                    inex_status = "include"
                else:
                    remark = values[2]
                    inex_status = "exclude"
                
                insert_query = f"""
                    INSERT INTO {table_name}
                    (process_id, rowno, active_ingrediants, color_status,
                     include_exclude_status, remark, added_datetime, filtered_name)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                """
                
                self.db.cursor.execute(insert_query, (
                    process_id, values[0], values[1], values[2],
                    inex_status, remark, filtered_name
                ))
            
            self.db.connection.commit()
            self._process_drug_names(table_name)
            
            self.logger.log_function_end("process_relonchem", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Process Relonchem")
            return False
    
    def process_marksans_usa(self, client_filepath: str, customer_config: Dict) -> bool:
        """Process Marksans USA customer data"""
        try:
            self.logger.log_function_start("process_marksans_usa", file=client_filepath)
            
            sheet_name = customer_config['excel_sheetname']
            col_names_str = customer_config['column_names']
            start_index = int(customer_config['excel_startindex']) - 1
            
            col_names = col_names_str.split(';')
            table_name = self.config.get_table('marksans_usa_master_report')
            
            self.db.truncate_table(table_name)
            
            row_values = self.excel.read_excel_with_clean_columns(
                client_filepath, sheet_name, col_names, start_index
            )
            
            process_id = self.config.PROCESS_CONFIG.get('process_id')
            remark_default = self.config.PROCESS_CONFIG.get('remark_default_value', '')
            
            for values in row_values:
                # values: [rowno, active_ingredients, approval_status, withdrawn_date]
                
                approval_status = values[2].strip().lower() if values[2] else ''
                withdrawn_date = values[3].strip() if values[3] else ''
                
                # Determine remark and status
                if approval_status not in ['approved', '']:
                    remark = "Approval Status is not Approved"
                    inex_status = "exclude"
                elif withdrawn_date:
                    remark = "Withdrawn Date is not empty"
                    inex_status = "exclude"
                else:
                    remark = remark_default
                    inex_status = "include"
                
                filtered_name = self._filter_drug_name(values[1])
                drugname = values[1].replace('\n', '')
                
                insert_query = f"""
                    INSERT INTO {table_name}
                    (process_id, rowno, active_ingrediants, filtered_name, approval_status,
                     withdrawn_date, include_exclude_status, remark, added_datetime)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """
                
                self.db.cursor.execute(insert_query, (
                    process_id, values[0], drugname, filtered_name,
                    values[2], values[3], inex_status, remark
                ))
            
            self.db.connection.commit()
            self._process_drug_names(table_name)
            
            self.logger.log_function_end("process_marksans_usa", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Process Marksans USA")
            return False
    
    def process_padagis_usa(self, client_filepath: str, customer_config: Dict) -> bool:
        """Process Padagis USA customer data with multi-sheet support"""
        try:
            self.logger.log_function_start("process_padagis_usa", file=client_filepath)
            
            # This would require special handling for multi-sheet processing
            # Implementation depends on ExcelHandler capabilities
            
            self.logger.warning("Padagis USA processing requires advanced Excel handling")
            return False
            
        except Exception as e:
            self.logger.log_exception(e, "Process Padagis USA")
            return False
    
    def process_padagis_israel(self, client_filepath: str, customer_config: Dict) -> bool:
        """Process Padagis Israel customer data"""
        try:
            self.logger.log_function_start("process_padagis_israel", file=client_filepath)
            
            sheet_name = customer_config['excel_sheetname']
            col_names = customer_config['column_names'].split(';')
            start_index = int(customer_config['excel_startindex'])
            
            table_name = self.config.get_table('padagis_israle_master_report')
            self.db.truncate_table(table_name)
            
            row_values = self.excel.read_excel_with_clean_columns(
                client_filepath, sheet_name, col_names, start_index
            )
            
            process_id = self.config.PROCESS_CONFIG.get('process_id')
            remark_default = self.config.PROCESS_CONFIG.get('remark_default_value', '')
            
            for values in row_values:
                filtered_name = self._filter_drug_name(values[1])
                
                insert_query = f"""
                    INSERT INTO {table_name}
                    (process_id, rowno, active_ingrediants, filtered_name,
                     include_exclude_status, remark, added_datetime)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """
                
                self.db.cursor.execute(insert_query, (
                    process_id, values[0], values[1], filtered_name,
                    'include', remark_default
                ))
            
            self.db.connection.commit()
            self._process_drug_names(table_name)
            
            self.logger.log_function_end("process_padagis_israel", "Success")
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Process Padagis Israel")
            return False
    
    def _filter_drug_name(self, drug_name: str) -> str:
        """
        Filter drug name by removing excluded salts
        
        Args:
            drug_name: Original drug name
        
        Returns:
            Filtered drug name
        """
        if self.data_processor and hasattr(self.data_processor, 'filter_drug_name'):
            return self.data_processor.filter_drug_name(drug_name)
        
        # Fallback implementation
        # This would use the excluded_saltnames list from config
        filtered = drug_name
        # Simple filtering logic
        return filtered.strip()
    
    def _process_drug_names(self, table_name: str):
        """
        Process drug names in the table for matching
        
        Args:
            table_name: Table to process
        """
        try:
            if self.data_processor and hasattr(self.data_processor, 'process_drug_names'):
                self.data_processor.process_drug_names(self.db, table_name)
            else:
                self.logger.info(f"Drug name processing for {table_name} - using default")
                # Default processing logic would go here
            
        except Exception as e:
            self.logger.log_exception(e, f"Process drug names in {table_name}")
