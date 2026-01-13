"""
Customer Processors - All PROCESS_* functions from Robot Framework
Exact line-by-line conversion
"""
from ExcelHandler import ExcelHandler
from DataProcessing import DataProcessing


# Global instances
excel_handler = ExcelHandler()
data_processor = DataProcessing()


def PROCESS_CAPLIN(client_filepath, customer_sheetname, excel_row_startind, 
                   excel_colnames, config, db):
    """PROCESS_CAPLIN - Exact Robot Framework logic"""
    print(f"   Processing CAPLIN...")
    
    colnames = excel_colnames.split(';')
    caplin_master_report = config.table_names['caplin_master_report']
    process_id = config.process_variables['process_id']
    excluded_saltnames = config.process_variables['excluded_saltnames']
    remark_default_value = config.process_variables['remark_default_value']
    
    # Truncate table
    db.execute_sql_string(f"TRUNCATE TABLE {caplin_master_report}")
    
    # Read Excel - Using your ExcelHandler class
    sheet_values = excel_handler.read_excel_with_clean_columns(
        client_filepath, customer_sheetname, colnames, int(excel_row_startind)
    )
    
    rowno = int(excel_row_startind)
    
    for list_values in sheet_values:
        # GET_EXCLUDED_SALT_2 - Using your DataProcessing class
        f_pdtname = data_processor.get_excluded_salt_2(list_values[4], excluded_saltnames)
        
        # Determine include/exclude status
        if list_values[-1] == '':
            in_ex_sts = 'include'
        else:
            in_ex_sts = 'exclude'
        
        # Strip whitespace
        list_values = [s.strip() if isinstance(s, str) else s for s in list_values]
        
        # Set remark
        if in_ex_sts == 'include':
            remark = remark_default_value
        else:
            remark = 'Withdrawn date is present'
        
        # Insert into database
        db.execute_sql_string(f"""
            INSERT INTO {caplin_master_report} 
            (process_id, rowno, productname, strength, unit, active_ingrediants, 
             filtered_name, withdrawn_date, include_exclude_status, added_datetime, remark)
            VALUES ('{process_id}', '{list_values[0]}', '{list_values[1]}', '{list_values[2]}', 
                    '{list_values[3]}', '{list_values[4]}', '{f_pdtname}', '{list_values[5]}', 
                    '{in_ex_sts}', NOW(), '{remark}')
        """)
    
    # PROCESS_DRUG_NAMES - Using your DataProcessing class
    data_processor.process_drug_names(caplin_master_report, process_id, db)
    
    print(f"   ✅ CAPLIN processed: {len(sheet_values)} records")


def PROCESS_BELLS(client_filepath, customer_sheetname, excel_row_startind,
                  excel_colnames, config, db):
    """PROCESS_BELLS - Exact Robot Framework logic"""
    print(f"   Processing BELLS...")
    
    colnames = excel_colnames.split(';')
    bells_master_report = config.table_names['bells_master_report']
    process_id = config.process_variables['process_id']
    excluded_saltnames = config.process_variables['excluded_saltnames']
    remark_default_value = config.process_variables['remark_default_value']
    
    # Truncate table
    db.execute_sql_string(f"TRUNCATE TABLE {bells_master_report}")
    
    # Color map
    color_map = {
        (204, 255, 255): "Marketed",
        (150, 150, 150): "Licence cancelled by MAH",
        (255, 204, 153): "Not Marketed"
    }
    
    # Parse colored cells - Using your ExcelHandler class
    excel_row_startind_adjusted = int(excel_row_startind) - 1
    excel_values = excel_handler.xls_parse_colored_cells(
        client_filepath, customer_sheetname, colnames, excel_row_startind_adjusted, color_map
    )
    
    for values in excel_values:
        # GET_EXCLUDED_SALT_2
        filtered_name = data_processor.get_excluded_salt_2(values[1], excluded_saltnames)
        
        # Determine remark and status
        if values[3] == "Licence cancelled by MAH":
            remark = "Licence cancelled by MAH"
            inex_sts = 'exclude'
        else:
            remark = remark_default_value
            inex_sts = 'include'
        
        # Insert into database
        db.execute_sql_string(f"""
            INSERT INTO {bells_master_report}
            (process_id, rowno, active_ingrediants, color_status, 
             include_exclude_status, remark, added_datetime, filtered_name)
            VALUES ('{process_id}', '{values[0]}', '{values[1]}', '{values[3]}',
                    '{inex_sts}', '{remark}', NOW(), '{filtered_name}')
        """)
    
    # PROCESS_DRUG_NAMES
    data_processor.process_drug_names(bells_master_report, process_id, db)
    
    print(f"   ✅ BELLS processed: {len(excel_values)} records")


