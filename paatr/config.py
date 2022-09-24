import os
from dotenv import dotenv_values

ENV = dotenv_values(".env") 

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

    # Supabase
    SUPABASE_URL = ENV["SUPABASE_URL"]
    SUPABASE_KEY = ENV["SUPABASE_KEY"]

    if ENV.get("MODE") == "development":
        NGINX_ENABLED_PAATR_APPS = ENV.get("NGINX_ENABLED_PAATR_APPS_DEV")
    else:
        NGINX_ENABLED_PAATR_APPS = ENV.get("NGINX_ENABLED_PAATR_APPS_PROD")
    
    DOMAIN = ENV.get("DOMAIN")