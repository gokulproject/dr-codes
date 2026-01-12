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
            LOGGER.info("Inserted row into caplin_master_report.")

        process_drug_names(Config.CAPLIN_MASTER_REPORT)
        LOGGER.info("PROCESS_CAPLIN completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_CAPLIN failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

def process_bells(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    """PROCESS_BELLS logic."""
    LOGGER.info("Starting PROCESS_BELLS.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.BELLS_MASTER_REPORT}")
        LOGGER.info(f"Truncated table {Config.BELLS_MASTER_REPORT}")

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
            LOGGER.info("Inserted row into bells_master_report.")

        process_drug_names(Config.BELLS_MASTER_REPORT)
        LOGGER.info("PROCESS_BELLS completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_BELLS failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

def process_relonchem(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    """PROCESS_RELONCHEM logic."""
    LOGGER.info("Starting PROCESS_RELONCHEM.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.RELONCHEM_MASTER_REPORT}")
        LOGGER.info(f"Truncated table {Config.RELONCHEM_MASTER_REPORT}")

        color_map = {"9": "Marketed", "0": "Licence cancelled by the MAH", "7": "Licence Application Pending", "5": "Not Marketed", "8": "Invented name deleted", "FFFFFF00":"Newly Added"}

        excel_values = xlsx_parse_colored_cells(client_filepath, customer_sheetname, excel_colnames.split(';'), int(excel_row_startind), color_map)

        for values in excel_values:
            filtered_name = get_excluded_salt_2(values[1])
            color_status = values[3]
            if color_status in ["Marketed","Not Marketed","Newly Added","Invented name deleted"]:
                remark = Config.REMARK_DEFAULT_VALUE
                inex_sts = 'include'
            else:
                remark = color_status
                inex_sts = 'exclude'

            params = (process_id, values[0], values[1], color_status, inex_sts, remark, filtered_name)
            execute_query(conn, f"INSERT INTO {Config.RELONCHEM_MASTER_REPORT} (process_id, rowno, active_ingrediants, color_status, include_exclude_status, remark, added_datetime, filtered_name) VALUES (%s,%s,%s,%s,%s,%s,NOW(),%s)", params=params)
            LOGGER.info("Inserted row into relonchem_master_report.")

        process_drug_names(Config.RELONCHEM_MASTER_REPORT)
        LOGGER.info("PROCESS_RELONCHEM completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_RELONCHEM failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

def process_marksans_usa(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    """PROCESS_MARKSANS_USA logic."""
    LOGGER.info("Starting PROCESS_MARKSANS_USA.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.MARKSANS_USA_MASTER_REPORT}")
        LOGGER.info(f"Truncated table {Config.MARKSANS_USA_MASTER_REPORT}")

        startindex = int(excel_row_startind) - 1
        colnames = excel_colnames.split(';')
        rowvalues = read_excel_with_clean_columns(client_filepath, customer_sheetname, colnames, startindex)

        for values in rowvalues:
            drugname = str(values[1]).replace('\n', '')
            filtered_name = get_excluded_salt_2(drugname)
            approval_status = str(values[2]).strip().lower()
            withdrawn_date = str(values[3]).strip()
            if approval_status not in ['approved', '']:
                remark = "Approval Status is not Approved"
                inex_sts = "exclude"
            elif withdrawn_date != '':
                remark = "Withdrawn Date is not empty"
                inex_sts = "exclude"
            else:
                remark = Config.REMARK_DEFAULT_VALUE
                inex_sts = "include"

            params = (process_id, values[0], drugname, filtered_name, values[2], values[3], inex_sts, remark)
            execute_query(conn, f"INSERT INTO {Config.MARKSANS_USA_MASTER_REPORT} (process_id, rowno, active_ingrediants, filtered_name, approval_status, withdrawn_date, include_exclude_status, remark, added_datetime) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())", params=params)
            LOGGER.info("Inserted row into marksans_usa_master_report.")

        process_drug_names(Config.MARKSANS_USA_MASTER_REPORT)
        LOGGER.info("PROCESS_MARKSANS_USA completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_MARKSANS_USA failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

def process_padagis_usa(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    """PROCESS_PADAGIS_USA logic."""
    LOGGER.info("Starting PROCESS_PADAGIS_USA.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.PADAGIS_USA_MASTER_REPORT}")
        LOGGER.info(f"Truncated table {Config.PADAGIS_USA_MASTER_REPORT}")

        color_map = {'FFFF5050': 'Red'}

        sheetnames = customer_sheetname.split(';')
        colnames = excel_colnames.split(';')
        startindex = int(excel_row_startind)
        rowvalues = xlsx_parse_colored_multicells(client_filepath, sheetnames, colnames, startindex, color_map)

        for values in rowvalues:
            comment = str(values[8]).replace('\n', ' ').replace("'", "''")
            productname = str(values[5]).replace("'", "''")
            filtered_name = get_excluded_salt_2(productname)
            if values[1] == "Contract Manufactured Products":
                remark = "Not MAH product"
                inex_sts = "exclude"
            elif values[7] == "Red":
                remark = "Product Highlighted in Red"
                inex_sts = "exclude"
            elif "discontinued" in comment.lower():
                remark = comment
                inex_sts = "exclude"
            else:
                remark = Config.REMARK_DEFAULT_VALUE
                inex_sts = "include"

            params = (process_id, values[0], values[1], values[2], productname, comment, filtered_name, values[7], inex_sts, remark)
            execute_query(conn, f"INSERT INTO {Config.PADAGIS_USA_MASTER_REPORT} (process_id, rowno, sheetname, ndc_no,active_ingrediants,comment,filtered_name,color_status,include_exclude_status, remark, added_datetime) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())", params=params)
            LOGGER.info("Inserted row into padagis_usa_master_report.")

        process_drug_names(Config.PADAGIS_USA_MASTER_REPORT)
        LOGGER.info("PROCESS_PADAGIS_USA completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_PADAGIS_USA failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)

def process_padagis_israel(client_filepath, excel_colnames, customer_sheetname, excel_row_startind):
    """PROCESS_PADAGIS_ISRAEL logic."""
    LOGGER.info("Starting PROCESS_PADAGIS_ISRAEL.")
    conn = connect_to_db()
    try:
        execute_query(conn, f"TRUNCATE TABLE {Config.PADAGIS_ISRALE_MASTER_REPORT}")
        LOGGER.info(f"Truncated table {Config.PADAGIS_ISRALE_MASTER_REPORT}")

        colnames = excel_colnames.split(';')
        rowvalues = read_excel_with_clean_columns(client_filepath, customer_sheetname, colnames, int(excel_row_startind))

        for values in rowvalues:
            active_ingrediants = str(values[1])
            filtered_name = get_excluded_salt_2(active_ingrediants)
            remark = Config.REMARK_DEFAULT_VALUE
            inex_sts = 'include'

            params = (process_id, values[0], active_ingrediants, filtered_name, inex_sts, remark)
            execute_query(conn, f"INSERT INTO {Config.PADAGIS_ISRALE_MASTER_REPORT} (process_id, rowno, active_ingrediants, filtered_name,include_exclude_status, remark, added_datetime) VALUES (%s,%s,%s,%s,%s,%s,NOW())", params=params)
            LOGGER.info("Inserted row into padagis_israle_master_report.")

        process_drug_names(Config.PADAGIS_ISRALE_MASTER_REPORT)
        LOGGER.info("PROCESS_PADAGIS_ISRAEL completed successfully.")
        return True
    except Exception as e:
        LOGGER.error(f"PROCESS_PADAGIS_ISRAEL failed: {e}")
        return False
    finally:
        disconnect_from_db(conn)