import logging

from lyra.factory import create_app

logging.basicConfig(level=logging.INFO)

app = create_app()
