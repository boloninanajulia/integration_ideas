"""
Example for Employee
"""
import logging

from rest_framework.serializers import CharField

from your_app.models import EmployeeModel, OrganizationModel, PositionModel
from .base import BaseObjectSerializer


class EmployeeSerializer(BaseObjectSerializer):
    position_ms_id = CharField(max_length=50, default=None)
    organization_ms_id = CharField(max_length=50, default=None)

    def precess_before_saving(self, *, validated_data):
        validated_data, related_data = super().precess_before_saving(validated_data=validated_data)

        position = PositionModel.objects.get(ms_id=validated_data.pop('position_ms_id'))
        validated_data['position_id'] = position.id

        organization = OrganizationModel.objects.get(ms_id=validated_data.pop('organization_ms_id'))
        validated_data['organization_id'] = organization.id

        logging.error(f'validated_data: {validated_data}')
        return validated_data, related_data

    class Meta:
        model = EmployeeModel
        fields = [
            'ms_id',
            'name', 'position_ms_id',
            'date_joined', 'joined_by', 'organization_ms_id',
            'deleted_at'
        ]
