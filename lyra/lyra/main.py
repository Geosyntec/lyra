import logging
import os

from lyra.factory import create_app

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

app = create_app()
