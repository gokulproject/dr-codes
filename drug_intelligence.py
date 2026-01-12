# drug_intelligence.py
import os
import shutil
from Config import Config
from Logger import LOGGER
from database import connect_to_db, execute_query, disconnect_from_db
from Processors import get_excluded_salt_2, process_drug_names, process_caplin, process_bells, process_relonchem, process_marksans_usa, process_padagis_usa, process_padagis_israel
from email_creation import send_email
from excel_creation import read_excel_with_clean_columns, xls_parse_colored_cells, xlsx_parse_colored_cells, xlsx_parse_colored_multicells, open_excel, close_excel, generate_include_exclude_count_report, generate_overall_report_generator, create_excel_report
from DataProcessing import DataProcessing  # External import from DataProcessing folder

process_id = None
master_tracker_path = None
master_tracker_filename = None
excluded_saltnames = []
di_output_dir = None  # Set dynamically
di_excel_report = None  # Set path

def initialize_process():
    """INITIALIZE_PROCESS logic."""
    global process_id, master_tracker_path, master_tracker_filename, excluded_saltnames, di_output_dir, di_excel_report
    LOGGER.info("Starting process initialization.")
    conn = connect_to_db()
    try:
        query_out = execute_query(conn, f"SELECT value FROM {Config.VARIABLE_TABLE} where name IN ('MTU Source Path','Customer Table')", fetch='all')
        Config.DRUG_INTELLIGENCE_PATH = query_out[0]['value']
        Config.CUSTOMER_TABLE = query_out[1]['value']
        LOGGER.info(f"Paths fetched: {Config.DRUG_INTELLIGENCE_PATH}")

        Config.MASTER_TRACKER_DIRPATH = os.path.join(Config.DRUG_INTELLIGENCE_PATH, 'BOT-IN', 'Master_Tracker')
        Config.CLIENT_DIRPATH = os.path.join(Config.DRUG_INTELLIGENCE_PATH, 'BOT-IN', 'Clients')
        Config.BOT_OUTPATH = os.path.join(Config.DRUG_INTELLIGENCE_PATH, 'BOT-OUT')
        Config.BOT_PROCESSPATH = os.path.join(Config.DRUG_INTELLIGENCE_PATH, 'BOT-PROCESS')
        Config.BOT_PROCESSEDPATH = os.path.join(Config.BOT_PROCESSPATH, 'Processed')
        Config.BOT_FAILEDPATH = os.path.join(Config.BOT_PROCESSPATH, 'Failed')
        Config.BOT_INPROGRESSPATH = os.path.join(Config.BOT_PROCESSPATH, 'Inprogress')
        LOGGER.info("Paths set successfully.")

        os.makedirs(Config.MASTER_TRACKER_DIRPATH, exist_ok=True)
        LOGGER.info(f"Directory created/checked: {Config.MASTER_TRACKER_DIRPATH}")

        list_excel_files = [f for f in os.listdir(Config.MASTER_TRACKER_DIRPATH) if f.lower().endswith('.xlsx')]
        client_files = []
        for root, _, files in os.walk(Config.CLIENT_DIRPATH):
            for file in files:
                if file.lower().endswith(('.xls', '.xlsx')):
                    client_files.append(os.path.join(root, file))

        client_files_count = len(client_files)
        list_excel_files_len = len(list_excel_files)
        if list_excel_files_len == 0 or client_files_count == 0:
            LOGGER.info("There is no Master Tracker/Client Files. Process stopping.")
            return

        query_out = execute_query(conn, f"SELECT value FROM {Config.VARIABLE_TABLE} where name IN ('MT Sheetname', 'MT Product Colname', 'Mail Configuration Table','MTU Table Names Table','MT Column Names Table','MT Comment Colname','MTU Default Remark Comment','MT SNo Colname')", fetch='all')

        master_tracker_path = os.path.join(Config.MASTER_TRACKER_DIRPATH, list_excel_files[0])
        Config.MASTER_SHEETNAME = query_out[0]['value']
        master_tracker_filename = list_excel_files[0]
        Config.MASTER_TRACKER_PRODUCTCOL = query_out[1]['value']
        Config.MAIL_CONFIG_TABLE = query_out[2]['value']
        Config.MTU_TABLENAMES_TABLE = query_out[3]['value']
        Config.MT_COLUMNNAME_TABLE = query_out[4]['value']
        Config.COMMENT_COLNAME = query_out[5]['value']
        Config.REMARK_DEFAULT_VALUE = query_out[6]['value']
        Config.SNO_COLNAME = query_out[7]['value']
        LOGGER.info("Variables fetched from DB.")

        mail_query = execute_query(conn, f"SELECT value FROM {Config.MAIL_CONFIG_TABLE} WHERE name IN ('Success To Address', 'Success Cc Address', 'Failure To Address', 'Failure Cc Address', 'Success Mail Subject', 'Failure Mai Subject', 'Success Mail Body', 'Failure Mail Body')", fetch='all')

        Config.SUCCESS_TO_ADDRESS = mail_query[0]['value']
        Config.SUCCESS_CC_ADDRESS = mail_query[1]['value']
        Config.FAILURE_TO_ADDRESS = mail_query[2]['value']
        Config.FAILURE_CC_ADDRESS = mail_query[3]['value']
        Config.SUCCESS_MAIL_SUBJECT = mail_query[4]['value']
        Config.FAILURE_MAIL_SUBJECT = mail_query[5]['value']
        Config.SUCCESS_MAIL_BODY = mail_query[6]['value']
        Config.FAILURE_MAIL_BODY = mail_query[7]['value']
        LOGGER.info("Mail configurations fetched.")

        mtu_query = execute_query(conn, f"SELECT value FROM {Config.MTU_TABLENAMES_TABLE} WHERE name IN ('process_status','suprocess_info','master_tracker_updates','overall_count_report','inclusion_exclusion_counts','salt_exclusion_list','caplin_master_report','bells_master_report','marksans_usa_master_report','relonchem_master_report','padagis_israle_master_report','padagis_usa_master_report','log_report') ORDER BY CASE name WHEN 'process_status' THEN 1 WHEN 'suprocess_info' THEN 2 WHEN 'master_tracker_updates' THEN 3 WHEN 'overall_count_report' THEN 4 WHEN 'inclusion_exclusion_counts' THEN 5 WHEN 'salt_exclusion_list' THEN 6 WHEN 'caplin_master_report' THEN 7 WHEN 'bells_master_report' THEN 8 WHEN 'marksans_usa_master_report' THEN 9 WHEN 'relonchem_master_report' THEN 10 WHEN 'padagis_israle_master_report' THEN 11 WHEN 'padagis_usa_master_report' THEN 12 WHEN 'log_report' THEN 13 ELSE 14 END", fetch='all')

        Config.PROCESS_STATUS = mtu_query[0]['value']
        Config.SUPROCESS_INFO = mtu_query[1]['value']
        Config.MASTER_TRACKER_UPDATES = mtu_query[2]['value']
        Config.OVERALL_COUNT_REPORT = mtu_query[3]['value']
        Config.INCLUSION_EXCLUSION_COUNTS = mtu_query[4]['value']
        Config.SALT_EXCLUSION_LIST = mtu_query[5]['value']
        Config.CAPLIN_MASTER_REPORT = mtu_query[6]['value']
        Config.BELLS_MASTER_REPORT = mtu_query[7]['value']
        Config.MARKSANS_USA_MASTER_REPORT = mtu_query[8]['value']
        Config.RELONCHEM_MASTER_REPORT = mtu_query[9]['value']
        Config.PADAGIS_ISRALE_MASTER_REPORT = mtu_query[10]['value']
        Config.PADAGIS_USA_MASTER_REPORT = mtu_query[11]['value']
        Config.LOG_REPORT = mtu_query[12]['value']
        LOGGER.info("Table names fetched.")

        move_to_inprogress()

        validate_master_tracker()

        exclued_salt = execute_query(conn, f"SELECT saltname FROM {Config.SALT_EXCLUSION_LIST} WHERE status=1", fetch='all')
        excluded_saltnames = [item['saltname'] for item in exclued_salt]
        Config.EXCLUDED_SALTNAMES = excluded_saltnames
        LOGGER.info("Excluded salt names fetched.")

        di_output_dir = os.path.join(Config.BOT_OUTPATH, str(process_id))
        os.makedirs(di_output_dir, exist_ok=True)
        LOGGER.info(f"Output directory created: {di_output_dir}")

        Config.BOT_PROCESSEDPATH = os.path.join(Config.BOT_PROCESSEDPATH, str(process_id))
        Config.BOT_FAILEDPATH = os.path.join(Config.BOT_FAILEDPATH, str(process_id))
        os.makedirs(Config.BOT_PROCESSEDPATH, exist_ok=True)
        os.makedirs(Config.BOT_FAILEDPATH, exist_ok=True)
        LOGGER.info("Processed and failed paths updated.")

        di_excel_report = os.path.join(di_output_dir, 'Drug_Intelligence_Report.xlsx')

        create_excel_report(di_excel_report)

        execute_query(conn, f"TRUNCATE table {Config.OVERALL_COUNT_REPORT}")
        execute_query(conn, f"TRUNCATE table {Config.INCLUSION_EXCLUSION_COUNTS}")
        LOGGER.info("Tables truncated.")

        LOGGER.info("Process initialization completed successfully.")
    except Exception as e:
        LOGGER.error(f"Initialization failed: {e}")
        raise e
    finally:
        disconnect_from_db(conn)

