import os

from dotenv import dotenv_values
from supabase import create_client, Client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_APP_FILES_DIR = os.path.join(BASE_DIR, "__apps_data__")
APP_FILES_DIR = os.path.join(_APP_FILES_DIR, "apps")

ENV = dotenv_values(".env")  # take environment variables from .env.
supabase: Client = create_client(ENV['SUPABASE_URL'], ENV['SUPABASE_KEY'])