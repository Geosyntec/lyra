import logging
from pathlib import Path

import pint

logging.getLogger("pint").setLevel(logging.ERROR)
ureg = pint.UnitRegistry()
ureg.load_definitions(str(Path(__file__).parent / "unit_def.txt"))
