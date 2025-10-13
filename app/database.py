import os
from sqlmodel import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('MYSQL_USER', 'fastapi_user')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'fastapi_pass')
DB_NAME = os.getenv('MYSQL_DATABASE', 'fastapi_db')
DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = os.getenv('DB_PORT', '3306')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL, echo=False)