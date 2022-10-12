from django.db import models
from django.contrib.contenttypes.fields import ContentType

from wagtail.admin.edit_handlers import FieldPanel


class RawIntegrationData(models.Model):
    data = models.JSONField(verbose_name='Сырые данные')
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE
    )

    status = models.IntegerField(choices=(
        (0, 'Сообщение МС получено'),
        (1, 'Сообщение МС получено. Сообщение корректно'),
        (-1, 'Сообщение MC получено. Сообщение не корректно'),
        (2, 'Сообщение разбито по объектам'),
        (-2, 'Ошибка разбиения по объектам'),
        (3, 'Обработано'),
        (-3, 'Обработано с ошибками'),
    ), verbose_name='Статус', default=0)
    status_details = models.TextField(verbose_name='Детали статуса', null=True, blank=True)

    panels = [
        FieldPanel('data'),
        FieldPanel('status')
    ]

    def __str__(self):
        return f'{self.id} {self.content_type}'

    class Meta:
        verbose_name = 'Сырые интеграционные данные'
        verbose_name_plural = 'Сырые интеграционные данные'


class IntegrationInstance(models.Model):
    raw_entry = models.ForeignKey(RawIntegrationData, on_delete=models.CASCADE, verbose_name='Необработанная запись')
    data = models.JSONField(verbose_name='json экземпляра объекта')
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
        verbose_name='Тип контента'
    )
    status = models.IntegerField(choices=(
        (0, 'В ожидании обработки'),
        (1, 'В процессе обработки'),
        (-2, 'Ошибка обработки'),
        (2, 'Обработано')
    ), verbose_name='Статус', default=0)
    status_details = models.TextField(verbose_name='Детали статуса', null=True, blank=True)

    panels = [
        FieldPanel('data'),
        FieldPanel('status')
    ]

    def __str__(self):
        return f'#{self.id} {self.raw_entry}'

    class Meta:
        verbose_name = 'Экземпляр объекта интеграции'
        verbose_name_plural = 'Экземпляры объектов интеграции'
