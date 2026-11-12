import logging
from .cli import main

logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(name)s %(message)s')
raise SystemExit(main())
