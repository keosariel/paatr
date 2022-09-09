from dotenv import dotenv_values
from supabase import create_client, Client

ENV = dotenv_values(".env")  # take environment variables from .env.
supabase: Client = create_client(ENV['SUPABASE_URL'], ENV['SUPABASE_KEY'])