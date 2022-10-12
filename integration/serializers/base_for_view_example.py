from rest_framework.serializers import ModelSerializer, ALL_FIELDS, \
    CharField, ListField, DateTimeField
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError

from your_app.models import OrganizationModel, EmployeeModel, OrganizationPage


class OrganizationPageIntegrationSerializer(ModelSerializer):

    def run_validation(self, data=empty):
        value = super().run_validation(data)

        if data is not empty and not data.get('district_ms_id') and not data.get('area_ms_id_list'):
            raise ValidationError(detail={"area_ms_id_list/district_ms_id": [
                "Одно из полей должно быть заполненно"
            ]})

        return value

    ms_id = CharField(max_length=50)
    district_ms_id = CharField(max_length=50, required=False, allow_null=True)
    area_ms_id_list = ListField(child=CharField(max_length=50), required=False)
    deleted_at = DateTimeField(required=False)

    class Meta:
        model = OrganizationPage
        fields = [
            'ms_id',
            'title',
            'district_ms_id', 'area_ms_id_list',
            'phone_number', 'address',
            'deleted_at'
        ]


class EmployeeIntegrationSerializer(ModelSerializer):
    ms_id = CharField(max_length=50)
    position_ms_id = CharField(max_length=50, required=False, allow_null=True)

    class Meta:
        model = EmployeeModel
        fields = [
            'ms_id',
            'name', 'position_ms_id',
            'date_joined', 'joined_by', 'organization_id',
            'deleted_at'
        ]
