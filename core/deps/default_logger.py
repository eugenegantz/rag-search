import logging

default_logger = logging.Logger("app")
default_logger.addHandler(logging.FileHandler('./info.log', encoding="utf-8"))
default_logger.addHandler(logging.StreamHandler())