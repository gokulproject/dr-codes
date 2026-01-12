"""
Main entry point for Drug Intelligence Automation
"""
import os
import sys
import shutil
from typing import Dict, Any

from config import Config
from database import DatabaseHandler
from excel import ExcelHandler
from drug_intelligence import DrugIntelligence
from processors import (
    CaplinProcessor, BellsProcessor, RelonchemProcessor,
    MarksansUSAProcessor, PadagisUSAProcessor, PadagisIsraelProcessor
)
from logger import get_logger
from scraper import WebScraper, DrugDatabaseScraper


def execute_customer_processing(di: DrugIntelligence, customer_info: Dict[str, Any]):
    """Execute processing for each customer"""
    logger = get_logger()
    
    try:
        customer_name = customer_info['customer_name']
        customer_id = customer_info['customer_id']
        
        logger.info(f"Processing customer: {customer_name} (ID: {customer_id})")
        
        # Get subprocess info
        subprocess_info = di.db.get_subprocess_info(
            di.config.get_table_name('suprocess_info'),
            customer_id
        )
        
        if not subprocess_info:
            logger.warning(f"No subprocess info for customer {customer_name}")
            return
        
        subprocess_name = subprocess_info['suprocess_name']
        customer_sheetname = subprocess_info['excel_sheetname']
        excel_start_index = subprocess_info['excel_startindex']
        excel_colnames = subprocess_info['column_names']
        
        # Find customer file
        customer_dirpath = os.path.join(
            di.config.get_path('client_dirpath'),
            customer_name
        )
        
        if not os.path.exists(customer_dirpath):
            os.makedirs(customer_dirpath, exist_ok=True)
        
        # Get Excel files
        list_files = [f for f in os.listdir(customer_dirpath) 
                     if f.lower().endswith(('.xls', '.xlsx'))]
        
        if not list_files:
            logger.warning(f"No files found for customer: {customer_name}")
            return
        
        in_client_filepath = os.path.join(customer_dirpath, list_files[0])
        
        # Log process start
        log_id = di.db.insert_process_log(
            di.config.get_table_name('log_report'),
            di.process_id,
            customer_id,
            customer_name,
            list_files[0]
        )
        
        # Move to in-progress
        client_inprogress_dir = os.path.join(
            di.config.get_path('bot_inprogresspath'),
            customer_name
        )
        os.makedirs(client_inprogress_dir, exist_ok=True)
        
        # Clear in-progress directory
        for item in os.listdir(client_inprogress_dir):
            item_path = os.path.join(client_inprogress_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
        
        client_filepath = os.path.join(client_inprogress_dir, list_files[0])
        shutil.move(in_client_filepath, client_filepath)
        
        logger.log_file_operation("MOVE", client_filepath, "to in-progress")
        
        # Process based on subprocess name
        process_status = True
        try:
            processor_map = {
                'PROCESS_CAPLIN': CaplinProcessor,
                'PROCESS_BELLS': BellsProcessor,
                'PROCESS_RELONCHEM': RelonchemProcessor,
                'PROCESS_MARKSANS_USA': MarksansUSAProcessor,
                'PROCESS_PADAGIS_USA': PadagisUSAProcessor,
                'PROCESS_PADAGIS_ISRAEL': PadagisIsraelProcessor
            }
            
            if subprocess_name in processor_map:
                processor = processor_map[subprocess_name](
                    di.db, di.excel_handler, di.config, di.process_id  # Changed from di.excel to di.excel_handler
                )
                processor.process(
                    client_filepath,
                    subprocess_info,
                    di.excluded_saltnames
                )
            else:
                logger.error(f"Unknown subprocess: {subprocess_name}")
                process_status = False
                
        except Exception as e:
            logger.error(f"Processing failed for {customer_name}: {str(e)}", exc_info=True)
            process_status = False
        
        # Handle success or failure
        if not process_status:
            move_to_failed(di, customer_name, client_filepath, log_id)
        else:
            move_to_processed(di, customer_name, client_filepath)
            
            # Update log as completed
            query = f"""
                UPDATE {di.config.get_table_name('log_report')}
                SET completed_sts = '1', end_datetime = NOW()
                WHERE log_id = %s
            """
            di.db.execute_update(query, (log_id,))
        
    except Exception as e:
        logger.error(f"Error executing customer processing: {str(e)}", exc_info=True)
        raise


def move_to_processed(di: DrugIntelligence, customer_name: str, client_filepath: str):
    """Move file to processed folder"""
    logger = get_logger()
    
    try:
        processed_dir = os.path.join(
            di.config.get_path('bot_processedpath'),
            customer_name
        )
        os.makedirs(processed_dir, exist_ok=True)
        
        dest_path = os.path.join(processed_dir, os.path.basename(client_filepath))
        shutil.move(client_filepath, dest_path)
        
        logger.log_file_operation("MOVE", dest_path, "to processed")
        
    except Exception as e:
        logger.error(f"Error moving to processed: {str(e)}", exc_info=True)


def move_to_failed(di: DrugIntelligence, customer_name: str, 
                  client_filepath: str, log_id: int):
    """Move file to failed folder"""
    logger = get_logger()
    
    try:
        failed_dir = os.path.join(
            di.config.get_path('bot_failedpath'),
            customer_name
        )
        os.makedirs(failed_dir, exist_ok=True)
        
        dest_path = os.path.join(failed_dir, os.path.basename(client_filepath))
        shutil.move(client_filepath, dest_path)
        
        logger.log_file_operation("MOVE", dest_path, "to failed")
        
        # Update log
        filename = os.path.basename(client_filepath)
        query = f"""
            UPDATE {di.config.get_table_name('log_report')}
            SET failed_sts = '1', 
                failure_message = 'Failed while processing {customer_name} customer - {filename}',
                end_datetime = NOW()
            WHERE log_id = %s
        """
        di.db.execute_update(query, (log_id,))
        
    except Exception as e:
        logger.error(f"Error moving to failed: {str(e)}", exc_info=True)


def master_tracker_update(di: DrugIntelligence):
    """Main master tracker update process"""
    logger = get_logger()
    
    try:
        # Get all active customers
        customers = di.db.get_customers(di.config.get_table_name('customer_table'))
        
        logger.info(f"Found {len(customers)} active customers")
        
        # Process each customer
        for customer in customers:
            execute_customer_processing(di, customer)
        
        # Generate reports
        logger.info("Generating reports...")
        di.generate_reports()
        
        # Move to BOT-OUT
        logger.info("Moving to BOT-OUT...")
        di.move_to_bot_out()
        
        # Update final status
        di.db.update_process_status(
            di.config.get_table_name('process_status'),
            di.process_id,
            'Completed'
        )
        
    except Exception as e:
        logger.error(f"Master tracker update failed: {str(e)}", exc_info=True)
        raise


def main():
    """Main execution function"""
    logger = get_logger()
    di = None
    
    try:
        logger.log_process_start("Drug Intelligence Automation - Main Process")
        
        # Initialize Drug Intelligence
        di = DrugIntelligence(server_type="DEV")
        
        # Initialize process
        if not di.initialize_process():
            logger.info("No files to process. Exiting.")
            return
        
        # Move master tracker to in-progress
        di.move_to_inprogress()
        
        # Validate master tracker
        if not di.validate_master_tracker():
            logger.error("Master Tracker validation failed")
            return
        
        # Read master tracker data
        di.read_master_tracker()
        
        # Execute master tracker update
        master_tracker_update(di)
        
        logger.log_process_end("Drug Intelligence Automation - Main Process", "SUCCESS")
        
    except Exception as e:
        logger.error(f"Main process failed: {str(e)}", exc_info=True)
        if di:
            # Move to failed
            error_msg = str(e)
            # Send failure email and update status
            di.db.update_process_status(
                di.config.get_table_name('process_status'),
                di.process_id,
                'Failed',
                error_msg
            )
        logger.log_process_end("Drug Intelligence Automation - Main Process", "FAILED")
        sys.exit(1)
        
    finally:
        if di:
            di.cleanup()


if __name__ == "__main__":
    main()
