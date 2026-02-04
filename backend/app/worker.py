import os
from arq.connections import RedisSettings

from app.ocr.jobs import ocr_parse_job

class WorkerSettings:
    functions = [ocr_parse_job]
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )
