import os


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    APP_FILES_DIR = os.path.join(BASE_DIR, "__apps__")
    APP_FILES_DIR = os.path.join(APP_FILES_DIR, "apps")

    # Logger
    LOG_CONFIG_FILE = os.path.join(BASE_DIR, "paatr/logging.conf")
    LOGS_DIR = os.path.join(BASE_DIR, "__logs__")
    LOGS_FILE = os.path.join(LOGS_DIR, "paatr.log")

    # App Logs
    APPS_LOGS = os.path.join(LOGS_DIR, "paatr-apps.log")