"""
Main Entry Point - Drug Intelligence Automation
Orchestrates the complete end-to-end workflow
Execute: python main.py
"""

import sys
import os
from datetime import datetime
import time

# Import all modules
from config import config
from database import DatabaseManager
from logger import create_logger
from email_sender import EmailSender
from excel_manager import ExcelManager
from processors import DrugDataProcessor
from drug_intelligence import DrugIntelligenceWorkflow


def print_banner(logger):
    """Print application banner"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          DRUG INTELLIGENCE AUTOMATION SYSTEM                   ║
║                                                                ║
║          Converting RPA to Production Python                   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    if logger:
        logger.info(banner)


def print_summary(logger, summary_data: dict):
    """Print execution summary"""
    print("\n" + "="*70)
    print("EXECUTION SUMMARY".center(70))
    print("="*70)
    
    for key, value in summary_data.items():
        print(f"{key:.<50} {value}")
    
    print("="*70 + "\n")
    
    if logger:
        logger.log_summary(summary_data)


def main():
    """
    Main execution function
    """
    logger = None
    db_manager = None
    start_time = time.time()
    
    try:
        # =====================================================================
        # STEP 1: INITIALIZE LOGGER
        # =====================================================================
        print("\n⏳ Initializing logger...")
        
        logger = create_logger(log_dir="./logs")
        print_banner(logger)
        
        logger.success("✅ Logger initialized successfully")
        
        # =====================================================================
        # STEP 2: INITIALIZE DATABASE CONNECTION
        # =====================================================================
        logger.log_process_step("Database Connection", "STARTED")
        
        db_manager = DatabaseManager(config.DB_CONFIG, logger)
        
        if not db_manager.connect():
            raise Exception("Failed to connect to database")
        
        logger.log_process_step("Database Connection", "COMPLETED")
        
        # =====================================================================
        # STEP 3: LOAD CONFIGURATIONS FROM DATABASE
        # =====================================================================
        logger.log_process_step("Configuration Loading", "STARTED")
        
        if not config.initialize_all_configs(db_manager):
            raise Exception("Failed to load configurations from database")
        
        logger.info(f"✅ Loaded {len(config.table_names)} table configurations")
        logger.info(f"✅ Loaded {len(config.paths)} path configurations")
        logger.info(f"✅ Loaded {len(config.excluded_saltnames)} excluded salt names")
        
        logger.log_process_step("Configuration Loading", "COMPLETED")
        
        # =====================================================================
        # STEP 4: INITIALIZE EMAIL SENDER
        # =====================================================================
        logger.log_process_step("Email Sender Initialization", "STARTED")
        
        email_sender = EmailSender(config.EMAIL_CONFIG, logger)
        
        # Test SMTP connection (optional)
        # email_sender.test_connection()
        
        logger.log_process_step("Email Sender Initialization", "COMPLETED")
        
        # =====================================================================
        # STEP 5: INITIALIZE EXCEL MANAGER
        # =====================================================================
        logger.log_process_step("Excel Manager Initialization", "STARTED")
        
        excel_manager = ExcelManager(
            excel_handler_path="./ExcelHandler",
            logger=logger
        )
        
        logger.log_process_step("Excel Manager Initialization", "COMPLETED")
        
        # =====================================================================
        # STEP 6: INITIALIZE DATA PROCESSOR
        # =====================================================================
        logger.log_process_step("Data Processor Initialization", "STARTED")
        
        processor = DrugDataProcessor(
            data_processing_path="./DataProcessing",
            config=config,
            db_manager=db_manager,
            excel_manager=excel_manager,
            logger=logger
        )
        
        logger.log_process_step("Data Processor Initialization", "COMPLETED")
        
        # =====================================================================
        # STEP 7: INITIALIZE WORKFLOW ORCHESTRATOR
        # =====================================================================
        logger.log_process_step("Workflow Initialization", "STARTED")
        
        workflow = DrugIntelligenceWorkflow(
            config=config,
            db_manager=db_manager,
            excel_manager=excel_manager,
            processor=processor,
            email_sender=email_sender,
            logger=logger
        )
        
        logger.log_process_step("Workflow Initialization", "COMPLETED")
        
        # =====================================================================
        # STEP 8: INITIALIZE PROCESS
        # =====================================================================
        if not workflow.initialize_process():
            raise Exception("Process initialization failed")
        
        # =====================================================================
        # STEP 9: MASTER TRACKER UPDATE (PROCESS ALL CUSTOMERS)
        # =====================================================================
        if not workflow.master_tracker_update():
            logger.warning("⚠️ Master tracker update completed with warnings")
        
        # =====================================================================
        # STEP 10: GENERATE REPORTS
        # =====================================================================
        if not workflow.generate_report():
            raise Exception("Report generation failed")
        
        # =====================================================================
        # STEP 11: MOVE TO OUTPUT AND SEND NOTIFICATIONS
        # =====================================================================
        if not workflow.move_to_bot_out():
            raise Exception("Failed to move output files")
        
        # =====================================================================
        # STEP 12: MARK PROCESS AS COMPLETED
        # =====================================================================
        workflow.complete_process()
        
        # =====================================================================
        # STEP 13: PRINT SUMMARY
        # =====================================================================
        end_time = time.time()
        execution_time = end_time - start_time
        
        summary_data = {
            "Process ID": config.process_id,
            "Master Tracker File": config.master_tracker_filename,
            "Total Customers": workflow.total_customers,
            "Successfully Processed": workflow.processed_customers,
            "Failed": workflow.failed_customers,
            "Execution Time": f"{execution_time:.2f} seconds",
            "Status": "✅ COMPLETED SUCCESSFULLY"
        }
        
        print_summary(logger, summary_data)
        
        logger.success("="*70)
        logger.success("DRUG INTELLIGENCE AUTOMATION COMPLETED SUCCESSFULLY")
        logger.success("="*70)
        
        return 0
        
    except KeyboardInterrupt:
        if logger:
            logger.warning("⚠️ Process interrupted by user")
        print("\n⚠️ Process interrupted by user")
        return 1
        
    except Exception as e:
        error_msg = f"CRITICAL ERROR: {str(e)}"
        
        if logger:
            logger.critical("="*70)
            logger.critical("PROCESS FAILED")
            logger.critical("="*70)
            logger.error(f"❌ {error_msg}")
            logger.log_exception("main", e)
        
        print(f"\n❌ {error_msg}")
        
        # Calculate execution time
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Print failure summary
        summary_data = {
            "Status": "❌ FAILED",
            "Error": str(e),
            "Execution Time": f"{execution_time:.2f} seconds"
        }
        
        if config.process_id:
            summary_data["Process ID"] = config.process_id
        
        print_summary(logger, summary_data)
        
        return 1
        
    finally:
        # =====================================================================
        # CLEANUP: CLOSE DATABASE CONNECTION
        # =====================================================================
        if db_manager:
            try:
                db_manager.disconnect()
                if logger:
                    logger.info("✅ Database connection closed")
            except Exception as e:
                if logger:
                    logger.warning(f"⚠️ Error closing database: {str(e)}")
        
        # Close logger
        if logger:
            logger.close()
        
        print("\n" + "="*70)
        print("Thank you for using Drug Intelligence Automation System")
        print("="*70 + "\n")


if __name__ == "__main__":
    """
    Entry point for command-line execution
    Usage: python main.py
    """
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
