from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, \
    modeladmin_register, PermissionHelper

from .models import RawIntegrationData, IntegrationInstance


class ReadOnlyPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True
    def user_can_create(self, user):
        return False
    def user_can_edit_obj(self, user, obj):
        return False
    def user_can_delete_obj(self, user, obj):
        return False


class ContentTypeFilter(admin.SimpleListFilter):
    title = 'Типы контента'
    parameter_name = 'content_type'

    def lookups(self, request, model_admin):
        items = ContentType.objects.filter(app_label='your_app', model__in=('organizationpage', 'employeemodel'))
        lookups = [(item.id, str(item)) for item in items]
        return lookups

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(content_type_id=value)
        else:
            return queryset


class RawIntegrationDataAdmin(ModelAdmin):
    model = RawIntegrationData
    permission_helper_class = ReadOnlyPermissionHelper
    inspect_view_enabled = True

    menu_label = 'Сырые интеграционные данные'
    menu_icon = 'doc-full'
    menu_order = 1
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_filter = (ContentTypeFilter, 'status', 'created_at',)
    search_fields = ('id', 'data')

    list_display = ('__str__', 'status', 'status_details', 'updated_at')


class IntegrationInstanceAdmin(ModelAdmin):
    model = IntegrationInstance

    menu_label = 'Экземпляры объектов интеграции'
    menu_icon = 'doc-full'
    menu_order = 2
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_filter = ('content_type', 'status', 'created_at')
    search_fields = ('id', 'data')

    list_display = ('__str__', 'status', 'status_details', 'updated_at')


class IntegrationGroup(ModelAdminGroup):
    menu_label = 'MS отчеты'
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (
        RawIntegrationDataAdmin, IntegrationInstanceAdmin,
    )


modeladmin_register(IntegrationGroup, )
