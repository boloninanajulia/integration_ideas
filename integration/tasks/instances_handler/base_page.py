from wagtail.models import Page

from ...serializers import BasePageSerializer
from .base import IntegrationInstancesHandler, IntegrationInstanceBaseHandler


class PageIntegrationInstanceBaseHandler(IntegrationInstanceBaseHandler):
    model = Page
    serializer_class = BasePageSerializer

    def __init__(self, *, instance, parent_page, **kwargs):
        """
        @is_draft: работать не с объектами (создавать, обновлять), а с их черновиками
        """
        self.parent_page = parent_page
        self.is_draft = kwargs.pop('is_draft') if 'is_draft' in kwargs else False

        super().__init__(instance=instance, **kwargs)

    def _build_object_info(self):
        page = self.object
        model = self.model
        return f'{page.title}" id={page.id} ' \
               f'content_type={model._meta.app_label}.{model.__name__} ' \
               f'path={page.url_path}'

    def _create_object(self) -> bool:
        if not self.parent_page:
            raise Exception("You can`t create pages without parent page")

        # parameter for logical deleting. If new page with parameter set
        deleted_at = self.data.get('deleted_at')
        is_created = super()._create_object(is_draft=self.is_draft, parent_page=self.parent_page, deleted_at=deleted_at)

        if is_created and not self.is_draft and not deleted_at:
            action = 'Created and Published'
            self._succeed_status_details = f'{action}: {self._build_object_info()}'
        return is_created

    def _update_object(self) -> bool:
        # parameter for logical deleting
        deleted_at = self.data.get('deleted_at')
        is_updated = super()._update_object(is_draft=self.is_draft, deleted_at=deleted_at)

        if is_updated:
            if not self.is_draft and not deleted_at:
                action = 'Edited and Published'
                self._succeed_status_details = f'{action}: {self._build_object_info()}'
            elif deleted_at:
                action = 'Edited and Unpublished'
                self._succeed_status_details = f'{action}: {self._build_object_info()}'
        return is_updated


class PageIntegrationInstancesHandler(IntegrationInstancesHandler):
    handler = PageIntegrationInstanceBaseHandler

    def __init__(self) -> None:
        super().__init__()

        self.parent_page = self._get_parent_page()

    def _get_parent_page(self) -> Page:
        # TODO правило определения главной страницы
        return Page.objects.filter(slug='main').first()

    def _start_instance_handler(self, *, instance, **kwargs) -> None:
        instance_handler = self.handler(instance=instance, parent_page=self.parent_page, **kwargs)
        instance_handler.start()
