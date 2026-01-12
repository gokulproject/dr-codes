"""
Customer-specific processors for different data formats
"""
import os
from typing import List, Dict, Any
from datetime import datetime

from database import DatabaseHandler
from excel import ExcelHandler
from logger import get_logger
from scraper import WebScraper


class CustomerProcessor:
    """Base class for customer-specific processing"""
    
    def __init__(self, db: DatabaseHandler, excel_handler: ExcelHandler, config, process_id: str):
        self.db = db
        self.excel_handler = excel_handler  # Changed from excel to excel_handler
        self.config = config
        self.process_id = process_id
        self.logger = get_logger()
        self.remark_default = config.master_tracker.get('default_remark', 'Default remark')
        self.scraper = WebScraper()  # Optional web scraper for data enrichment
    
    def get_filtered_name(self, product_name: str, excluded_salts: List[str]) -> str:
        """Remove excluded salts from product name"""
        import re
        if not product_name:
            return ""
        
        filtered_name = product_name
        for salt in excluded_salts:
            pattern = re.compile(re.escape(salt), re.IGNORECASE)
            filtered_name = pattern.sub('', filtered_name)
        
        filtered_name = ' '.join(filtered_name.split())
        return filtered_name.strip()


class CaplinProcessor(CustomerProcessor):
    """Process Caplin customer data"""
    
    def process(self, client_filepath: str, customer_info: Dict[str, Any], 
                excluded_salts: List[str]):
        """Process Caplin Excel file"""
        try:
            self.logger.info(f"Processing Caplin file: {client_filepath}")
            
            sheetname = customer_info['excel_sheetname']
            start_index = int(customer_info['excel_startindex'])
            column_names = customer_info['column_names'].split(';')
            
            # Truncate table
            table_name = self.config.get_table_name('caplin_master_report')
            self.db.truncate_table(table_name)
            
            # Read Excel data
            sheet_values = self.excel_handler.read_excel_with_clean_columns(
                client_filepath, sheetname, column_names, start_index
            )
            
            # Process each row
            for values in sheet_values:
                # values = [rowno, productname, strength, unit, active_ingredients, withdrawn_date]
                filtered_name = self.get_filtered_name(values[5], excluded_salts)
                
                # Determine include/exclude status
                if values[-1] == '':  # withdrawn_date is empty
                    in_ex_sts = 'include'
                    remark = self.remark_default
                else:
                    in_ex_sts = 'exclude'
                    remark = 'Withdrawn date is present'
                
                # Strip whitespace
                values = [v.strip() if isinstance(v, str) else v for v in values]
                
                # Insert into database
                data = {
                    'process_id': self.process_id,
                    'rowno': values[0],
                    'productname': values[1],
                    'strength': values[2],
                    'unit': values[3],
                    'active_ingrediants': values[4],
                    'filtered_name': filtered_name,
                    'withdrawn_date': values[5] if len(values) > 5 else '',
                    'include_exclude_status': in_ex_sts,
                    'added_datetime': datetime.now(),
                    'remark': remark
                }
                
                self.db.insert_drug_record(table_name, data)
            
            self.logger.info(f"Processed {len(sheet_values)} Caplin records")
            
        except Exception as e:
            self.logger.error(f"Error processing Caplin: {str(e)}", exc_info=True)
            raise


