import logging

import structlog
from constants import LOG_DIR
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import filter_by_level


def setup_structlog():
    structlog.configure(
        processors=[
            filter_by_level,
            TimeStamper(fmt="iso"),
            JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[logging.FileHandler(LOG_DIR), logging.StreamHandler()],
    )


setup_structlog()
