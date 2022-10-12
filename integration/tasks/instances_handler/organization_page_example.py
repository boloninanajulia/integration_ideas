"""
Example for Employee
"""
from wagtail.models import Page

from your_app.models import OrganizationPage
from ...serializers import OrganizationPageSerializer
from .base_page import PageIntegrationInstanceBaseHandler, PageIntegrationInstancesHandler


class OrganizationPageIntegrationInstanceHandler(PageIntegrationInstanceBaseHandler):
    model = OrganizationPage
    serializer_class = OrganizationPageSerializer

    def _get_object_as_dict(self, *, field_names) -> dict:
        object_as_dict = super()._get_object_as_dict(field_names=field_names)
        object_as_dict['district_ms_id'] = getattr(self.object.district, 'ms_id', None)
        object_as_dict['area_ms_id_list'] = [item.area.ms_id for item in self.object.area_placements.all()]
        return object_as_dict


class OrganizationPageIntegrationInstancesHandler(PageIntegrationInstancesHandler):
    handler = OrganizationPageIntegrationInstanceHandler

    def _get_parent_page(self) -> Page:
        # TODO правило определения главной страницы
        first_page = OrganizationPage.objects.first()
        return first_page.specific.get_parent() \
            if first_page else \
            super()._get_parent_page()