def move_to_inprogress():
    """MOVE_TO_INPROGRESS logic."""
    global process_id, master_tracker_path, master_tracker_filename
    LOGGER.info("Starting move to inprogress.")
    conn = connect_to_db()
    try:
        master_tracker_filename = os.path.basename(master_tracker_path)
        execute_query(conn, f"INSERT INTO {Config.PROCESS_STATUS} (process_status, mt_filename, start_datetime) VALUES ('Initiated', %s, NOW())", params=(master_tracker_filename,))
        maxid = execute_query(conn, f"SELECT MAX(process_id) FROM {Config.PROCESS_STATUS}", fetch='one')
        process_id = maxid['MAX(process_id)']
        LOGGER.info(f"Process ID created: {process_id}")

        os.makedirs(Config.BOT_INPROGRESSPATH, exist_ok=True)
        for root, dirs, files in os.walk(Config.BOT_INPROGRESSPATH):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                shutil.rmtree(os.path.join(root, dir))
        LOGGER.info("Inprogress directory emptied.")

        shutil.move(master_tracker_path, Config.BOT_INPROGRESSPATH)
        master_tracker_path = os.path.join(Config.BOT_INPROGRESSPATH, master_tracker_filename)
        LOGGER.info(f"File moved to inprogress: {master_tracker_path}")

        update_status('File Moved to Inprogress')
        LOGGER.info("Move to inprogress completed successfully.")
    except Exception as e:
        LOGGER.error(f"Move to inprogress failed: {e}")
    finally:
        disconnect_from_db(conn)

