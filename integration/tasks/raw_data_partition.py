from celery.utils.log import get_task_logger
from celery import current_app

from .raw_data_handler import RawIntegrationDataPartitionHandler

logger = get_task_logger(__name__)


@current_app.task
def run_raw_integration_data_partition_handler(*, ids=None):
    """
    Асинхронная задача разбиения сообщения (сырых данных)
    на экземпляры объектов интеграции
    """

    handler = RawIntegrationDataPartitionHandler()
    handler.start(ids=ids)
