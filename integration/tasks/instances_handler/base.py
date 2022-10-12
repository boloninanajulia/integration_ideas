from abc import ABC
from typing import Optional
import hashlib
import json
import logging
from datetime import datetime, timedelta, date
import traceback

from django.forms.models import model_to_dict
from django.contrib.contenttypes.fields import ContentType

from wagtail.blocks.stream_block import StreamValue

from ...models import IntegrationInstance

log = logging.getLogger('celery')


class IntegrationInstanceBaseHandler(ABC):
    """
    Запускает создание|обновление|удвление объектов интеграции
    IntegrationInstance - Экземпляр объекта интеграции
    Статусы:
    0  = 'В ожидании обработки'
    1  = 'В процессе обработки'
    -2 = 'Ошибка обработки'
    2  = 'Обработано'
    """

    log = log
    model = None
    serializer_class = None

    ms_unique_filed = 'ms_id'

    def __init__(self, *, instance: IntegrationInstance, **kwargs):
        if not instance:
            raise Exception('You have to set an integration instance')
        self.instance = instance
        self.data = instance.data
        self.object = self._get_mapping_object()
        self._succeed_status_details = None

    @property
    def succeed_status_details(self) -> Optional[str]:
        return self._succeed_status_details

    def start(self) -> None:
        try:
            self._integration_instance_is_running()
            if self.object:
                self._update_object()
            else:
                self._create_object()
            self._integration_instance_is_successful()
        except Exception as e:
            self._integration_instance_failed(status_details=e)
            self.log.debug(f'raise error while handling {self.object}: {e}')
            print(traceback.format_exc())

    def _integration_instance_is_running(self) -> None:
        self._update_status(status=1, status_details=None)

    def _integration_instance_is_successful(self) -> None:
        self._update_status(status=2, status_details=self.succeed_status_details)

    def _integration_instance_failed(self, *, status_details) -> None:
        self._update_status(status=-2, status_details=status_details)

    def _update_status(self, *, status, status_details=None) -> None:
        self.instance.status = status
        self.instance.status_details = status_details
        self.instance.save()

    def _get_mapping_object(self) -> Optional[model]:
        mapping_filter = {self.ms_unique_filed: self.data[self.ms_unique_filed]}
        return self.model.objects.filter(**mapping_filter).first()

    def _build_object_info(self):
        object_ = self.object
        model = self.model
        return f'id={object_.id} ' \
               f'content_type={model._meta.app_label}.{model.__name__} '

    def _create_object(self, **kwargs) -> bool:
        serializer = self.serializer_class(data=self.data, **kwargs)
        serializer.is_valid(raise_exception=True)
        self.object = serializer.save()
        self._succeed_status_details = f'Created: {self._build_object_info()}'
        return True

    def _update_object(self, **kwargs) -> bool:
        serializer = self.serializer_class(instance=self.object, data=self.data, partial=True, **kwargs)
        serializer.is_valid(raise_exception=True)

        if self._object_is_the_same_as(serializer):
            self._succeed_status_details = f'Object wasn`t changed: {self._build_object_info()}'
            return False

        self.object = serializer.save()
        action = 'Edited and Deleted' if self.data.get('deleted_at') else 'Edited'
        self._succeed_status_details = f'{action}: {self._build_object_info()}'
        return True

    def _get_object_as_dict(self, *, field_names) -> dict:
        self.log.info(f'field_names: {field_names}')
        return model_to_dict(self.object, fields=field_names)

    def _object_is_the_same_as(self, serializer) -> bool:
        object_as_dict = self._get_object_as_dict(field_names=serializer.Meta.fields)
        updated_object_as_dict = dict(serializer.validated_data)

        object_md5 = self._get_md5_for_dict(item=object_as_dict)
        updated_object_md5 = self._get_md5_for_dict(item=updated_object_as_dict)

        return object_md5 == updated_object_md5

    def _get_md5_for_dict(self, *, item: dict):
        for field, value in item.items():
            if isinstance(value, StreamValue):
                item[field] = list(item[field].raw_data)
            elif isinstance(value, datetime):
                item[field] = value.strftime("%m/%d/%Y, %H:%M:%S")
            elif isinstance(value, date):
                item[field] = value.strftime("%m/%d/%Y")

        self.log.info(f'md5 for item: {item}')
        hashcode = hashlib.md5(
            json.dumps(item, sort_keys=True).encode('utf-8')
        ).hexdigest()

        self.log.info(f'hashcode: {hashcode}')
        return hashcode


class IntegrationInstancesHandler(ABC):
    """
    Проходится по всем экземплярам объектов интеграции определенного типа контента
    и запускает обработку
    """

    handler = IntegrationInstanceBaseHandler

    def __init__(self) -> None:
        if self.handler.model is None:
            raise Exception('You use incorrect handler class. You should set a model for it')

        model = self.handler.model
        self.content_type = ContentType.objects.get_for_model(model)

    def start(self, **kwargs):
        integration_instances = IntegrationInstance.objects.filter(
            content_type=self.content_type.id, status=0
        )

        return self.__start(integration_instances=integration_instances, **kwargs)

    def restart(self, days=None, **kwargs):
        mapping_filter = {'content_type': self.content_type.id, 'status': -2}
        if days:
            day = datetime.today() + timedelta(days=days)
            mapping_filter['created_at__date__gte'] = day

        integration_instances = IntegrationInstance.objects.filter(**mapping_filter)

        return self.__start(integration_instances=integration_instances, **kwargs)

    def __start(self, *, integration_instances, **kwargs) -> list:
        raw_entries = []
        for integration_instance in integration_instances:
            self._start_instance_handler(instance=integration_instance, **kwargs)

            raw_entry = integration_instance.raw_entry
            if raw_entry not in raw_entries:
                raw_entries.append(integration_instance.raw_entry)

        return raw_entries

    def _start_instance_handler(self, *, instance, **kwargs) -> None:
        instance_handler = self.handler(instance=instance, **kwargs)
        instance_handler.start()