def update_status(status):
    """UPDATE_STAUTS logic."""
    LOGGER.info(f"Updating status to: {status}")
    conn = connect_to_db()
    try:
        execute_query(conn, f"UPDATE {Config.PROCESS_STATUS} SET process_status = %s WHERE process_id = %s", params=(status, process_id))
        LOGGER.info(f"Status updated successfully to: {status}")
    except Exception as e:
        LOGGER.error(f"Update status failed: {status} - {e}")
    finally:
        disconnect_from_db(conn)

def validate_master_tracker():
    """VALIDATE_MASTER_TRACKER logic."""
    LOGGER.info("Starting master tracker validation.")
    update_status('Master Tracker Validation Initiated')
    conn = connect_to_db()
    try:
        column_names_query = execute_query(conn, f"SELECT excel_colname FROM {Config.MT_COLUMNNAME_TABLE} WHERE status='1'", fetch='all')
        column_names = [Config.MASTER_TRACKER_PRODUCTCOL] + [item['excel_colname'] for item in column_names_query]
        full_colnames = column_names.copy()
        full_colnames.append(Config.COMMENT_COLNAME)
        LOGGER.info("Column names fetched for validation.")

        try:
            read_excel_with_clean_columns(master_tracker_path, Config.MASTER_SHEETNAME, full_colnames)
            LOGGER.info("Master tracker parsed successfully.")
        except Exception as e:
            LOGGER.error(f"Parse failed during validation: {e}")
            move_to_failed("Wrong Master Tracker File was upload - Column/Sheet not found")
            return

        comment_colno = get_column_number(master_tracker_path, Config.MASTER_SHEETNAME, Config.COMMENT_COLNAME)
        Config.COMMENT_COLNO = comment_colno
        LOGGER.info(f"Comment column number found: {comment_colno}")

        update_status('Master Tracker Validation Completed')
        LOGGER.info("Master tracker validation completed successfully.")
    except Exception as e:
        LOGGER.error(f"Validate master tracker failed: {e}")
    finally:
        disconnect_from_db(conn)