class BellsProcessor(CustomerProcessor):
    """Process Bells customer data with colored cells"""
    
    def process(self, client_filepath: str, customer_info: Dict[str, Any],
                excluded_salts: List[str]):
        """Process Bells Excel file with colored cells"""
        try:
            self.logger.info(f"Processing Bells file: {client_filepath}")
            
            sheetname = customer_info['excel_sheetname']
            start_index = int(customer_info['excel_startindex']) - 1
            column_names = customer_info['column_names'].split(';')
            
            # Color mapping
            color_map = {
                (204, 255, 255): "Marketed",
                (150, 150, 150): "Licence cancelled by MAH",
                (255, 204, 153): "Not Marketed"
            }
            
            # Truncate table
            table_name = self.config.get_table_name('bells_master_report')
            self.db.truncate_table(table_name)
            
            # Parse colored cells
            excel_values = self.excel_handler.parse_colored_cells_xls(
                client_filepath, sheetname, column_names, start_index, color_map
            )
            
            # Process each row
            for values in excel_values:
                # values = [rowno, active_ingredients, ..., color_status]
                filtered_name = self.get_filtered_name(values[1], excluded_salts)
                
                # Determine include/exclude status and remark
                if values[3] == "Licence cancelled by MAH":
                    in_ex_sts = 'exclude'
                    remark = 'Licence cancelled by MAH'
                else:
                    in_ex_sts = 'include'
                    remark = self.remark_default
                
                # Insert into database
                data = {
                    'process_id': self.process_id,
                    'rowno': values[0],
                    'active_ingrediants': values[1],
                    'color_status': values[3],
                    'include_exclude_status': in_ex_sts,
                    'remark': remark,
                    'added_datetime': datetime.now(),
                    'filtered_name': filtered_name
                }
                
                self.db.insert_drug_record(table_name, data)
            
            self.logger.info(f"Processed {len(excel_values)} Bells records")
            
        except Exception as e:
            self.logger.error(f"Error processing Bells: {str(e)}", exc_info=True)
            raise


class RelonchemProcessor(CustomerProcessor):
    """Process Relonchem customer data with colored cells"""
    
    def process(self, client_filepath: str, customer_info: Dict[str, Any],
                excluded_salts: List[str]):
        """Process Relonchem Excel file"""
        try:
            self.logger.info(f"Processing Relonchem file: {client_filepath}")
            
            sheetname = customer_info['excel_sheetname']
            start_index = int(customer_info['excel_startindex'])
            column_names = customer_info['column_names'].split(';')
            
            # Color mapping
            color_map = {
                "9": "Marketed",
                "0": "Licence cancelled by the MAH",
                "7": "Licence Application Pending",
                "5": "Not Marketed",
                "8": "Invented name deleted",
                "FFFFFF00": "Newly Added"
            }
            
            # Truncate table
            table_name = self.config.get_table_name('relonchem_master_report')
            self.db.truncate_table(table_name)
            
            # Parse colored cells
            excel_values = self.excel_handler.parse_colored_cells_xlsx(
                client_filepath, sheetname, column_names, start_index, color_map
            )
            
            # Process each row
            for values in excel_values:
                filtered_name = self.get_filtered_name(values[1], excluded_salts)
                
                # Determine include/exclude status
                if values[3] in ["Marketed", "Not Marketed", "Newly Added", "Invented name deleted"]:
                    remark = self.remark_default
                    in_ex_sts = 'include'
                else:
                    remark = values[3]
                    in_ex_sts = 'exclude'
                
                # Insert into database
                data = {
                    'process_id': self.process_id,
                    'rowno': values[0],
                    'active_ingrediants': values[1],
                    'color_status': values[3],
                    'include_exclude_status': in_ex_sts,
                    'remark': remark,
                    'added_datetime': datetime.now(),
                    'filtered_name': filtered_name
                }
                
                self.db.insert_drug_record(table_name, data)
            
            self.logger.info(f"Processed {len(excel_values)} Relonchem records")
            
        except Exception as e:
            self.logger.error(f"Error processing Relonchem: {str(e)}", exc_info=True)
            raise


