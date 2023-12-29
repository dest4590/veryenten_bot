import logging
import colorlog

def setup_logger(name):
    formatter = colorlog.ColoredFormatter(
        "[%(log_color)s%(levelname)s%(reset)s] %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red,bg_white',},
        secondary_log_colors={},
        style='%',
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)
 
    logger.addHandler(handler)

    return logger

logger = setup_logger('VeryentenBotLogger')