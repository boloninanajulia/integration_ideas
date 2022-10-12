"""
Example for OrganizationPage
"""
"""
Example for OrganizationPage
"""
import json
import logging

from rest_framework.serializers import CharField, ListField

from your_app.models import OrganizationPage, DistrictModel, AreaModel, OrganizationAreaPlacement
from your_app.blocks.body import BodyStreamBlock
from .base_page import BasePageSerializer


class OrganizationPageSerializer(BasePageSerializer):
    district_ms_id = CharField(max_length=50, default=None)
    area_ms_id_list = ListField(child=CharField(max_length=50), default=[])

    def precess_before_saving(self, *, validated_data):
        validated_data, related_data = super().precess_before_saving(validated_data=validated_data)

        if 'district_ms_id' in validated_data:
            district = DistrictModel.objects.get(ms_id=validated_data.pop('district_ms_id'))
            validated_data['district_id'] = district.id
        else:
            validated_data['district_id'] = None

        areas = []
        if 'area_ms_id_list' in validated_data:
            area_ms_id_list = validated_data.pop('area_ms_id_list')
            areas = AreaModel.objects.filter(ms_id__in=area_ms_id_list)
            assert areas.count() == len(area_ms_id_list), 'there are not all areas in db'

        validated_data['body'] = json.dumps(BodyStreamBlock._meta_class.default)

        related_data.update({'areas': areas})

        logging.error(f'validated_data: {validated_data}')
        return validated_data, related_data

    def create(self, validated_data):
        validated_data, related_data = self.precess_before_saving(validated_data=validated_data)
        instance = super().create(validated_data)

        for area in related_data['areas']:
            placement = OrganizationAreaPlacement.objects.filter(organization_page=instance, area=area).first()
            if not placement:
                placement = OrganizationAreaPlacement(organization_page=instance, area=area)
                placement.save()

        return instance

    def update(self, instance, validated_data):
        validated_data, related_data = self.precess_before_saving(validated_data=validated_data)
        instance = super().update(instance, validated_data)

        areas = related_data['areas']
        if len(areas) == 0:
            OrganizationAreaPlacement.objects.filter(organization_page=instance).delete()
        else:
            OrganizationAreaPlacement.objects.filter(organization_page=instance).exclude(area__in=areas).delete()
            for area in areas:
                placement = OrganizationAreaPlacement.objects.filter(organization_page=instance, area=area).first()
                if not placement:
                    placement = OrganizationAreaPlacement(organization_page=instance, area=area)
                    placement.save()

        return instance

    class Meta:
        model = OrganizationPage
        fields = [
            'ms_id',
            'title', 
            'phone_number', 'address',
            'district_ms_id', 'area_ms_id_list'
        ]
