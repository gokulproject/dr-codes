"""
Excel Manager Module - Drug Intelligence Automation
Wrapper for ExcelHandler class with logging and error handling
Dynamically imports and uses ExcelHandler methods
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple


class ExcelManager:
    """
    Wrapper class for ExcelHandler
    Provides logging, error handling, and validation for Excel operations
    """
    
    def __init__(self, excel_handler_path: str = "./ExcelHandler", logger=None):
        """
        Initialize Excel Manager and import ExcelHandler
        
        Args:
            excel_handler_path: Path to ExcelHandler folder
            logger: Logger instance for logging operations
        """
        self.logger = logger
        self.excel_handler = None
        
        try:
            # Add ExcelHandler path to system path
            if excel_handler_path not in sys.path:
                sys.path.insert(0, excel_handler_path)
            
            # Import ExcelHandler class
            if self.logger:
                self.logger.info(f"⏳ Importing ExcelHandler from {excel_handler_path}...")
            
            from ExcelHandler import ExcelHandler
            
            # Create ExcelHandler instance
            self.excel_handler = ExcelHandler()
            
            if self.logger:
                self.logger.success("✅ ExcelHandler imported and initialized successfully")
                
        except ImportError as e:
            error_msg = f"Failed to import ExcelHandler: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise ImportError(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to initialize ExcelHandler: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def create_excel_with_sheets(self, filename: str, sheet_list: List[str]) -> bool:
        """
        Create a new Excel file with specified sheets
        
        Args:
            filename: Path to the Excel file to create
            sheet_list: List of sheet names to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.logger:
                self.logger.log_function_entry("create_excel_with_sheets", filename=filename, sheets=sheet_list)
                self.logger.info(f"⏳ Creating Excel file: {filename} with {len(sheet_list)} sheets...")
            
            self.excel_handler.create_excel_with_sheets(filename, sheet_list)
            
            if self.logger:
                self.logger.log_file_operation("CREATE", filename, "SUCCESS")
                self.logger.log_function_exit("create_excel_with_sheets", result="SUCCESS")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to create Excel file {filename}: {str(e)}")
                self.logger.log_exception("create_excel_with_sheets", e)
            return False
    
    def open_excel(self, filename: str, sheetname: Optional[str] = None) -> bool:
        """
        Open an Excel file and optionally load a specific sheet
        
        Args:
            filename: Path to the Excel file
            sheetname: Optional sheet name to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.logger:
                self.logger.log_function_entry("open_excel", filename=filename, sheetname=sheetname)
                self.logger.info(f"⏳ Opening Excel file: {filename}...")
            
            # Validate file exists
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Excel file not found: {filename}")
            
            self.excel_handler.open_excel(filename, sheetname)
            
            if self.logger:
                self.logger.log_file_operation("OPEN", filename, "SUCCESS")
                self.logger.log_function_exit("open_excel", result="SUCCESS")
            
            return True
            
        except FileNotFoundError as e:
            if self.logger:
                self.logger.error(f"❌ {str(e)}")
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to open Excel file {filename}: {str(e)}")
                self.logger.log_exception("open_excel", e)
            return False
    
    def save_excel(self) -> bool:
        """
        Save the currently open Excel file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.logger:
                self.logger.info("⏳ Saving Excel file...")
            
            self.excel_handler.save_excel()
            
            if self.logger:
                self.logger.success("✅ Excel file saved successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to save Excel file: {str(e)}")
                self.logger.log_exception("save_excel", e)
            return False
    
    def close_excel(self) -> bool:
        """
        Close the currently open Excel file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.logger:
                self.logger.info("⏳ Closing Excel file...")
            
            self.excel_handler.close_excel()
            
            if self.logger:
                self.logger.success("✅ Excel file closed successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to close Excel file: {str(e)}")
                self.logger.log_exception("close_excel", e)
            return False
    
    def read_excel_with_clean_columns(
        self,
        filepath: str,
        sheetname: str,
        column_names: List[str],
        starting_rowindex: int = 0
    ) -> Optional[List[List]]:
        """
        Read Excel file and return data with clean column names
        
        Args:
            filepath: Path to Excel file
            sheetname: Sheet name to read
            column_names: List of column names to read
            starting_rowindex: Starting row index (0-based)
            
        Returns:
            List of lists containing row data, or None if failed
        """
        try:
            if self.logger:
                self.logger.log_function_entry(
                    "read_excel_with_clean_columns",
                    filepath=filepath,
                    sheetname=sheetname,
                    columns=len(column_names)
                )
                self.logger.info(f"⏳ Reading Excel: {filepath}, Sheet: {sheetname}...")
            
            # Validate file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Excel file not found: {filepath}")
            
            result = self.excel_handler.read_excel_with_clean_columns(
                filepath, sheetname, column_names, starting_rowindex
            )
            
            if self.logger:
                self.logger.log_file_operation("READ", filepath, "SUCCESS")
                self.logger.success(f"✅ Read {len(result)} rows from {sheetname}")
                self.logger.log_function_exit("read_excel_with_clean_columns", result=f"{len(result)} rows")
            
            return result
            
        except FileNotFoundError as e:
            if self.logger:
                self.logger.error(f"❌ {str(e)}")
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to read Excel file: {str(e)}")
                self.logger.log_exception("read_excel_with_clean_columns", e)
            return None
    
    def parse_excel_with_dynamic_header(
        self,
        filepath: str,
        sheetname: str,
        column_names: List[str]
    ) -> Optional[List[List]]:
        """
        Parse Excel with dynamic header detection
        
        Args:
            filepath: Path to Excel file
            sheetname: Sheet name
            column_names: Column names to find
            
        Returns:
            List of lists or None if failed
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Parsing Excel with dynamic header: {filepath}...")
            
            result = self.excel_handler.parse_excel_with_dynamic_header(
                filepath, sheetname, column_names
            )
            
            if self.logger:
                self.logger.success(f"✅ Parsed {len(result)} rows")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to parse Excel: {str(e)}")
            return None
    
    def xls_parse_colored_cells(
        self,
        xls_file: str,
        sheet_name: str,
        header_name: str,
        start_row_index: int,
        color_status_map: Dict[Tuple[int, int, int], str]
    ) -> Optional[List]:
        """
        Parse XLS file for colored cells
        
        Args:
            xls_file: Path to XLS file
            sheet_name: Sheet name
            header_name: Header column name
            start_row_index: Starting row index
            color_status_map: Color to status mapping
            
        Returns:
            List of parsed data or None
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Parsing XLS colored cells: {xls_file}...")
            
            result = self.excel_handler.xls_parse_colored_cells(
                xls_file, sheet_name, header_name, start_row_index, color_status_map
            )
            
            if self.logger:
                self.logger.success(f"✅ Parsed {len(result)} colored cells")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to parse colored cells: {str(e)}")
            return None
    
    def xlsx_parse_colored_cells(
        self,
        xlsx_file: str,
        sheet_name: str,
        header_name: str,
        start_row_index: int,
        color_status_map: Dict[str, str]
    ) -> Optional[List]:
        """
        Parse XLSX file for colored cells
        
        Args:
            xlsx_file: Path to XLSX file
            sheet_name: Sheet name
            header_name: Header column name
            start_row_index: Starting row index
            color_status_map: Color to status mapping
            
        Returns:
            List of parsed data or None
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Parsing XLSX colored cells: {xlsx_file}...")
            
            result = self.excel_handler.xlsx_parse_colored_cells(
                xlsx_file, sheet_name, header_name, start_row_index, color_status_map
            )
            
            if self.logger:
                self.logger.success(f"✅ Parsed {len(result)} colored cells")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to parse XLSX colored cells: {str(e)}")
            return None
    
    def xlsx_parse_colored_multicells(
        self,
        xlsx_file: str,
        sheet_names: List[str],
        header_names: List[str],
        start_row_index: int,
        color_status_map: Dict[str, str]
    ) -> Optional[List]:
        """
        Parse XLSX file with multiple sheets and colored cells
        
        Args:
            xlsx_file: Path to XLSX file
            sheet_names: List of sheet names
            header_names: List of header names
            start_row_index: Starting row index
            color_status_map: Color to status mapping
            
        Returns:
            List of parsed data or None
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Parsing XLSX multi-sheet colored cells: {xlsx_file}...")
            
            result = self.excel_handler.xlsx_parse_colored_multicells(
                xlsx_file, sheet_names, header_names, start_row_index, color_status_map
            )
            
            if self.logger:
                self.logger.success(f"✅ Parsed {len(result)} rows from multiple sheets")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to parse multi-sheet colored cells: {str(e)}")
            return None
    
    def get_column_number(self, file_path: str, sheet_name: str, header_name: str) -> Optional[int]:
        """
        Get column number for a given header name
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            header_name: Header name to find
            
        Returns:
            Column number (1-based) or None if not found
        """
        try:
            if self.logger:
                self.logger.debug(f"Finding column number for header: {header_name}")
            
            col_num = self.excel_handler.get_column_number(file_path, sheet_name, header_name)
            
            if self.logger:
                self.logger.debug(f"Column '{header_name}' found at position {col_num}")
            
            return col_num
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to get column number: {str(e)}")
            return None
    
    def set_cell_value(
        self,
        filepath: str,
        worksheet_name: str,
        column: int,
        row: int,
        value: Any
    ) -> bool:
        """
        Set value in a specific cell
        
        Args:
            filepath: Path to Excel file
            worksheet_name: Worksheet name
            column: Column index (1-based)
            row: Row index (1-based)
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.debug(f"Setting cell value at ({row}, {column})")
            
            self.excel_handler.set_cell_value(filepath, worksheet_name, column, row, value)
            
            if self.logger:
                self.logger.debug(f"✅ Cell value updated successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to set cell value: {str(e)}")
            return False
    
    def update_excel_with_customer_data(
        self,
        file_path: str,
        sheet_name: str,
        customer_dict: Dict[int, str],
        data_dict: Dict[str, Any],
        customer_id: int
    ) -> bool:
        """
        Update Excel with customer-specific data
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            customer_dict: Customer ID to column name mapping
            data_dict: Data to update
            customer_id: Current customer ID
            
        Returns:
            bool: True if successful
        """
        try:
            if self.logger:
                self.logger.info(f"⏳ Updating Excel with customer data (ID: {customer_id})...")
            
            self.excel_handler.update_excel_with_customer_data(
                file_path, sheet_name, customer_dict, data_dict, customer_id
            )
            
            if self.logger:
                self.logger.success(f"✅ Excel updated with customer {customer_id} data")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to update customer data: {str(e)}")
            return False
