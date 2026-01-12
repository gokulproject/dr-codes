# main.py
from drug_intelligence import initialize_process, master_tracker_update
from Logger import LOGGER

if __name__ == "__main__":
    LOGGER.info("Starting main process.")
    initialize_process()
    if process_id:
        master_tracker_update()
    LOGGER.info("Main process completed.")