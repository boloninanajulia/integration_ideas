from rest_framework.serializers import ModelSerializer, ALL_FIELDS, CharField, ListField, DateTimeField
from django.utils import timezone

from ..models import RawIntegrationData


class RawIntegrationDataSerializer(ModelSerializer):
    class Meta:
        model = RawIntegrationData
        fields = ALL_FIELDS


class BaseObjectSerializer(ModelSerializer):
    def precess_before_saving(self, *, validated_data):
        validated_data['load_from_ms_at'] = timezone.now()

        return validated_data, {}

    def create(self, validated_data):
        validated_data, _ = self.precess_before_saving(validated_data=validated_data)
        instance = super().create(validated_data)

        return instance

    def update(self, instance, validated_data):
        validated_data, _ = self.precess_before_saving(validated_data=validated_data)
        instance = super().update(instance, validated_data)

        return instance