def get_column_number(file_path, sheet_name, col_name):
    """get_column_number logic."""
    LOGGER.info(f"Getting column number for '{col_name}' in {file_path}")
    try:
        wb = load_workbook(file_path, read_only=True)
        ws = wb[sheet_name]
        header_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
        for idx, header in enumerate(header_row, 1):
            if str(header).strip() == col_name:
                LOGGER.info(f"Column number found: {idx}")
                return idx
        LOGGER.warning(f"Column '{col_name}' not found.")
        return None
    except Exception as e:
        LOGGER.error(f"Get column number failed: {e}")
        return None

def master_tracker_update():
    """MASTER_TRACKER_UPDATE logic."""
    LOGGER.info("Starting master tracker update.")
    conn = connect_to_db()
    try:
        customer_list = execute_query(conn, f"SELECT customer_id, customer_name FROM {Config.CUSTOMER_TABLE} WHERE status = 1", fetch='all')
        LOGGER.info(f"Fetched {len(customer_list)} customers.")

        for customer in customer_list:
            execute_each_customer(customer)

        generate_report()

        move_to_bot_out()

        execute_query(conn, f"UPDATE {Config.PROCESS_STATUS} SET process_status='Completed', end_datetime=NOW() WHERE process_id=%s", params=(process_id,))
        LOGGER.info("Master tracker update completed successfully.")
    except Exception as e:
        LOGGER.error(f"Master tracker update failed: {e}")
    finally:
        disconnect_from_db(conn)

def execute_each_customer(customer_info):
    """EXECUTE_EACH_CUSTOMER logic."""
    customer_id = customer_info['customer_id']
    customer_name = customer_info['customer_name']
    LOGGER.info(f"Processing customer: {customer_name} (ID: {customer_id})")
    
    conn = connect_to_db()
    try:
        query_out = execute_query(conn, f"SELECT suprocess_name,excel_sheetname,excel_startindex,column_names FROM {Config.SUPROCESS_INFO} WHERE customer_id=%s", params=(customer_id,), fetch='all')
        
        query_len = len(query_out)
        if query_len == 0:
            LOGGER.info(f"No subprocess for customer: {customer_name}. Skipping.")
            return

        suprocess_name = query_out[0]['suprocess_name']
        customer_sheetname = query_out[0]['excel_sheetname']
        excel_row_startind = query_out[0]['excel_startindex']
        excel_colnames = query_out[0]['column_names']
        LOGGER.info(f"Subprocess info fetched for {customer_name}: {suprocess_name}")

        customer_foldername = customer_name
        customer_dirpath = os.path.join(Config.CLIENT_DIRPATH, customer_foldername)
        os.makedirs(customer_dirpath, exist_ok=True)
        LOGGER.info(f"Customer directory checked/created: {customer_dirpath}")

        list_files = [f for f in os.listdir(customer_dirpath) if f.lower().endswith(('.xls', '.xlsx'))]
        files_count = len(list_files)
        if files_count == 0:
            LOGGER.info(f"No files for customer: {customer_name}. Skipping.")
            return

        in_client_filepath = os.path.join(customer_dirpath, list_files[0])
        LOGGER.info(f"Client file found: {in_client_filepath}")

        execute_query(conn, f"INSERT INTO {Config.LOG_REPORT} (process_id,customer_id,initiated_sts,start_datetime,customer_name,filename) VALUES (%s,%s,'1',NOW(),%s,%s)", params=(process_id, customer_id, customer_name, list_files[0]))
        LOGGER.info("Log report inserted.")

        maxid = execute_query(conn, f"SELECT MAX(log_id) FROM {Config.LOG_REPORT} WHERE process_id=%s AND customer_id=%s", params=(process_id, customer_id), fetch='one')
        log_id = maxid['MAX(log_id)']
        LOGGER.info(f"Log ID fetched: {log_id}")

        client_inprogress_dir = os.path.join(Config.BOT_INPROGRESSPATH, customer_name)
        os.makedirs(client_inprogress_dir, exist_ok=True)
        for file in os.listdir(client_inprogress_dir):
            os.remove(os.path.join(client_inprogress_dir, file))
        LOGGER.info(f"Inprogress dir for customer emptied: {client_inprogress_dir}")

        client_filepath = os.path.join(client_inprogress_dir, list_files[0])
        shutil.move(in_client_filepath, client_filepath)
        LOGGER.info(f"File moved to inprogress: {client_filepath}")

        process_map = {
            'PROCESS_CAPLIN': process_caplin,
            'PROCESS_BELLS': process_bells,
            'PROCESS_RELONCHEM': process_relonchem,
            'PROCESS_MARKSANS_USA': process_marksans_usa,
            'PROCESS_PADAGIS_USA': process_padagis_usa,
            'PROCESS_PADAGIS_ISRAEL': process_padagis_israel,
        }

        process_func = process_map.get(suprocess_name)
        if process_func:
            process_status = process_func(client_filepath, excel_colnames, customer_sheetname, excel_row_startind)
            LOGGER.info(f"Subprocess {suprocess_name} executed with status: {process_status}")
        else:
            process_status = False
            LOGGER.warning(f"Unknown subprocess: {suprocess_name}")

        if not process_status:
            move_failed_clientfile(customer_name, client_filepath, log_id)
        else:
            move_to_processed(customer_name, client_filepath)

        execute_query(conn, f"UPDATE {Config.LOG_REPORT} SET completed_sts='1', end_datetime=NOW() WHERE log_id=%s", params=(log_id,))
        LOGGER.info(f"Customer {customer_name} processing completed.")
    except Exception as e:
        LOGGER.error(f"Execute customer failed: {customer_name} - {e}")
    finally:
        disconnect_from_db(conn)

