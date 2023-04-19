# Register your models here.
from django.contrib import admin

from holiday.holiday_module.models import Holidays

admin.site.register(Holidays)
