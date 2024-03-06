import os
import logging
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(level = logging.DEBUG if os.getenv("MODE") == "dev" else logging.WARN,
                    filename = BASE_DIR.joinpath("logs/errors.log"),
                    filemode = "w",
                    format = "%(asctime)s - %(name)s[%(funcName)s(%(lineno)d)] - %(levelname)s - %(message)s")

LOG = logging.getLogger(__name__)

try:
    connect = psycopg2.connect(host="localhost", 
                               user=os.getenv("DB_USER"), 
                               password=os.getenv("DB_PASSWORD"), 
                               dbname="mta_db")
except Exception as err:
    LOG.error(err)
    print("Ошибка при подключении к базе данных")