def generate_report():
    """GENERATE_REPORT logic."""
    LOGGER.info("Starting report generation.")
    try:
        handler = open_excel(di_excel_report)
        generate_include_exclude_count_report(handler)
        generate_overall_report_generator(handler)
        close_excel(handler)
        LOGGER.info("Report generation completed successfully.")
    except Exception as e:
        LOGGER.error(f"Generate report failed: {e}")

def move_to_bot_out():
    """MOVE_TO_BOT-OUT logic."""
    LOGGER.info("Starting move to BOT-OUT.")
    conn = connect_to_db()
    try:
        completed_query = execute_query(conn, f"SELECT customer_name, filename FROM {Config.LOG_REPORT} WHERE completed_sts='1' AND process_id=%s", params=(process_id,), fetch='all')
        failed_query = execute_query(conn, f"SELECT customer_name, filename, failure_message FROM {Config.LOG_REPORT} WHERE failed_sts='1' AND process_id=%s", params=(process_id,), fetch='all')
        LOGGER.info(f"Fetched completed: {len(completed_query)}, failed: {len(failed_query)}")

        completed_query_len = len(completed_query)
        failed_query_len = len(failed_query)

        if completed_query_len == 0 and failed_query_len != 0:
            error_message = "Below files failed during processing:\n\n" + "\n".join(f"{i+1}) {f['customer_name']} - {f['filename']}" for i, f in enumerate(failed_query)) if failed_query else "NA"
            move_to_failed(error_message)
        else:
            shutil.move(master_tracker_path, di_output_dir)
            LOGGER.info(f"Master tracker moved to output dir: {di_output_dir}")

            attachments = []
            list_files = [f for f in os.listdir(di_output_dir) if f.lower().endswith('.xlsx')]
            for file in list_files:
                full_path = os.path.join(di_output_dir, file)
                if "Conflict" in file:
                    os.remove(full_path)
                    LOGGER.info(f"Removed conflict file: {full_path}")
                else:
                    attachments.append(full_path)

            attachments_str = ';'.join(attachments)
            LOGGER.info(f"Attachments prepared: {attachments_str}")

            suceess_failed_files = "Success Files:\n" + ("\n".join(f"{i+1}) {c['customer_name']} - {c['filename']}" for i, c in enumerate(completed_query)) if completed_query else "NA") + "\n\nFailed Files:\n" + ("\n".join(f"{i+1}) {f['customer_name']} - {f['filename']} - {f['failure_message']}" for i, f in enumerate(failed_query)) if failed_query else "NA"

            success_mail_body = Config.SUCCESS_MAIL_BODY.replace("<FILES>", suceess_failed_files).replace("<>", "\n")

            send_email(Config.SUCCESS_TO_ADDRESS, Config.SUCCESS_MAIL_SUBJECT, success_mail_body, attachments=attachments_str, cc_address=Config.SUCCESS_CC_ADDRESS)
            LOGGER.info("Success email sent.")

            for root, dirs, files in os.walk(Config.BOT_INPROGRESSPATH):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    shutil.rmtree(os.path.join(root, dir))
            LOGGER.info("Inprogress directory cleared.")

        LOGGER.info("Move to BOT-OUT completed successfully.")
    except Exception as e:
        LOGGER.error(f"Move to BOT-OUT failed: {e}")
    finally:
        disconnect_from_db(conn)

def move_to_processed(customer_name, client_filepath):
    """MOVE_TO_PROCESSED logic."""
    LOGGER.info(f"Starting move to processed for {customer_name}: {client_filepath}")
    try:
        client_processed_dir = os.path.join(Config.BOT_PROCESSEDPATH, customer_name)
        os.makedirs(client_processed_dir, exist_ok=True)
        LOGGER.info(f"Processed dir checked/created: {client_processed_dir}")
        shutil.move(client_filepath, client_processed_dir)
        LOGGER.info(f"Moved to processed successfully: {client_filepath}")
    except Exception as e:
        LOGGER.error(f"Move to processed failed: {e}")

def move_failed_clientfile(customer_name, client_filepath, log_id):
    """MOVE_FAILED_CLIENTFILE logic."""
    LOGGER.info(f"Starting move failed client file for {customer_name}: {client_filepath}")
    try:
        client_failed_dir = os.path.join(Config.BOT_FAILEDPATH, customer_name)
        os.makedirs(client_failed_dir, exist_ok=True)
        LOGGER.info(f"Failed dir checked/created: {client_failed_dir}")
        shutil.move(client_filepath, client_failed_dir)
        filename = os.path.basename(client_filepath)
        conn = connect_to_db()
        execute_query(conn, f"UPDATE {Config.LOG_REPORT} SET failed_sts='1', failure_message='Failed while processing {customer_name} customer - {filename}', end_datetime=NOW() WHERE log_id=%s", params=(log_id,))
        LOGGER.info(f"Moved failed client file successfully: {client_filepath}")
    except Exception as e:
        LOGGER.error(f"Move failed client file failed: {e}")
    finally:
        disconnect_from_db(conn)

def move_to_failed(error_message):
    """MOVE_TO_FAILED logic."""
    LOGGER.info(f"Starting move to failed with message: {error_message}")
    try:
        os.makedirs(Config.BOT_FAILEDPATH, exist_ok=True)
        LOGGER.info(f"Failed path checked/created: {Config.BOT_FAILEDPATH}")
        shutil.move(master_tracker_path, Config.BOT_FAILEDPATH)
        shutil.move(di_output_dir, Config.BOT_FAILEDPATH)
        LOGGER.info("Files moved to failed.")

        conn = connect_to_db()
        execute_query(conn, f"UPDATE {Config.PROCESS_STATUS} SET process_status='Failed', error_message=%s, end_datetime=NOW() WHERE process_id=%s", params=(error_message, process_id))
        LOGGER.info("Process status updated to Failed.")

        filename = os.path.basename(master_tracker_path)
        attachment = os.path.join(Config.BOT_FAILEDPATH, filename)

        failure_mail_body = Config.FAILURE_MAIL_BODY.replace("<process_id>", f" {process_id} - {filename} - {error_message}").replace("<>", "\n")

        send_email(Config.FAILURE_TO_ADDRESS, Config.FAILURE_MAIL_SUBJECT, failure_mail_body, attachments=attachment, cc_address=Config.FAILURE_CC_ADDRESS)
        LOGGER.info("Failure email sent.")
        LOGGER.info(error_message)
    except Exception as e:
        LOGGER.error(f"Move to failed failed: {e}")
    finally:
        disconnect_from_db(conn)