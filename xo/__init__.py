name = "xml-ormz"


import sys
from loguru import logger

# remove all first
logger.remove()

__logger_id__ = None

def set_log_level(*, level="INFO", enable=True):
    global __logger_id__
    
    if type( __logger_id__ ) == int:
        logger.remove( __logger_id__ )

    if enable:
        if level in ["DEBUG", "TRACE"]:
            __logger_id__ = logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", level=level)
        else:
            __logger_id__ = logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>", level=level)
    else:
        logger.remove( __logger_id__ )

