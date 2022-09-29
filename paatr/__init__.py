import logging
import os

import docker
from dotenv import dotenv_values
from sqlitedict import SqliteDict
from supabase import create_client

from .config import Config

# Supabase setup
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

for dir in [Config.APP_FILES_DIR, Config.LOGS_DIR]:
    if not os.path.exists(dir):
        os.makedirs(dir)

# setup loggers
logging.config.fileConfig(Config.LOG_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger(__name__)  

BUILD_LOGS_TABLE = SqliteDict(Config.APPS_LOGS, tablename="build_logs", autocommit=True)
NEW_DB_CONN = lambda: SqliteDict(Config.APPS_LOGS, tablename="build_logs", autocommit=True)

# Docker setup
DOCKER_CLIENT = docker.from_env()

APP_CONFIG_FILE = "paatr.yaml"
INSTALLATION_FILE = "requirements.txt"
DEFAULT_PORT = 80

# Add python versions
PYTHON_VERSION_DOCKER_MAPS = {}

CONFIG_KEYS_X = ["runtime", "web"]
CONFIG_KEYS = CONFIG_KEYS_X + ["env"]

CONFIG_VALUE_VALIDATOR = {
    "runtime": lambda x: type(x) == str,
    "run": lambda x: type(x) == str or type(x) == list,
    "port": lambda x: type(x) == int,
    "web": lambda x: type(x) == str,
    "env": lambda x: type(x) == dict
}

PYTHON_RUNTIMES = {
    "python3.7": "python:3.7-alpine3.15",
    "python3.8": "python:3.8-alpine3.15",
    "python3.9": "python:3.9-alpine3.15",
    "python3.10": "python:3.10-alpine3.15"
}

DOCKER_TEMPLATE = """
FROM {runtime}
WORKDIR /app
COPY ./{app_name} .
{run}
EXPOSE {port}
CMD {web} > /paatr/logs.txt 2>&1
"""