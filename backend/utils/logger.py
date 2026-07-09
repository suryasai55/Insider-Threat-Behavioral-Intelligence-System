import os
import logging
from logging.handlers import RotatingFileHandler

# Define log path
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Create a logger
logger = logging.getLogger('insider_threat_backend')
logger.setLevel(logging.INFO)

# Define formatter
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s (Line: %(lineno)d): %(message)s'
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Rotating File Handler (Max 10MB per file, backup count = 5)
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Add handlers
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def get_logger():
    return logger
