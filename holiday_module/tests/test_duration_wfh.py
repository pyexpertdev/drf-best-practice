import datetime
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from holiday.holiday_module.models import Holidays
from holiday.holiday_module.tests.constants import EMAIL, USERNAME, USER_PASS, DELETE_PERMISSION, ADD_PERMISSION, CHANGE_PERMISSION
from roles.models import Role
from settings.models import CompanySettings, AttendanceSettings, SettingsCurrency, SettingsDateFormat, SettingsTimeZone, \
    SettingsTimeFormat, ModuleSettings
from work_from_home.models import WorkFromHomeRequestDefaultRole, WorkFromHome

TODAY = date.today()


class TestWFHDurationsOfHolidays(APITestCase):
    """test cases to create,delete,update Work from home duration according to Holiday """
    email = EMAIL
    username = USERNAME
    user_pass = USER_PASS

    def setUp(self):
        """set up to create permissions, user, role, attendance, currency, time-format, timezone, company, holiday"""
        user = get_user_model()
        role = Role.objects.create(name='Testing', code='TT', type='test')
        self.delete_permission = Permission.objects.get(codename=DELETE_PERMISSION)
        self.create_permission = Permission.objects.get(codename=ADD_PERMISSION)
        self.put_permission = Permission.objects.get(codename=CHANGE_PERMISSION)
        self.user = user.objects.create_user(
            email=self.email,
            password=self.user_pass,
            username=self.username,
            is_active=True,
            is_admin_user=True,
            is_superuser=True,
            role=role)
        self.attendance = AttendanceSettings.objects.create(
            created_by_id=self.user.id,
            monday=True,
            tuesday=True,
            wednesday=True,
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
            company_name="Test",
            company_email="admin@test.com",
            company_address="Testing",
            company_phone_number="+919601457841",
            company_website="www.test.com",
            financial_year_start_date=TODAY + timedelta(days=1),
            financial_year_end_date=TODAY + timedelta(days=365),
            file_size=10,
            file_type="MB",
            image_size=10,
            image_type="MB",
            time_zone=self.timezone,
            time_type="24 Hour",
            time_format=self.timeformat,
            date_format=self.dateformat,
            currency=self.currency,
            daily_sod_defaulter_execution_time=used_time,
            is_active=True
        )
        self.holidays = Holidays.objects.create(
            created_by_id=self.user.id,
            name="diwali",
            date=TODAY + timedelta(days=4)
        )
        self.holidays1 = Holidays.objects.create(
            created_by_id=self.user.id,
            name="holi",
            date=TODAY + timedelta(days=2)
        )
        self.holidays2 = Holidays.objects.create(
            created_by_id=self.user.id,
            name="duleti",
            date=TODAY + timedelta(days=9)
        )
        self.module = ModuleSettings.objects.create(module="Holidays", sub_module="Holidays",
                                                    is_display=True, dependent_on=None,
                                                    display_module="Holidays",
                                                    display_sub_module="Holidays")
        self.module.permission.add(self.delete_permission)
        self.module = ModuleSettings.objects.create(module="Work From Home", sub_module="My WFH Request",
                                                    is_display=True, dependent_on=None,
                                                    display_module="Work From Home",
                                                    display_sub_module="My WFH Request")
        self.module.permission.add(self.delete_permission)
        self.module.save()
        self.wfh_request_default_role = WorkFromHomeRequestDefaultRole.objects.create(role=role)
        self.work_from_home = WorkFromHome.objects.create(
            requested_by_id=self.user.id,
            request_from_id=self.user.id,
            type="half",
            half_day_status="firsthalf",
            start_date=TODAY + timedelta(days=3),
            end_date=TODAY + timedelta(days=8),
            reason="test",
            duration=5,
            isadhoc_wfh=False,
        )
        self.holidays_url = reverse('retrieve_update_destroy_holidays',
                                    kwargs={'id': self.holidays.id})
        self.holidays_url1 = reverse('retrieve_update_destroy_holidays',
                                     kwargs={'id': self.holidays1.id})
        self.holidays_url2 = reverse('retrieve_update_destroy_holidays',
                                     kwargs={'id': self.holidays2.id})
        self.holidays_add_url = reverse('list_create_holidays')

    def test_delete_holiday_increment_duration_wfh(self):
        """when holiday is deleted then increase work from duration """
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.holidays_url)
        wfh = WorkFromHome.objects.get(id=self.work_from_home.id)
        self.assertEquals(wfh.duration, 5.5)

    def test_delete_holiday1_increment_duration_wfh(self):
        """when holiday is deleted then increase work from duration """
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.holidays_url1)
        wfh = WorkFromHome.objects.get(id=self.work_from_home.id)
        self.assertEquals(wfh.duration, 5)

    def test_delete_holiday2_increment_duration_wfh(self):
        """when holiday is deleted then increase work from duration """
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.holidays_url2)
        wfh = WorkFromHome.objects.get(id=self.work_from_home.id)
        self.assertEquals(wfh.duration, 5.00)

    def test_create_holiday_reduce_duration_wfh(self):
        """when holiday is created then reduce work from duration """
        self.user.user_permissions.add(self.create_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": TODAY + timedelta(days=3)
        }
        self.client.post(self.holidays_add_url, data)
        wfh = WorkFromHome.objects.get(id=self.work_from_home.id)
        self.assertEquals(int(wfh.duration), int(4.50))

    def test_create_holiday1_reduce_duration_wfh(self):
        """when holiday is created then reduce work from duration """
        self.user.user_permissions.add(self.create_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": TODAY + timedelta(days=1)
        }
        self.client.post(self.holidays_add_url, data)
        wfh = WorkFromHome.objects.get(id=self.work_from_home.id)
        self.assertEquals(wfh.duration, 5.00)

    def test_create_holiday2_reduce_duration_wfh(self):
        """when holiday is created then reduce work from duration """
        self.user.user_permissions.add(self.create_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": TODAY + timedelta(days=9)
        }
        self.client.post(self.holidays_add_url, data)
        wfh = WorkFromHome.objects.get(id=self.work_from_home.id)
        self.assertEquals(wfh.duration, 5.00)

    def test_update_holiday_update_duration_wfh(self):
        """when holiday is update then update work from duration """
        self.user.user_permissions.add(self.put_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "sty",
            "date": TODAY + timedelta(days=4)
        }
        response = self.client.put(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 200, body)

    def test_update1_holiday_update_duration_wfh(self):
        """when holiday is update then update work from duration """
        self.user.user_permissions.add(self.put_permission)
        self.client.force_authenticate(user=self.user)

        data = {
            "name": "styy",
            "date": TODAY + timedelta(days=1)
        }
        response = self.client.put(self.holidays_url1, data)
        body = response.json()
        self.assertEquals(response.status_code, 200, body)

    def test_update2_holiday_update_duration_wfh(self):
        """when holiday is update then update work from duration """
        self.user.user_permissions.add(self.put_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "stui",
            "date": TODAY + timedelta(days=9)
        }
        response = self.client.put(self.holidays_url2, data)
        body = response.json()
        self.assertEquals(response.status_code, 200, body)
