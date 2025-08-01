# Import libraries
import os
from dotenv import load_dotenv

# Local variables
excel_filename = 'excel_file.xlsx'
context_filename = 'columns_context.txt'

# Read .env file
load_dotenv()

# Global variables
EXCEL_FILE_PATH = os.path.join('data', excel_filename)
CONTEXT_FILE_PATH = os.path.join('data', context_filename)
MODEL_CODE_GENERATOR = os.getenv('MODEL_CODE_GENERATOR')
MODEL_CHAT_LLM = os.getenv('MODEL_CHAT_LLM')