import logging

from ...models import IntegrationInstance, RawIntegrationData

log = logging.getLogger('celery')


class RawIntegrationDataPartitionHandler:
    """
    1 = 'Сообщение МС получено. Сообщение корректно'
    2  = 'Сообщение разбито по объектам'
    -2 = 'Ошибка разбиения по объектам'
    """
    def start(self, *, ids=None):
        raw_entries = RawIntegrationData.objects.filter(status__in=[1, -2])
        if ids:
            raw_entries = raw_entries.filter(id__in=ids)

        for raw_entry in raw_entries:
            self.raw_data_dividing(raw_entry=raw_entry)
        return raw_entries

    def raw_data_dividing(self, *, raw_entry):
        try:
            instances = []
            for instance_data in raw_entry.data:
                instances.append(IntegrationInstance(
                    raw_entry=raw_entry, data=instance_data,
                    content_type=raw_entry.content_type
                ))

            IntegrationInstance.objects.bulk_create(instances)

            self._is_successful(raw_entry=raw_entry)
        except Exception as e:
            self._failed(raw_entry=raw_entry, error=e)

    @staticmethod
    def _failed(*, raw_entry, error):
            raw_entry.status = -2
            raw_entry.status_details = error
            raw_entry.save()

    @staticmethod
    def _is_successful(*, raw_entry):
        raw_entry.status = 2
        raw_entry.status_details = None
        raw_entry.save()


class RawIntegrationDataStatusHandler:
    """
    2 = 'Сообщение разбито по объектам'
    3 = 'Обработано'
    -3 = 'Обработано с ошибками'
    """
    def start(self, *, ids=None):
        """
        IntegrationInstance statuses
        -2 = 'Ошибка обработки'
        2 = 'Обработано
        """
        if ids:
            raw_entries = RawIntegrationData.objects.filter(id__in=ids)
        else:
            raw_entries = RawIntegrationData.objects.filter(status=2)

        for raw_entry in raw_entries:
            self.raw_data_updating(raw_entry=raw_entry)

    def raw_data_updating(self, *, raw_entry):
        instances = IntegrationInstance.objects.filter(raw_entry=raw_entry)
        status_details = [{'ms_id': item.data['ms_id'], 'status_details': item.status_details} for item in instances]

        failed_instances = instances.filter(status=-2)

        raw_instances_count = instances.exclude(status__in=[-2, 2]).count()
        failed_instances_count = failed_instances.count()

        log.info(f'status_handler. raw entry: {raw_entry.id}, '
                 f'failed: {failed_instances_count}, '
                 f'raw: {raw_instances_count}')

        if failed_instances_count == 0 and raw_instances_count == 0:
            self.__update_status(raw_entry=raw_entry, status=3, status_details=status_details)
        elif failed_instances_count > 0 and raw_instances_count == 0:
            self.__update_status(raw_entry=raw_entry, status=-3, status_details=status_details)

    @staticmethod
    def __update_status(*, raw_entry, status, status_details):
        raw_entry.status = status
        raw_entry.status_details = status_details
        raw_entry.save()
