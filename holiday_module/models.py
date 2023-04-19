# Create your models here.
from django.conf import settings
from django.db import models
from django.utils import timezone


class Common(models.Model):
    """
    this common model contain some common fields which used in every model .
    """
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   related_name='%(class)s_createdby', on_delete=models.SET_NULL, null=True, blank=True)

    modified_at = models.DateTimeField(blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    related_name='%(class)s_modifiedby', on_delete=models.SET_NULL, null=True,
                                    blank=True)

    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   related_name='%(class)s_deletedby', on_delete=models.SET_NULL, null=True,
                                   blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Holidays(Common):
    """holiday model"""
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    holiday_image = models.ImageField(upload_to="holiday_img", blank=True, null=True)

    class Meta:
        db_table = 'Holidays'
        verbose_name = 'Holiday'
        permissions = [
            ("list_holidays", "Can list holidays")
        ]

    def __str__(self):
        return self.name