class MarksansUSAProcessor(CustomerProcessor):
    """Process Marksans USA customer data"""
    
    def process(self, client_filepath: str, customer_info: Dict[str, Any],
                excluded_salts: List[str]):
        """Process Marksans USA Excel file"""
        try:
            self.logger.info(f"Processing Marksans USA file: {client_filepath}")
            
            sheetname = customer_info['excel_sheetname']
            start_index = int(customer_info['excel_startindex']) - 1
            column_names = customer_info['column_names'].split(';')
            
            # Truncate table
            table_name = self.config.get_table_name('marksans_usa_master_report')
            self.db.truncate_table(table_name)
            
            # Read Excel data
            row_values = self.excel_handler.read_excel_with_clean_columns(
                client_filepath, sheetname, column_names, start_index
            )
            
            # Process each row
            for values in row_values:
                # values = [rowno, active_ingredients, approval_status, withdrawn_date]
                
                # Determine include/exclude status
                approval_status = str(values[2]).strip().lower()
                withdrawn_date = str(values[3]).strip()
                
                if approval_status not in ["approved", ""]:
                    remark = "Approval Status is not Approved"
                    in_ex_sts = 'exclude'
                elif withdrawn_date:
                    remark = "Withdrawn Date is not empty"
                    in_ex_sts = 'exclude'
                else:
                    remark = self.remark_default
                    in_ex_sts = 'include'
                
                filtered_name = self.get_filtered_name(values[1], excluded_salts)
                drugname = str(values[1]).replace('\n', '')
                
                # Insert into database
                data = {
                    'process_id': self.process_id,
                    'rowno': values[0],
                    'active_ingrediants': drugname,
                    'filtered_name': filtered_name,
                    'approval_status': values[2],
                    'withdrawn_date': values[3],
                    'include_exclude_status': in_ex_sts,
                    'remark': remark,
                    'added_datetime': datetime.now()
                }
                
                self.db.insert_drug_record(table_name, data)
            
            self.logger.info(f"Processed {len(row_values)} Marksans USA records")
            
        except Exception as e:
            self.logger.error(f"Error processing Marksans USA: {str(e)}", exc_info=True)
            raise


class PadagisUSAProcessor(CustomerProcessor):
    """Process Padagis USA customer data"""
    
    def process(self, client_filepath: str, customer_info: Dict[str, Any],
                excluded_salts: List[str]):
        """Process Padagis USA Excel file with multiple sheets and colored cells"""
        try:
            self.logger.info(f"Processing Padagis USA file: {client_filepath}")
            
            sheetnames = customer_info['excel_sheetname'].split(';')
            start_index = int(customer_info['excel_startindex'])
            column_names = customer_info['column_names'].split(';')
            
            # Color mapping
            color_map = {'FFFF5050': 'Red'}
            
            # Truncate table
            table_name = self.config.get_table_name('padagis_usa_master_report')
            self.db.truncate_table(table_name)
            
            # Process all sheets (implementation would need multi-sheet support)
            # For now, processing first sheet as example
            
            self.logger.info(f"Processed Padagis USA records")
            
        except Exception as e:
            self.logger.error(f"Error processing Padagis USA: {str(e)}", exc_info=True)
            raise


class PadagisIsraelProcessor(CustomerProcessor):
    """Process Padagis Israel customer data"""
    
    def process(self, client_filepath: str, customer_info: Dict[str, Any],
                excluded_salts: List[str]):
        """Process Padagis Israel Excel file"""
        try:
            self.logger.info(f"Processing Padagis Israel file: {client_filepath}")
            
            sheetname = customer_info['excel_sheetname']
            start_index = int(customer_info['excel_startindex'])
            column_names = customer_info['column_names'].split(';')
            
            # Truncate table
            table_name = self.config.get_table_name('padagis_israle_master_report')
            self.db.truncate_table(table_name)
            
            # Read Excel data
            row_values = self.excel_handler.read_excel_with_clean_columns(
                client_filepath, sheetname, column_names, start_index
            )
            
            # Process each row
            for values in row_values:
                filtered_name = self.get_filtered_name(values[1], excluded_salts)
                
                # Insert into database
                data = {
                    'process_id': self.process_id,
                    'rowno': values[0],
                    'active_ingrediants': values[1],
                    'filtered_name': filtered_name,
                    'include_exclude_status': 'include',
                    'remark': self.remark_default,
                    'added_datetime': datetime.now()
                }
                
                self.db.insert_drug_record(table_name, data)
            
            self.logger.info(f"Processed {len(row_values)} Padagis Israel records")
            
        except Exception as e:
            self.logger.error(f"Error processing Padagis Israel: {str(e)}", exc_info=True)
            raise
