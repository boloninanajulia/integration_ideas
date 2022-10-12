import logging

from celery.utils.log import get_task_logger

from celery import current_app
from .raw_data_handler import RawIntegrationDataStatusHandler

logger = get_task_logger(__name__)
log = logging.getLogger('celery')


@current_app.task
def run_raw_integration_data_status_handler(*, ids=None):
    """
    Асинхронная задача проверки статусов всех экземпляров
    объектов интеграции в рамках одного сообщения
    """
    log.info(f'run_raw_integration_data_status_handler ids={ids}')
    handler = RawIntegrationDataStatusHandler()
    handler.start(ids=ids)
