import logging


def get_logger(name):
    short = name.split(".", 1)[-1] if name.startswith("billing.") else name
    return logging.getLogger("billing." + short)
