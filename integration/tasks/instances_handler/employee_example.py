"""
Example for Employee
"""
from your_model.models import EmployeeModel
from ...serializers import EmployeeIntegrationSerializer
from .base import IntegrationInstancesHandler, IntegrationInstanceBaseHandler


class EmployeeIntegrationInstanceHandler(IntegrationInstanceBaseHandler):
    model = EmployeeModel
    serializer_class = EmployeeIntegrationSerializer

    def _get_object_as_dict(self, *, field_names) -> dict:
        object_as_dict = super()._get_object_as_dict(field_names=field_names)
        object_as_dict['position_ms_id'] = getattr(self.object.position, 'ms_id', None)
        object_as_dict['organization_ms_id'] = getattr(self.object.organization, 'ms_id', None)
        return object_as_dict


class EmployeeIntegrationInstancesHandler(IntegrationInstancesHandler):
    handler = EmployeeIntegrationInstanceHandler
