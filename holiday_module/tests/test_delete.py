import datetime
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from holiday.holiday_module.models import Holidays
from roles.models import Role
from settings.models import (CompanySettings, AttendanceSettings, SettingsCurrency, SettingsDateFormat,
                             SettingsTimeZone, SettingsTimeFormat, ModuleSettings)
from holiday.holiday_module.tests.test_common import upload_image_company_logo, upload_image_favicon
from holiday.holiday_module.tests.constants import EMAIL, USERNAME, USER_PASS, DELETE_PERMISSION

TODAY = date.today()


class TestDeleteHolidays(APITestCase):
    """test cases to delete holidays"""
    email = EMAIL
    username = USERNAME
    user_pass = USER_PASS

    def setUp(self):
        """set up to create permissions, user, role, attendance, currency, time-format, timezone, company, holiday"""
        user = get_user_model()
        role = Role.objects.create(name='Testing', code='TT', type='test')
        self.delete_permission = Permission.objects.get(codename=DELETE_PERMISSION)
        self.user = user.objects.create_user(
            email=self.email,
            password=self.user_pass,
            username=self.username,
            role=role,
            is_active=True
        )
        self.attendance = AttendanceSettings.objects.create(
            created_by_id=self.user.id,
            monday=True,
            tuesday=True,
            thursday=True,
            friday=True,
            saturday=True,
            sunday=True,
            daily_working_hours="8:20",
        )
        self.currency = SettingsCurrency.objects.create(
            created_by_id=self.user.id,
            currency="INR(@@)",
            is_active=True
        )
        self.dateformat = SettingsDateFormat.objects.create(
            created_by_id=self.user.id,
            date_format="%d-%m-%Y",
            is_active=True
        )
        self.timezone = SettingsTimeZone.objects.create(
            created_by_id=self.user.id,
            time_zone="Asia/Delhi",
            is_active=True
        )
        self.timeformat = SettingsTimeFormat.objects.create(
            created_by_id=self.user.id,
            time_format="%H:%M:%S",
            is_active=True
        )

        create_time = datetime.time(12, 00, 00)
        used_time = create_time.strftime(self.timeformat.time_format)

        self.company = CompanySettings.objects.create(
            created_by_id=self.user.id,
            company_name="test",
            company_email="admin@test.com",
            company_logo=upload_image_company_logo(),
            favicon=upload_image_favicon(),
            company_address="test address",
            company_phone_number="+919601457841",
            company_website="www.test.com",
            financial_year_start_date=TODAY + timedelta(days=1),
            financial_year_end_date=TODAY + timedelta(days=365),
            file_size=10,
            file_type="MB",
            image_size=10,
            image_type="MB",
            time_zone=self.timezone,
            time_format=self.timeformat,
            date_format=self.dateformat,
            currency=self.currency,
            daily_sod_defaulter_execution_time=used_time,
            is_active=True
        )
        self.holidays = Holidays.objects.create(
            id=1,
            created_by_id=self.user.id,
            name="diwali",
            date="2023-09-16"
        )
        self.module = ModuleSettings.objects.create(module="Holidays", sub_module="Holidays",
                                                    is_display=True, dependent_on=None,
                                                    display_module="Holidays",
                                                    display_sub_module="Holidays")
        self.module.permission.add(self.delete_permission)
        self.holidays_url = reverse('retrieve_update_destroy_holidays',
                                    kwargs={'id': self.holidays.id})
        self.holidays_url_wrong_id = reverse('retrieve_update_destroy_holidays',
                                             kwargs={'id': 98})

    def test_delete_holidays_with_valid_id(self):
        """test cases to delete holidays with valid id"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.holidays_url)
        self.assertEquals(response.status_code, 200)

    def test_delete_holidays_with_invalid_id(self):
        """test cases to delete holidays with invalid id"""
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.holidays_url_wrong_id)
        self.assertEquals(response.status_code, 404)

    def test_delete_holidays_with_no_permission(self):
        """test cases to delete holidays with no permission"""
        response = self.client.delete(self.holidays_url)
        self.assertEquals(response.status_code, 401)
