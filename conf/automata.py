import os
import re
import shutil
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Bank module >>
import actual_importer
import bankinter 
import sabadell
import caixa
import santander
import traderepublic
import sumup

IN_FOLDER = "/input"
OUT_FOLDER = "/output"
IMPORTED_FOLDER = "/imported"
RETENTION_HOUR = int(os.environ.get("RETENTION_HOUR", 12))

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

ERROR_RED = "\033[1;31m"
RESET_COLOR = "\033[0m"

def clean_old_csv(folder):
    now = time.time()
    limit_seconds = RETENTION_HOUR * 3600
    
    logger.info(
        f"🧹 Cleaning {folder}: removing CSV files older than {RETENTION_HOUR} hours"
    )
    
    try:
        for file_name in os.listdir(folder):
            full_path_file = os.path.join(folder, file_name)
            
            if os.path.isfile(full_path_file) and file_name.endswith('.csv'):
                modification_date = os.path.getmtime(full_path_file)
                if (now - modification_date) > limit_seconds:
                    os.remove(full_path_file)
                    logger.info(f"🗑️ Deleted {file_name} file")
    except OSError as error:
        logger.error("%s⚠️ Error while deleting old CSV files in %s: %s%s",
                     ERROR_RED, folder, error, RESET_COLOR)


def move_to_imported(csv_path):
    file_name = os.path.basename(csv_path)
    base_name, extension = os.path.splitext(file_name)
    destination = os.path.join(IMPORTED_FOLDER, file_name)
    suffix = 1
    while os.path.exists(destination):
        destination = os.path.join(
            IMPORTED_FOLDER, f"{base_name}_{suffix}{extension}"
        )
        suffix += 1

    shutil.move(csv_path, destination)
    logger.info("📥 Moved imported CSV to: %s", destination)

class FilesMonitor(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or os.path.basename(event.src_path).startswith("~$"):
            return

        clean_old_csv(OUT_FOLDER)
        clean_old_csv(IMPORTED_FOLDER)
            
        file_name = os.path.basename(event.src_path)
        file_name_lower = file_name.lower()
        bankinter_csv_path = None

        if file_name_lower.endswith(('.xlsx', '.xls', '.txt', '.csv', '.pdf')):
            logger.info(f"⚡ Find: {file_name}")
            time.sleep(2) # Wait for complete copy
            
            try:
                # 1. SUMUP
                if file_name_lower.startswith("sumup") and file_name_lower.endswith(".pdf"):
                    logger.info("-> Using [SumUp] module")
                    sumup.process(event.src_path, OUT_FOLDER, file_name)

                # 2. TRADE REPUBLIC
                elif file_name_lower == "exportación de transacción.csv":
                    logger.info("-> Using [Trade Republic] module")
                    traderepublic.process(event.src_path, OUT_FOLDER, file_name)

                # 3. SANTANDER (Files starts with transactions)
                elif file_name_lower.startswith("transactions"):
                    logger.info("-> Using [Santander] module")
                    santander.process(event.src_path,OUT_FOLDER,file_name)

                # 4. LA CAIXA
                elif file_name_lower.startswith("movimientos_cuenta"):
                    logger.info("-> Using [Caixa] module")
                    caixa.process(event.src_path,OUT_FOLDER,file_name)

                # 5. BANKINTER
                elif file_name_lower.startswith("movimientos"):
                    logger.info("-> Using [Bankinter] module")
                    bankinter.process(event.src_path,OUT_FOLDER,file_name)
                    base_name = os.path.splitext(file_name)[0]
                    prefix = os.environ.get("PREFIX_BANKINTER", "BK")
                    bankinter_csv_path = os.path.join(
                        OUT_FOLDER, f"{prefix}_{base_name}.csv"
                    )

                # 6. CASO SABADELL
                elif file_name_lower.endswith('.txt') or re.match(r'^[\d_]+\.[a-zA-Z0-9]+$', file_name_lower):
                    logger.info("-> Using [Sabadell] module")
                    sabadell.process(event.src_path, OUT_FOLDER, file_name)
                
                else:
                    logger.info(f"{ERROR_RED}❌ This file is not asociated to any bank: {file_name}{RESET_COLOR}")
                    return

                if bankinter_csv_path and actual_importer.import_bankinter_csv(
                    bankinter_csv_path
                ):
                    move_to_imported(bankinter_csv_path)

                # Delete the original file from /input
                os.remove(event.src_path)

            except Exception as e:
                logger.info(f"{ERROR_RED}💥 Error processing {file_name}: {e}{RESET_COLOR}")

if __name__ == "__main__":
    os.makedirs(IN_FOLDER, exist_ok=True)
    os.makedirs(OUT_FOLDER, exist_ok=True)
    os.makedirs(IMPORTED_FOLDER, exist_ok=True)
    
    observer = Observer()
    observer.schedule(FilesMonitor(), path=IN_FOLDER, recursive=False)
    observer.start()
    logger.info("Starting the app")
    logger.info(
        f"🤖 Watching {IN_FOLDER}; CSV output: {OUT_FOLDER}; imported files: "
        f"{IMPORTED_FOLDER}"
    )
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()