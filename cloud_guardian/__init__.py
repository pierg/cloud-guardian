import sys

from loguru import logger

# Set the logger to output messages at the INFO level and higher
logger.remove()  # Removes all default handlers
logger.add(sys.stderr, level="INFO")
