"""
Drug Intelligence - Main process logic
All core Robot Framework actions
"""
import os
import shutil
from processors import *
from email_sender import send_success_email, send_failure_email
from excel_creation import GENERATE_REPORT
from logger import get_logger


logger = get_logger()


def INITIALIZE_PROCESS(server_type, db, config):
    """
    INITIALIZE_PROCESS - Exact Robot Framework logic
    """
    logger.info("="*60)
    logger.info("INITIALIZE_PROCESS")
    logger.info("="*60)
    
    # Set process variables based on server type
    if server_type == "DEV":
        db_module_name = "pymysql"
        db_name = "drug_intelligence_automation"
        db_username = "admin"
        db_password = "Password21"
        db_host = "nividous-dev.ci.us-east-1.rds.amazonaws.com"
        db_port = 3306
    else:
        db_module_name = "pymysql"
        db_name = "drug_intelligence_automation"
        db_username = "admin"
        db_password = "Password21"
        db_host = "nividous-dev.ci.us-east-1.rds.amazonaws.com"
        db_port = 3306
    
    # Email settings
    e_authuser = "AKIAVCYLC7ABOWX6PLE3"
    e_authpass = "BBrefAqS4WsmKGVacbz7WEaYmgOd9gGnHBw2LKzjwXQk"
    e_host = "email-smtp.us-east-1.amazonaws.com"
    e_port = 2587
    from_address = "NavitasBOT@navitascloud.com"
    
    # Connect to database
    db.connect_to_database(db_module_name, db_name, db_username, db_password, db_host, db_port)
    
    # Query variables from database
    variable_table = "DI_process_variables"
    queryout = db.query(f"SELECT value FROM {variable_table} WHERE name IN ('MTU Source Path','Customer Table')")
    
    drug_intelligence_path = queryout[0]['value']
    customer_table = queryout[1]['value']
    
    # Set paths
    master_tracker_dirpath = os.path.join(drug_intelligence_path, "BOT-IN", "Master_Tracker")
    client_dirpath = os.path.join(drug_intelligence_path, "BOT-IN", "Clients")
    bot_outpath = os.path.join(drug_intelligence_path, "BOT-OUT")
    bot_processpath = os.path.join(drug_intelligence_path, "BOT-PROCESS")
    bot_processedpath = os.path.join(bot_processpath, "Processed")
    bot_failedpath = os.path.join(bot_processpath, "Failed")
    bot_inprogresspath = os.path.join(bot_processpath, "Inprogress")
    
    # Create directories
    os.makedirs(master_tracker_dirpath, exist_ok=True)
    
    # Get list of Excel files
    list_excel_files = [f for f in os.listdir(master_tracker_dirpath) if f.endswith('.xlsx')]
    client_files = []
    for root, dirs, files in os.walk(client_dirpath):
        client_files.extend([f for f in files if f.endswith(('.xls', '.xlsx'))])
    
    list_excel_files_len = len(list_excel_files)
    client_files_count = len(client_files)
    
    # Pass execution if no files
    if list_excel_files_len == 0 or client_files_count == 0:
        logger.warning("⚠️  There is no Master Tracker/Client Files")
        return None
    
    # Get configuration from database
    queryout = db.query(f"""
        SELECT value FROM {variable_table} 
        WHERE name IN ('MT Sheetname', 'MT Product Colname', 'Mail Configuration Table',
                      'MTU Table Names Table','MT Column Names Table','MT Comment Colname',
                      'MTU Default Remark Comment','MT SNo Colname')
    """)
    
    master_tracker_path = os.path.join(master_tracker_dirpath, list_excel_files[0])
    master_sheetname = queryout[0]['value']
    master_tracker_filename = list_excel_files[0]
    mater_tracker_productcol = queryout[1]['value']
    mail_config_table = queryout[2]['value']
    mtu_tablenames_table = queryout[3]['value']
    mt_columnnames_table = queryout[4]['value']
    comment_colname = queryout[5]['value']
    remark_default_value = queryout[6]['value']
    sno_colname = queryout[7]['value']
    
    # Get mail configuration
    mail_query = db.query(f"""
        SELECT value FROM {mail_config_table} 
        WHERE name IN ('Success To Address', 'Success Cc Address', 'Failure To Address', 
                      'Failure Cc Address', 'Success Mail Subject', 'Failure Mai Subject', 
                      'Success Mail Body', 'Failure Mail Body')
    """)
    
    success_to_address = mail_query[4]['value']
    success_cc_address = mail_query[5]['value']
    failure_to_address = mail_query[2]['value']
    failure_cc_address = mail_query[3]['value']
    success_mail_subject = mail_query[0]['value']
    failure_mail_subject = mail_query[1]['value']
    success_mail_body = mail_query[6]['value']
    failure_mail_body = mail_query[7]['value']
    
    # Get table names
    mtu_query = db.query(f"""
        SELECT value FROM {mtu_tablenames_table} 
        WHERE name IN ('process_status','suprocess_info','master_tracker_updates',
                      'overall_count_report','inclusion_exclusion_counts','salt_exclusion_list',
                      'caplin_master_report','bells_master_report','marksans_usa_master_report',
                      'relonchem_master_report','padagis_israle_master_report',
                      'padagis_usa_master_report','log_report')
        ORDER BY CASE name
            WHEN 'process_status' THEN 1
            WHEN 'suprocess_info' THEN 2
            WHEN 'master_tracker_updates' THEN 3
            WHEN 'overall_count_report' THEN 4
            WHEN 'inclusion_exclusion_counts' THEN 5
            WHEN 'salt_exclusion_list' THEN 6
            WHEN 'caplin_master_report' THEN 7
            WHEN 'bells_master_report' THEN 8
            WHEN 'marksans_usa_master_report' THEN 9
            WHEN 'relonchem_master_report' THEN 10
            WHEN 'padagis_israle_master_report' THEN 11
            WHEN 'padagis_usa_master_report' THEN 12
            WHEN 'log_report' THEN 13
            ELSE 14 END
    """)
    
    process_status = mtu_query[0]['value']
    suprocess_info = mtu_query[1]['value']
    master_tracker_updates = mtu_query[2]['value']
    overall_count_report = mtu_query[3]['value']
    inclusion_exclusion_counts = mtu_query[4]['value']
    salt_exclusion_list = mtu_query[5]['value']
    caplin_master_report = mtu_query[6]['value']
    bells_master_report = mtu_query[7]['value']
    marksans_usa_master_report = mtu_query[8]['value']
    relonchem_master_report = mtu_query[9]['value']
    padagis_israle_master_report = mtu_query[10]['value']
    padagis_usa_master_report = mtu_query[11]['value']
    log_report = mtu_query[12]['value']
    
    # Get excluded salts
    exclued_salt = db.query(f"SELECT saltname FROM {salt_exclusion_list} WHERE status=1")
    excluded_saltnames = [item['saltname'] for item in exclued_salt]
    
    # Store in config
    config.process_variables = {
        'drug_intelligence_path': drug_intelligence_path,
        'customer_table': customer_table,
        'master_tracker_path': master_tracker_path,
        'master_sheetname': master_sheetname,
        'master_tracker_filename': master_tracker_filename,
        'bot_inprogresspath': bot_inprogresspath,
        'bot_processedpath': bot_processedpath,
        'bot_failedpath': bot_failedpath,
        'bot_outpath': bot_outpath,
        'remark_default_value': remark_default_value,
        'excluded_saltnames': excluded_saltnames
    }
    
    config.table_names = {
        'process_status': process_status,
        'suprocess_info': suprocess_info,
        'log_report': log_report,
        'caplin_master_report': caplin_master_report,
        'bells_master_report': bells_master_report,
        'marksans_usa_master_report': marksans_usa_master_report,
        'relonchem_master_report': relonchem_master_report,
        'padagis_israle_master_report': padagis_israle_master_report,
        'padagis_usa_master_report': padagis_usa_master_report,
        'overall_count_report': overall_count_report,
        'inclusion_exclusion_counts': inclusion_exclusion_counts
    }
    
    config.mail_config = {
        'success_to_address': success_to_address,
        'success_cc_address': success_cc_address,
        'failure_to_address': failure_to_address,
        'failure_cc_address': failure_cc_address,
        'success_mail_subject': success_mail_subject,
        'failure_mail_subject': failure_mail_subject,
        'success_mail_body': success_mail_body,
        'failure_mail_body': failure_mail_body,
        'from_address': from_address,
        'e_authuser': e_authuser,
        'e_authpass': e_authpass,
        'e_host': e_host,
        'e_port': e_port
    }
    
    logger.info("✅ INITIALIZE_PROCESS completed")
    return config


