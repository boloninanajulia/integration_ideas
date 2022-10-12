from rest_framework.serializers import ALL_FIELDS, empty
from wagtail.core.models import Page

from .base import BaseObjectSerializer


class BasePageSerializer(BaseObjectSerializer):

    def __init__(self, instance=None, data=empty, **kwargs):
        self.is_draft = kwargs.pop('is_draft', False)
        self.parent_page = kwargs.pop('parent_page', None)
        self.deleted_at = kwargs.pop('deleted_at', None)

        super().__init__(instance, data, **kwargs)

    def create(self, validated_data):
        # TODO check created by in the object

        validated_data['live'] = False
        instance = self.Meta.model(**validated_data)
        self.parent_page.add_child(instance=instance)
        revision = instance.save_revision()

        if not self.is_draft and not self.deleted_at:
            revision.publish()

        return instance

    def update(self, instance, validated_data):
        # TODO check created by in the object

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        revision = instance.save_revision()

        if self.deleted_at:
            instance.unpublish()
        elif not self.is_draft:
            revision.publish()

        return instance

    class Meta:
        model = Page
        fields = ('title',)
