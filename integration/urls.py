from django.urls import path

from .views import OrganizationPageIntegrationAPIView, EmployeeIntegrationAPIView


urlpatterns_api = [
    path('organization_page/', OrganizationPageIntegrationAPIView.as_view(), name='organization-page-integration'),
    path('employee/', EmployeeIntegrationAPIView.as_view(), name='employee-integration')
]