def PROCESS_RELONCHEM(client_filepath, customer_sheetname, excel_row_startind,
                      excel_colnames, config, db):
    """PROCESS_RELONCHEM - Exact Robot Framework logic"""
    print(f"   Processing RELONCHEM...")
    
    colnames = excel_colnames.split(';')
    relonchem_master_report = config.table_names['relonchem_master_report']
    process_id = config.process_variables['process_id']
    excluded_saltnames = config.process_variables['excluded_saltnames']
    remark_default_value = config.process_variables['remark_default_value']
    
    # Truncate table
    db.execute_sql_string(f"TRUNCATE TABLE {relonchem_master_report}")
    
    # Color map
    color_map = {
        "9": "Marketed",
        "0": "Licence cancelled by the MAH",
        "7": "Licence Application Pending",
        "5": "Not Marketed",
        "8": "Invented name deleted",
        "FFFFFF00": "Newly Added"
    }
    
    # Parse colored cells - Using your ExcelHandler class
    excel_values = excel_handler.xlsx_parse_colored_cells(
        client_filepath, customer_sheetname, colnames, int(excel_row_startind), color_map
    )
    
    for values in excel_values:
        # GET_EXCLUDED_SALT_2
        filtered_name = data_processor.get_excluded_salt_2(values[1], excluded_saltnames)
        
        # Determine remark and status
        if values[3] in ["Marketed", "Not Marketed", "Newly Added", "Invented name deleted"]:
            remark = remark_default_value
            inex_sts = 'include'
        else:
            remark = values[3]
            inex_sts = 'exclude'
        
        # Insert into database
        db.execute_sql_string(f"""
            INSERT INTO {relonchem_master_report}
            (process_id, rowno, active_ingrediants, color_status,
             include_exclude_status, remark, added_datetime, filtered_name)
            VALUES ('{process_id}', '{values[0]}', '{values[1]}', '{values[3]}',
                    '{inex_sts}', '{remark}', NOW(), '{filtered_name}')
        """)
    
    # PROCESS_DRUG_NAMES
    data_processor.process_drug_names(relonchem_master_report, process_id, db)
    
    print(f"   ✅ RELONCHEM processed: {len(excel_values)} records")


def PROCESS_MARKSANS_USA(client_filepath, customer_sheetname, excel_row_startind,
                         excel_colnames, config, db):
    """PROCESS_MARKSANS_USA - Exact Robot Framework logic"""
    print(f"   Processing MARKSANS USA...")
    
    startindex = int(excel_row_startind) - 1
    colnames = excel_colnames.split(';')
    marksans_usa_master_report = config.table_names['marksans_usa_master_report']
    process_id = config.process_variables['process_id']
    excluded_saltnames = config.process_variables['excluded_saltnames']
    remark_default_value = config.process_variables['remark_default_value']
    
    # Truncate table
    db.execute_sql_string(f"TRUNCATE TABLE {marksans_usa_master_report}")
    
    # Read Excel - Using your ExcelHandler class
    rowvalues = excel_handler.read_excel_with_clean_columns(
        client_filepath, customer_sheetname, colnames, startindex
    )
    
    for values in rowvalues:
        # Determine remark and status
        approval_status_clean = str(values[2]).strip().lower()
        withdrawn_date_clean = str(values[3]).strip()
        
        if approval_status_clean not in ["approved", ""]:
            remark = "Approval Status is not Approved"
            inex_sts = 'exclude'
        elif withdrawn_date_clean:
            remark = "Withdrawn Date is not empty"
            inex_sts = 'exclude'
        else:
            remark = remark_default_value
            inex_sts = 'include'
        
        # GET_EXCLUDED_SALT_2
        filtered_name = data_processor.get_excluded_salt_2(values[1], excluded_saltnames)
        
        # Clean drug name
        drugname = str(values[1]).replace('\n', '')
        
        # Insert into database
        db.execute_sql_string(f"""
            INSERT INTO {marksans_usa_master_report}
            (process_id, rowno, active_ingrediants, filtered_name, approval_status,
             withdrawn_date, include_exclude_status, remark, added_datetime)
            VALUES ('{process_id}', '{values[0]}', '{drugname}', '{filtered_name}',
                    '{values[2]}', '{values[3]}', '{inex_sts}', '{remark}', NOW())
        """)
    
    # PROCESS_DRUG_NAMES
    data_processor.process_drug_names(marksans_usa_master_report, process_id, db)
    
    print(f"   ✅ MARKSANS USA processed: {len(rowvalues)} records")


