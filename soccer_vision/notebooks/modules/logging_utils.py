from __future__ import annotations
import logging, sys

def get_logger(level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger("soccer_vision")
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(h)
    logger.setLevel(level)
    return logger

# Singleton used by modules
log = get_logger()