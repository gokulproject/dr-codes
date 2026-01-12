# Processors.py
from database import connect_to_db, execute_query, disconnect_from_db
from excel_creation import read_excel_with_clean_columns, xls_parse_colored_cells, xlsx_parse_colored_cells, xlsx_parse_colored_multicells
from Logger import LOGGER
from DataProcessing import DataProcessing  # External
from Config import Config
import re

data_processor = DataProcessing()

def get_excluded_salt_2(active_ingredients):
    """GET_EXCLUDED_SALT_2 logic."""
    LOGGER.info("Starting get excluded salt.")
    try:
        active_ingredients = str(active_ingredients).strip()
        for salt in Config.EXCLUDED_SALTNAMES:
            active_ingredients = re.sub(re.escape(salt), '', active_ingredients, flags=re.IGNORECASE).strip()
        LOGGER.info("Get excluded salt completed successfully.")
        return active_ingredients
    except Exception as e:
        LOGGER.error(f"Get excluded salt failed: {e}")
        return active_ingredients

def process_drug_names(table_name):
    """PROCESS_DRUG_NAMES logic."""
    LOGGER.info(f"Starting process drug names for table: {table_name}")
    conn = connect_to_db()
    try:
        # Assume data_processor.process_drug_names(table_name, conn)
        data_processor.process_drug_names(table_name, conn)
        LOGGER.info(f"Process drug names completed successfully for {table_name}")
    except Exception as e:
        LOGGER.error(f"Process drug names failed: {table_name} - {e}")
    finally:
        disconnect_from_db(conn)

def process_caplin(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    """PROCESS_CAPLIN logic."""
    LOGGER.info("Starting PROCESS_CAPLIN.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.CAPLIN_MASTER_REPORT}")
        LOGGER.info(f"Truncated table {Config.CAPLIN_MASTER_REPORT}")

        colnames = excel_colnames.split(';')
        sheet_values = read_excel_with_clean_columns(client_filepath, customer_sheetname, colnames, int(excel_row_startind))

        for list_values in sheet_values:
            f_pdtname = get_excluded_salt_2(list_values[4])
            in_ex_sts = 'include' if list_values[-1] == '' else 'exclude'
            list_values.append(in_ex_sts)
            list_values = [str(s).strip() if isinstance(s, str) else s for s in list_values]
            remark = Config.REMARK_DEFAULT_VALUE if in_ex_sts == 'include' else 'Withdrawn date is present'

            params = (process_id, list_values[0], list_values[1], list_values[2], list_values[3], list_values[4], f_pdtname, list_values[5], in_ex_sts, remark)
            execute_query(conn, f"INSERT INTO {Config.CAPLIN_MASTER_REPORT} (process_id,rowno,productname,strength,unit,active_ingrediants,filtered_name,withdrawn_date,include_exclude_status,added_datetime,remark) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)", params=params)

        process_drug_names(Config.CAPLIN_MASTER_REPORT)
        LOGGER.info("PROCESS_CAPLIN completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_CAPLIN failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

# Similar logging additions for other processors...
def process_bells(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    LOGGER.info("Starting PROCESS_BELLS.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.BELLS_MASTER_REPORT}")
        color_map = {'CCFFFF': 'Marketed', '969696': 'Licence cancelled by MAH', 'FFCC99': 'Not Marketed'}

        excel_row_startind = int(excel_row_startind) - 1
        excel_values = xls_parse_colored_cells(client_filepath, customer_sheetname, excel_colnames.split(';'), excel_row_startind, color_map)

        for values in excel_values:
            filtered_name = get_excluded_salt_2(values[1])
            if values[3] == 'Licence cancelled by MAH':
                remark = 'Licence cancelled by MAH'
                inex_sts = 'exclude'
            else:
                remark = Config.REMARK_DEFAULT_VALUE
                inex_sts = 'include'

            params = (process_id, values[0], values[1], values[3], inex_sts, remark, filtered_name)
            execute_query(conn, f"INSERT INTO {Config.BELLS_MASTER_REPORT} (process_id, rowno, active_ingrediants, color_status, include_exclude_status, remark, added_datetime, filtered_name) VALUES (%s,%s,%s,%s,%s,%s,NOW(),%s)", params=params)

        process_drug_names(Config.BELLS_MASTER_REPORT)
        LOGGER.info("PROCESS_BELLS completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_BELLS failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

# Add for process_relonchem, process_marksans_usa, process_padagis_usa, process_padagis_israel similarly with LOGGER.info start/end/key steps.