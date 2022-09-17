import logging

import docker
from dotenv import dotenv_values
from sqlitedict import SqliteDict
from supabase import create_client

from .config import Config

ENV = dotenv_values(".env")  # Load environment variables

# Supabase setup
supabase = create_client(ENV['SUPABASE_URL'], ENV['SUPABASE_KEY'])

# setup loggers
logging.config.fileConfig(Config.LOG_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger(__name__)  

BUILD_LOGS_TABLE = SqliteDict(Config.APPS_LOGS, tablename="build_logs", autocommit=True)
NEW_DB_CONN = lambda: SqliteDict(Config.APPS_LOGS, tablename="build_logs", autocommit=True)

# Docker setup
DOCKER_CLIENT = docker.from_env()

APP_CONFIG_FILE = "paatr.yaml"

# Add python versions
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