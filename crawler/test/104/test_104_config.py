# crawler/test/104/test_104_config.py
from crawler_enviroment.config import (
    WORKER_ACCOUNT,
    WORKER_PASSWORD,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
)

print(
    f"""
    WORKER_ACCOUNT: {WORKER_ACCOUNT}
    WORKER_PASSWORD: {WORKER_PASSWORD}
    RABBITMQ_HOST: {RABBITMQ_HOST}
    RABBITMQ_PORT: {RABBITMQ_PORT}
"""
)
