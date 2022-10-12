from celery.utils.log import get_task_logger

from celery import current_app
from .instances_handler import OrganizationPageIntegrationInstancesHandler, EmployeeIntegrationInstancesHandler
from .raw_data_logging import run_raw_integration_data_status_handler

logger = get_task_logger(__name__)


@current_app.task
def run_integration_instances_handler(*, is_draft=False):
    """
    Асинхронная задача обработки экземпляров объектов интеграции
    # 1. Запускает обработчики IntegrationInstances для каждого типа данных
    в отдельности
    # 2. Запускает задачу обнавления статусов таблицы RawIntegrationData
    """

    handler = OrganizationPageIntegrationInstancesHandler()
    raw_entries = handler.start(is_draft=is_draft)

    handler = EmployeeIntegrationInstancesHandler()
    raw_entries += handler.start(is_draft=is_draft)

    if len(raw_entries):
        run_raw_integration_data_status_handler.apply_async(kwargs={'ids': [entry.id for entry in raw_entries]})


@current_app.task
def rerun_integration_instances_handler(*, days=None, is_draft=False):
    """
    Асинхронная задача повторной обработки экземпляров объектов интеграции
    # 1. Запускает обработчики IntegrationInstances для каждого типа данных
    в отдельности
    # 2. Запускает задачу обнавления статусов таблицы RawIntegrationData
    """

    handler = OrganizationPageIntegrationInstancesHandler()
    raw_entries = handler.restart(days=days, is_draft=is_draft)

    handler = EmployeeIntegrationInstancesHandler()
    raw_entries += handler.restart(days=days, is_draft=is_draft)

    if len(raw_entries):
        run_raw_integration_data_status_handler.apply_async(kwargs={'ids': [entry.id for entry in raw_entries]})
