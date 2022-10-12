import logging
from typing import Optional, Any

from rest_framework import status, views, generics, authentication, permissions
from rest_framework.response import Response
from django.contrib.contenttypes.fields import ContentType

from your_app.models import OrganizationPage, EmployeeModel
from .serializers import RawIntegrationDataSerializer, OrganizationPageIntegrationSerializer, \
    EmployeeIntegrationSerializer
from .tasks import run_raw_integration_data_partition_handler
from .models import RawIntegrationData

log = logging.getLogger('default')


class IntegrationAPIView(views.APIView):
    serializer_class = RawIntegrationDataSerializer

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    model_integration_serializer_class = None
    model_integration_class = None

    def post(self, request, *args, **kwargs) -> Response:
        data = request.data
        if isinstance(data, dict):
            data = [data]

        # Записываем в таблицу с сырыми JSON -> статус 0=Сообщение  МС получено
        raw_entry = self.create(data=data)

        # Проверяем корректность схемы
        is_valid, errors = self.check_schema_data(data=data)

        # Корректно -> статус 1=Сообщение  МС получено. Сообщение корректно
        # Не корректно -> статус -1=Сообщение MC получено. Сообщение не корректн
        raw_entry_id = raw_entry.id
        self.update(
            instance=raw_entry,
            data={
                'status': 1 if is_valid else -1,
                'status_details': None if is_valid else str(errors)
            },
        )

        # Не корректно -> status = 400
        if not is_valid:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Корректно ->
        # Запускаем всинхронную задачу разбиения сырых данных по объектам
        try:
            run_raw_integration_data_partition_handler.apply_async(kwargs={'ids': [raw_entry_id]})
        except Exception as e:
            self.update(
                instance=raw_entry,
                data={
                    'status_details': 'Ошибка при запуске задачи разбиения по объектам: ' + str(e)
                },
            )

        # status = 200
        return Response('OK', status=status.HTTP_200_OK)

    def check_schema_data(self, *, data: list) -> (bool, Optional[Any]):
        serializer = self.model_integration_serializer_class(data=data, many=True)
        is_valid = serializer.is_valid()

        # it return list or dict
        errors = serializer.errors

        errors_as_dict = list(errors) \
            if isinstance(errors, list) \
            else dict(errors)
        return is_valid, errors_as_dict

    def create(self, *, data: dict) -> RawIntegrationData:
        content_type = ContentType.objects.get_for_model(self.model_integration_class)
        serializer = self.serializer_class(data={'data': data, 'content_type': content_type.id})
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def update(self, *, instance: RawIntegrationData, data: dict) -> None:
        serializer = self.serializer_class(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()


class OrganizationPageIntegrationAPIView(IntegrationAPIView):
    '''
    Принимает данные из мастер системы
    Формат: список элементов (json)

    Каждый элемент должен включать:
    __________
    ms_id: ИД в мастер-системе (обязательный)
    deleted_at: Дата удаления
    __________
    Общая информация
    __________
    title: Наименование (обязательный)
    district_ms_id: Округ (district__ms_id)
    area_ms_id_list: Район (list of area__ms_id)
    (district_ms_id/area_ms_id_list Одно из полей должно быть заполненной)
    __________
    Контакты
    __________
    phone_number: Телефон
    address: Адрес
    '''

    model_integration_serializer_class = OrganizationPageIntegrationSerializer
    model_integration_class = OrganizationPage


class EmployeeIntegrationAPIView(IntegrationAPIView):
    '''
    Принимает данные из мастер системы
    Формат: список элементов (json)

    Каждый элемент должен включать:
    __________
    ms_id: ИД в мастер-системе
    deleted_at: Дата логического удаления
    __________
    name: ФИО
    position_ms_id: Роль (position__ms_id)
    date_joined: Дата избрания
    joined_by: Кем выдвинут
    organization_ms_id: Организация (organization__ms_id)
    '''

    model_integration_serializer_class = EmployeeIntegrationSerializer
    model_integration_class = EmployeeModel