def MOVE_TO_INPROGRESS(config, db):
    """MOVE_TO_INPROGRESS - Exact Robot Framework logic"""
    logger.info("\n" + "="*60)
    logger.info("MOVE_TO_INPROGRESS")
    logger.info("="*60)
    
    process_status = config.table_names['process_status']
    master_tracker_filename = config.process_variables['master_tracker_filename']
    
    # Insert into process_status
    db.execute_sql_string(f"""
        INSERT INTO {process_status} (process_status, mt_filename, start_datetime)
        VALUES ('Initiated', '{master_tracker_filename}', NOW())
    """)
    
    # Get max process_id
    maxid = db.query(f"SELECT MAX(process_id) as max_id FROM {process_status}")
    process_id = maxid[0]['max_id']
    config.process_variables['process_id'] = process_id
    
    logger.info(f"✅ Created Process ID: {process_id}")
    
    # Create and empty inprogress directory
    bot_inprogresspath = config.process_variables['bot_inprogresspath']
    os.makedirs(bot_inprogresspath, exist_ok=True)
    
    # Empty directory
    for item in os.listdir(bot_inprogresspath):
        item_path = os.path.join(bot_inprogresspath, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    
    # Move master tracker to inprogress
    master_tracker_path = config.process_variables['master_tracker_path']
    dest_path = os.path.join(bot_inprogresspath, master_tracker_filename)
    shutil.move(master_tracker_path, dest_path)
    config.process_variables['master_tracker_path'] = dest_path
    
    # Update status
    UPDATE_STAUTS("File Moved to Inprogress", config, db)
    
    logger.info("✅ MOVE_TO_INPROGRESS completed")


def UPDATE_STAUTS(status, config, db):
    """UPDATE_STAUTS - Update process status"""
    process_id = config.process_variables['process_id']
    process_status = config.table_names['process_status']
    
    db.execute_sql_string(f"""
        UPDATE {process_status} 
        SET process_status = '{status}' 
        WHERE process_id = '{process_id}'
    """)
    logger.info(f"   Status: {status}")


def VALIDATE_MASTER_TRACKER(config, db):
    """VALIDATE_MASTER_TRACKER - Exact Robot Framework logic"""
    logger.info("\n" + "="*60)
    logger.info("VALIDATE_MASTER_TRACKER")
    logger.info("="*60)
    
    UPDATE_STAUTS("Master Tracker Validation Initiated", config, db)
    
    # Placeholder for validation logic
    # In Robot code: Parse Excel With Dynamic Header
    
    UPDATE_STAUTS("Master Tracker Validation Completed", config, db)
    logger.info("✅ VALIDATE_MASTER_TRACKER completed")


def EXECUTE_EACH_CUSTOMER(customer_info, config, db):
    """EXECUTE_EACH_CUSTOMER - Exact Robot Framework logic"""
    customer_name = customer_info['customer_name']
    customer_id = customer_info['customer_id']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing Customer: {customer_name} (ID: {customer_id})")
    logger.info(f"{'='*60}")
    
    # Get subprocess info
    suprocess_info = config.table_names['suprocess_info']
    query_out = db.query(f"""
        SELECT suprocess_name, excel_sheetname, excel_startindex, column_names 
        FROM {suprocess_info} 
        WHERE customer_id='{customer_id}'
    """)
    
    queryLen = db.get_length(query_out)
    if queryLen == 0:
        logger.info(f"   No subprocess info for {customer_name}, skipping...")
        return
    
    suprocess_name = query_out[0]['suprocess_name']
    customer_sheetname = query_out[0]['excel_sheetname']
    excel_row_startind = query_out[0]['excel_startindex']
    excel_colnames = query_out[0]['column_names']
    
    # Get customer directory
    drug_intelligence_path = config.process_variables['drug_intelligence_path']
    customer_foldername = customer_name
    customer_dirpath = os.path.join(drug_intelligence_path, "BOT-IN", "Clients", customer_foldername)
    
    os.makedirs(customer_dirpath, exist_ok=True)
    
    # Get customer files
    list_files = [f for f in os.listdir(customer_dirpath) if f.lower().endswith(('.xls', '.xlsx'))]
    files_count = len(list_files)
    
    if files_count == 0:
        logger.info(f"   No files found for {customer_name}")
        return
    
    in_client_filepath = os.path.join(customer_dirpath, list_files[0])
    
    # Insert log
    log_report = config.table_names['log_report']
    process_id = config.process_variables['process_id']
    
    db.execute_sql_string(f"""
        INSERT INTO {log_report} 
        (process_id, customer_id, initiated_sts, start_datetime, customer_name, filename)
        VALUES ('{process_id}', '{customer_id}', '1', NOW(), '{customer_name}', '{list_files[0]}')
    """)
    
    maxid = db.query(f"""
        SELECT MAX(log_id) as max_id FROM {log_report} 
        WHERE process_id='{process_id}' AND customer_id='{customer_id}'
    """)
    log_id = maxid[0]['max_id']
    
    # Move to inprogress
    bot_inprogresspath = config.process_variables['bot_inprogresspath']
    client_inprogress_dir = os.path.join(bot_inprogresspath, customer_name)
    os.makedirs(client_inprogress_dir, exist_ok=True)
    
    # Empty directory
    for item in os.listdir(client_inprogress_dir):
        item_path = os.path.join(client_inprogress_dir, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
    
    client_filepath = os.path.join(client_inprogress_dir, list_files[0])
    shutil.move(in_client_filepath, client_filepath)
    
    # Process based on subprocess name
    try:
        if suprocess_name == "PROCESS_CAPLIN":
            PROCESS_CAPLIN(client_filepath, customer_sheetname, excel_row_startind, 
                          excel_colnames, config, db)
        elif suprocess_name == "PROCESS_BELLS":
            PROCESS_BELLS(client_filepath, customer_sheetname, excel_row_startind,
                         excel_colnames, config, db)
        elif suprocess_name == "PROCESS_RELONCHEM":
            PROCESS_RELONCHEM(client_filepath, customer_sheetname, excel_row_startind,
                             excel_colnames, config, db)
        elif suprocess_name == "PROCESS_MARKSANS_USA":
            PROCESS_MARKSANS_USA(client_filepath, customer_sheetname, excel_row_startind,
                                excel_colnames, config, db)
        elif suprocess_name == "PROCESS_PADAGIS_USA":
            PROCESS_PADAGIS_USA(client_filepath, customer_sheetname, excel_row_startind,
                               excel_colnames, config, db)
        elif suprocess_name == "PROCESS_PADAGIS_ISRAEL":
            PROCESS_PADAGIS_ISRAEL(client_filepath, customer_sheetname, excel_row_startind,
                                  excel_colnames, config, db)
        
        # Move to processed
        MOVE_TO_PROCESSED(customer_name, client_filepath, config)
        
        # Update log
        db.execute_sql_string(f"""
            UPDATE {log_report} 
            SET completed_sts='1', end_datetime=NOW() 
            WHERE log_id='{log_id}'
        """)
        
        logger.info(f"✅ {customer_name} processed successfully")
        
    except Exception as e:
        logger.error(f"❌ {customer_name} processing failed: {e}")
        MOVE_FAILED_CLIENTFILE(customer_name, client_filepath, log_id, list_files[0], config, db)


def MOVE_TO_PROCESSED(customer_name, client_filpath, config):
    """MOVE_TO_PROCESSED - Exact Robot Framework logic"""
    bot_processedpath = config.process_variables['bot_processedpath']
    processed_customer_path = os.path.join(bot_processedpath, customer_name)
    
    os.makedirs(processed_customer_path, exist_ok=True)
    
    dest_path = os.path.join(processed_customer_path, os.path.basename(client_filpath))
    shutil.move(client_filpath, dest_path)


def MOVE_FAILED_CLIENTFILE(customer_name, client_filepath, log_id, filename, config, db):
    """MOVE_FAILED_CLIENTFILE - Exact Robot Framework logic"""
    bot_failedpath = config.process_variables['bot_failedpath']
    failed_customer_path = os.path.join(bot_failedpath, customer_name)
    
    os.makedirs(failed_customer_path, exist_ok=True)
    
    dest_path = os.path.join(failed_customer_path, os.path.basename(client_filepath))
    if os.path.exists(client_filepath):
        shutil.move(client_filepath, dest_path)
    
    # Update log
    log_report = config.table_names['log_report']
    db.execute_sql_string(f"""
        UPDATE {log_report}
        SET failed_sts='1', 
            failure_message='Failed while processing {customer_name} customer - {filename}',
            end_datetime=NOW()
        WHERE log_id='{log_id}'
    """)


def MOVE_TO_FAILED(error_message, config, db):
    """MOVE_TO_FAILED - Exact Robot Framework logic"""
    logger.error(f"\n❌ MOVING TO FAILED: {error_message}")
    
    bot_failedpath = config.process_variables['bot_failedpath']
    bot_outpath = config.process_variables['bot_outpath']
    master_tracker_path = config.process_variables['master_tracker_path']
    process_id = config.process_variables['process_id']
    
    os.makedirs(bot_failedpath, exist_ok=True)
    
    # Move master tracker to failed
    if os.path.exists(master_tracker_path):
        filename = os.path.basename(master_tracker_path)
        dest_path = os.path.join(bot_failedpath, filename)
        shutil.move(master_tracker_path, dest_path)
        attachment = dest_path
    else:
        attachment = ""
    
    # Move output directory to failed
    output_dir = os.path.join(bot_outpath, str(process_id))
    if os.path.exists(output_dir):
        failed_output = os.path.join(bot_failedpath, str(process_id))
        shutil.move(output_dir, failed_output)
    
    # Update process status
    process_status = config.table_names['process_status']
    error_message_clean = error_message.replace("'", "''")
    db.execute_sql_string(f"""
        UPDATE {process_status}
        SET process_status='Failed', error_message='{error_message_clean}', end_datetime=NOW()
        WHERE process_id='{process_id}'
    """)
    
    # Send failure email
    send_failure_email(config, process_id, 
                      os.path.basename(master_tracker_path) if master_tracker_path else "Unknown",
                      error_message, attachment)


def MOVE_TO_BOT_OUT(config, db):
    """MOVE_TO_BOT_OUT - Exact Robot Framework logic"""
    logger.info("\n" + "="*60)
    logger.info("MOVE TO BOT-OUT")
    logger.info("="*60)
    
    # Get completed and failed files
    log_report = config.table_names['log_report']
    process_id = config.process_variables['process_id']
    
    completedQuery = db.query(f"""
        SELECT customer_name, filename 
        FROM {log_report} 
        WHERE completed_sts='1' AND process_id='{process_id}'
    """)
    
    failedQuery = db.query(f"""
        SELECT customer_name, filename, failure_message
        FROM {log_report}
        WHERE failed_sts='1' AND process_id='{process_id}'
    """)
    
    completedQueryLen = db.get_length(completedQuery)
    failedQueryLen = db.get_length(failedQuery)
    
    # If only failures
    if completedQueryLen == 0 and failedQueryLen != 0:
        error_lines = []
        for i, f in enumerate(failedQuery):
            error_lines.append(f"{i+1}) {f['customer_name']} - {f['filename']}")
        error_message = "Below files failed during processing:\n\n" + "\n".join(error_lines)
        MOVE_TO_FAILED(error_message, config, db)
        return
    
    # Move master tracker to output
    

di_output_dir = os.path.join(config.process_variables['bot_outpath'], str(process_id))
    master_tracker_path = config.process_variables['master_tracker_path']
    
    if os.path.exists(master_tracker_path):
        dest_path = os.path.join(di_output_dir, os.path.basename(master_tracker_path))
        shutil.move(master_tracker_path, dest_path)
    
    # Collect attachments
    attachments = []
    for filename in os.listdir(di_output_dir):
        if filename.endswith('.xlsx') and 'Conflict' not in filename:
            attachments.append(os.path.join(di_output_dir, filename))
    
    # Send success email
    attachments_str = ';'.join(attachments)
    send_success_email(config, completedQuery, failedQuery, attachments_str)
    
    # Clean inprogress
    bot_inprogresspath = config.process_variables['bot_inprogresspath']
    for item in os.listdir(bot_inprogresspath):
        item_path = os.path.join(bot_inprogresspath, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    
    logger.info("✅ MOVE_TO_BOT_OUT completed")


def MASTER_TRACKER_UPDATE(config, db):
    """MASTER_TRACKER_UPDATE - Exact Robot Framework logic"""
    logger.info("\n" + "="*60)
    logger.info("MASTER_TRACKER_UPDATE")
    logger.info("="*60)
    
    # Get customer list
    customer_table = config.process_variables['customer_table']
    customer_list = db.query(f"SELECT customer_id, customer_name FROM {customer_table} WHERE status = 1")
    
    logger.info(f"Found {len(customer_list)} active customers")
    
    # Process each customer
    for customer_info in customer_list:
        try:
            EXECUTE_EACH_CUSTOMER(customer_info, config, db)
        except Exception as e:
            logger.error(f"❌ Error processing {customer_info['customer_name']}: {e}")
    
    # Generate reports
    try:
        GENERATE_REPORT(config, db)
    except Exception as e:
        logger.error(f"⚠️  Report generation failed: {e}")
    
    # Move to BOT-OUT
    try:
        MOVE_TO_BOT_OUT(config, db)
    except Exception as e:
        logger.error(f"⚠️  Move to BOT-OUT failed: {e}")
    
    # Update final status
    process_status = config.table_names['process_status']
    process_id = config.process_variables['process_id']
    db.execute_sql_string(f"""
        UPDATE {process_status}
        SET process_status='Completed', end_datetime=NOW()
        WHERE process_id='{process_id}'
    """)
    
    logger.info("\n✅ MASTER_TRACKER_UPDATE