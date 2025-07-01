# crawler/logging_config.py

import logging


def setup_logging():
    """
    設定應用程式的日誌。
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
