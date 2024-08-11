# ============================================================
#  File:        logger.py
#  Author:      Sergio Ribeiro
#  Description: Rotina de log
# ============================================================
import os
import datetime

# Caminho padrão (caso config.json não tenha sido carregado ainda)
LOG_PATH = "./logs"
LOG_FILE = os.path.join(
    LOG_PATH,
    datetime.datetime.now().strftime("%Y%m%d %H-%M-%S") + " eda.log"
)
os.makedirs(LOG_PATH, exist_ok=True)


def set_log_path(new_path: str):
    """Atualiza o caminho do log e recria o arquivo de log."""
    global LOG_PATH, LOG_FILE
    LOG_PATH = new_path
    os.makedirs(LOG_PATH, exist_ok=True)
    LOG_FILE = os.path.join(
        LOG_PATH,
        datetime.datetime.now().strftime("%Y%m%d %H-%M-%S") + " eda.log"
    )

def log_event(location: str, occurrence: str, detail: str, log_type: str = "info"):
    """
    Escreve uma linha no arquivo de log no formato:
    datetime, location, occurrence, detail, type
    """
    os.makedirs(LOG_PATH, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = "Datetime;location,occurrence,detail,log_type\n"
    entry = entry + f"{timestamp};{location};{occurrence};{detail};{log_type}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
