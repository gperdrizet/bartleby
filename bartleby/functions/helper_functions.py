import glob
import logging
import os
import bartleby.configuration as conf
from pathlib import Path
from logging.handlers import RotatingFileHandler

def start_logger():
    '''Sets up logging, returns logger'''

    # Clear logs if asked
    if conf.CLEAR_LOGS == True:
        for file in glob.glob(f'{conf.LOG_PATH}/*.log*'):
            os.remove(file)

    # Create logger
    logger = logging.getLogger('bartleby')
    logger.setLevel(conf.LOG_LEVEL)
    
    handler = RotatingFileHandler(
        f'{conf.LOG_PATH}/bartleby.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB, 
        backupCount=5
    )
    
    formatter = logging.Formatter(conf.LOG_PREFIX, datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info('############################################### ')
    logger.info('############## Starting bartleby ############## ')
    logger.info('############################################### ')

    return logger

def start_discord_logger():
    '''Sets up logging for discord.py'''

    logger = logging.getLogger('discord')
    logger.setLevel(conf.LOG_LEVEL)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    handler = RotatingFileHandler(
        f'{conf.LOG_PATH}/discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def check_directory_structure():
    '''Check to make sure we have directories that were not tracked by git'''

    Path(conf.HF_CACHE).mkdir(parents=True, exist_ok=True)
    Path(conf.LOG_PATH).mkdir(parents=True, exist_ok=True)