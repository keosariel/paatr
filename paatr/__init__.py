import os
import logging

import docker
from dotenv import dotenv_values
from supabase import create_client, Client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_CONFIG_FILE = os.path.join(BASE_DIR, "paatr/logging.conf")
APP_FILES_DIR = os.path.join(BASE_DIR, "__apps__")
APP_FILES_DIR = os.path.join(APP_FILES_DIR, "apps")
APP_CONFIG_FILE = "paatr.yaml"

LOGS_DIR = os.path.join(BASE_DIR, "__logs__")
LOGS_FILE = os.path.join(LOGS_DIR, "paatr.log")
LOGS_LEVEL = "DEBUG"

ENV = dotenv_values(".env")  # take environment variables from .env.
supabase: Client = create_client(ENV['SUPABASE_URL'], ENV['SUPABASE_KEY'])

# TODO: Add python versions
PYTHON_VERSION_DOCKER_MAPS = {}

CONFIG_KEYS_X = ["runtime", "run", "port", "start"]
CONFIG_KEYS = CONFIG_KEYS_X + ["env"]

CONFIG_VALUE_VALIDATOR = {
    "runtime": lambda x: type(x) == str,
    "run": lambda x: type(x) == str or type(x) == list,
    "port": lambda x: type(x) == int,
    "start": lambda x: type(x) == str,
    "env": lambda x: type(x) == dict
}

DOCKER_TEMPLATE = """
FROM python:3.9-alpine3.15
WORKDIR /app
COPY ./{app_name} .
{run}
EXPOSE {port}
CMD {start}
"""

DOCKER_CLIENT = docker.from_env()
# setup loggers
logging.config.fileConfig(LOG_CONFIG_FILE, disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)  

class AppLogs:
    def __init__(self):
        self.logs = {}
    
    def add(self, app_name, logs_str):
        self.logs[app_name] = logs_str.split("\n")

ALL_APPS_LOGS_CACHE = AppLogs()