def PROCESS_PADAGIS_USA(client_filepath, customer_sheetname, excel_row_startind,
                        excel_colnames, config, db):
    """PROCESS_PADAGIS_USA - Exact Robot Framework logic"""
    print(f"   Processing PADAGIS USA...")
    
    color_map = {'FFFF5050': 'Red'}
    sheetnames = customer_sheetname.split(';')
    colnames = excel_colnames.split(';')
    startindex = int(excel_row_startind)
    padagis_usa_master_report = config.table_names['padagis_usa_master_report']
    process_id = config.process_variables['process_id']
    excluded_saltnames = config.process_variables['excluded_saltnames']
    remark_default_value = config.process_variables['remark_default_value']
    
    # Truncate table
    db.execute_sql_string(f"TRUNCATE TABLE {padagis_usa_master_report}")
    
    # Parse colored multicells - Using your ExcelHandler class
    rowvalues = excel_handler.xlsx_parse_colored_multicells(
        client_filepath, sheetnames, colnames, startindex, color_map
    )
    
    for values in rowvalues:
        # Clean comment
        comment = str(values[8]).replace('\n', ' ')
        comment = comment.replace("'", "''")
        
        # GET_EXCLUDED_SALT_2
        filtered_name = data_processor.get_excluded_salt_2(values[5], excluded_saltnames)
        
        # Determine remark and status
        if values[1] == "Contract Manufactured Products":
            remark = "Not MAH product"
            inex_sts = 'exclude'
        elif values[7] == "Red":
            remark = "Product Highlighted in Red"
            inex_sts = 'exclude'
        elif "discontinued" in comment.lower().strip():
            remark = comment
            inex_sts = 'exclude'
        else:
            remark = remark_default_value
            inex_sts = 'include'
        
        # Clean product name
        productname = str(values[5]).replace("'", "''")
        
        # Insert into database
        db.execute_sql_string(f"""
            INSERT INTO {padagis_usa_master_report}
            (process_id, rowno, sheetname, ndc_no, active_ingrediants, comment,
             filtered_name, color_status, include_exclude_status, remark, added_datetime)
            VALUES ('{process_id}', '{values[0]}', '{values[1]}', '{values[2]}',
                    '{productname}', '{comment}', '{filtered_name}', '{values[7]}',
                    '{inex_sts}', '{remark}', NOW())
        """)
    
    # PROCESS_DRUG_NAMES
    data_processor.process_drug_names(padagis_usa_master_report, process_id, db)
    
    print(f"   ✅ PADAGIS USA processed: {len(rowvalues)} records")


def PROCESS_PADAGIS_ISRAEL(client_filepath, customer_sheetname, excel_row_startind,
                           excel_colnames, config, db):
    """PROCESS_PADAGIS_ISRAEL - Exact Robot Framework logic"""
    print(f"   Processing PADAGIS ISRAEL...")
    
    colnames = excel_colnames.split(';')
    padagis_israle_master_report = config.table_names['padagis_israle_master_report']
    process_id = config.process_variables['process_id']
    excluded_saltnames = config.process_variables['excluded_saltnames']
    remark_default_value = config.process_variables['remark_default_value']
    
    # Truncate table
    db.execute_sql_string(f"TRUNCATE TABLE {padagis_israle_master_report}")
    
    # Read Excel - Using your ExcelHandler class
    rowvalues = excel_handler.read_excel_with_clean_columns(
        client_filepath, customer_sheetname, colnames, int(excel_row_startind)
    )
    
    for values in rowvalues:
        # GET_EXCLUDED_SALT_2
        filtered_name = data_processor.get_excluded_salt_2(values[1], excluded_saltnames)
        
        # All records are included
        remark = remark_default_value
        inex_sts = 'include'
        
        # Insert into database
        db.execute_sql_string(f"""
            INSERT INTO {padagis_israle_master_report}
            (process_id, rowno, active_ingrediants, filtered_name,
             include_exclude_status, remark, added_datetime)
            VALUES ('{process_id}', '{values[0]}', '{values[1]}', '{filtered_name}',
                    '{inex_sts}', '{remark}', NOW())
        """)
    
    # PROCESS_DRUG_NAMES
    data_processor.process_drug_names(padagis_israle_master_report, process_id, db)
    
    print(f"   ✅ PADAGIS ISRAEL processed: {len(rowvalues)} records")