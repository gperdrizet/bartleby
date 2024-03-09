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
    logger = logging.getLogger(__name__)
    handler = RotatingFileHandler(f'{conf.LOG_PATH}/bartleby.log', maxBytes=80000, backupCount=10)
    formatter = logging.Formatter(conf.LOG_PREFIX, datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(conf.LOG_LEVEL)

    logger.info('############################################### ')
    logger.info('############## Starting bartleby ############## ')
    logger.info('############################################### ')

    return logger

def check_directory_structure():
    '''Check to make sure we have directories that were not tracked by git'''

    Path(conf.HF_CACHE).mkdir(parents=True, exist_ok=True)
    Path(conf.LOG_PATH).mkdir(parents=True, exist_ok=True)