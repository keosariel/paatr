import os

from dotenv import dotenv_values
from supabase import create_client, Client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_FILES_DIR = os.path.join(BASE_DIR, "__apps_data__")
APP_FILES_DIR = os.path.join(APP_FILES_DIR, "apps")
APP_CONFIG_FILE = "paatr.yaml"

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
FROM python:{runtime}
WORKDIR /app
COPY . .
{run}
EXPOSE {port}
CMD {start}
"""