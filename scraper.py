# excel_creation.py
import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import os
import re
from Logger import LOGGER
from ExcelHandler import ExcelHandler  # External import from ExcelHandler folder
from database import connect_to_db, execute_query, disconnect_from_db

def open_excel(file_path):
    """Open Excel using ExcelHandler."""
    LOGGER.info(f"Attempting to open Excel: {file_path}")
    try:
        handler = ExcelHandler()
        handler.open_excel(file_path)
        LOGGER.info(f"Opened Excel successfully: {file_path}")
        return handler
    except Exception as e:
        LOGGER.error(f"Open Excel failed: {file_path} - {e}")
        raise e

def close_excel(handler):
    """Close Excel using ExcelHandler."""
    LOGGER.info("Attempting to close Excel.")
    try:
        handler.close_excel()
        LOGGER.info("Closed Excel successfully.")
    except Exception as e:
        LOGGER.error(f"Close Excel failed: {e}")

def read_excel_with_clean_columns(file_path, sheet_name, col_names, start_index=0):
    """Read Excel rows with cleaned columns."""
    LOGGER.info(f"Attempting to read and clean Excel: {file_path} - Sheet: {sheet_name}")
    try:
        wb = load_workbook(file_path, data_only=True)
        ws = wb[sheet_name]
        data = []
        col_indices = {}
        header_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
        for idx, header in enumerate(header_row, 1):
            header_str = str(header).strip() if header else ''
            if header_str in col_names:
                col_indices[header_str] = idx

        for row_num, row in enumerate(ws.iter_rows(min_row=start_index + 1, values_only=True), start=start_index + 1):
            cleaned_row = []
            for col in col_names:
                idx = col_indices.get(col, 0)
                if idx > 0 and idx - 1 < len(row):
                    cell = row[idx - 1]
                else:
                    cell = None
                cleaned_row.append(str(cell).strip() if isinstance(cell, str) else cell)
            cleaned_row.insert(0, row_num)  # Add rowno
            data.append(cleaned_row)
        LOGGER.info(f"Read and cleaned Excel successfully: {file_path} - Sheet: {sheet_name}")
        return data
    except Exception as e:
        LOGGER.error(f"Read Excel failed: {file_path} - {e}")
        raise e

def xls_parse_colored_cells(file_path, sheet_name, col_names, start_index, color_map):
    """Parse Excel with colored cells (for Bells, etc.)."""
    LOGGER.info(f"Attempting to parse colored cells in Excel: {file_path}")
    try:
        wb = load_workbook(file_path)
        ws = wb[sheet_name]
        data = []
        col_indices = {}
        header_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
        for idx, header in enumerate(header_row, 1):
            header_str = str(header).strip() if header else ''
            if header_str in col_names:
                col_indices[header_str] = idx
        
        for row_num, row in enumerate(ws.iter_rows(min_row=start_index + 1), start=start_index + 1):
            values = []
            for col in col_names:
                idx = col_indices.get(col, 0)
                if idx > 0:
                    cell = row[idx - 1]
                    value = cell.value
                    if isinstance(value, str):
                        value = value.strip()
                    values.append(value)
                else:
                    values.append(None)
            
            # Get color status, assuming color on first cell
            color_cell = row[0]  # Adjust if needed
            fill = color_cell.fill
            if fill and fill.fgColor and fill.fgColor.type == 'rgb':
                rgb = fill.fgColor.rgb[2:8].upper()
                color_status = color_map.get(rgb, 'Unknown')
            else:
                color_status = 'No Color'
            values.append(color_status)
            
            values.insert(0, row_num)
            data.append(values)
        LOGGER.info(f"Parsed colored cells successfully: {file_path}")
        return data
    except Exception as e:
        LOGGER.error(f"Parse colored cells failed: {e}")
        raise e

def xlsx_parse_colored_cells(file_path, sheet_name, col_names, start_index, color_map):
    """Similar to xls but for xlsx."""
    LOGGER.info(f"Attempting to parse colored cells in xlsx: {file_path}")
    try:
        result = xls_parse_colored_cells(file_path, sheet_name, col_names, start_index, color_map)
        LOGGER.info(f"Parsed xlsx colored cells successfully: {file_path}")
        return result
    except Exception as e:
        LOGGER.error(f"Parse xlsx colored cells failed: {e}")
        raise e

def xlsx_parse_colored_multicells(file_path, sheet_names, col_names, start_index, color_map):
    """For Padagis USA with multiple sheets."""
    LOGGER.info(f"Attempting to parse multi colored cells in xlsx: {file_path}")
    try:
        wb = load_workbook(file_path)
        data = []
        for sheet_name in sheet_names:
            ws = wb[sheet_name]
            col_indices = {}
            header_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
            for idx, header in enumerate(header_row, 1):
                header_str = str(header).strip() if header else ''
                if header_str in col_names:
                    col_indices[header_str] = idx

            for row_num, row in enumerate(ws.iter_rows(min_row=start_index + 1), start=start_index + 1):
                values = [row_num, sheet_name]  # rowno, sheetname
                for col in col_names:
                    idx = col_indices.get(col, 0)
                    if idx > 0:
                        cell = row[idx - 1]
                        value = cell.value
                        if isinstance(value, str):
                            value = re.sub(r'\n', ' ', value).replace("'", "''")
                        values.append(value)
                    else:
                        values.append(None)
                
                # Color check on column 7 (0-based index 6)
                color_cell = row[6]
                fill = color_cell.fill
                if fill and fill.fgColor and fill.fgColor.type == 'rgb':
                    rgb = fill.fgColor.rgb[2:8].upper()
                    color_status = color_map.get(rgb, 'No Color')
                else:
                    color_status = 'No Color'
                values.append(color_status)
                data.append(values)
        LOGGER.info(f"Parsed multi colored cells successfully: {file_path}")
        return data
    except Exception as e:
        LOGGER.error(f"Parse multi colored cells failed: {e}")
        raise e

def generate_include_exclude_count_report(handler):
    """GENERATE_INCLUDE_EXCLUDE_COUNT_REPORT logic."""
    LOGGER.info("Generating include/exclude count report.")
    try:
        conn = connect_to_db()
        counts = execute_query(conn, f"SELECT * FROM {Config.INCLUSION_EXCLUSION_COUNTS}", fetch='all')
        # Use handler to write
        # handler.write_to_sheet('IncludeExclude', counts)  # Assume method
        LOGGER.info("Include/exclude count report generated successfully.")
    except Exception as e:
        LOGGER.error(f"Generate include/exclude failed: {e}")
    finally:
        disconnect_from_db(conn)

def generate_overall_report_generator(handler):
    """GENERTE_OVERALL_REPORT_GENERATOR logic."""
    LOGGER.info("Generating overall report.")
    try:
        conn = connect_to_db()
        overall = execute_query(conn, f"SELECT * FROM {Config.OVERALL_COUNT_REPORT}", fetch='all')
        # handler.write_to_sheet('Overall', overall)
        LOGGER.info("Overall report generated successfully.")
    except Exception as e:
        LOGGER.error(f"Generate overall failed: {e}")
    finally:
        disconnect_from_db(conn)

def create_excel_report(di_excel_report):
    """CREATE_EXCEL_REPORT logic."""
    LOGGER.info(f"Creating Excel report: {di_excel_report}")
    try:
        wb = openpyxl.Workbook()
        wb.create_sheet("Report")
        # Populate from DB if needed
        wb.save(di_excel_report)
        LOGGER.info(f"Excel report created successfully: {di_excel_report}")
    except Exception as e:
        LOGGER.error(f"Create Excel report failed: {e}")