import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC")
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")

if not DATABASE_URL_ASYNC:
    raise RuntimeError("DATABASE_URL_ASYNC is not set")
if not DATABASE_URL_SYNC:
    raise RuntimeError("DATABASE_URL_SYNC is not set")
