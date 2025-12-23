import os
from loguru import logger


def setup_logging():
    logger.remove()
    os.makedirs("logs", exist_ok=True)
    logger.add(sink="logs/app.log",
               level="INFO",
               format="{time:HH:mm:ss} | {level:8} | {name}:{function}:{line} | {message}",
               rotation="10 MB",
               retention="7 day",
               compression="zip")
