import datetime
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from holiday.holiday_module.models import Holidays
from leaves.models import Leave, LeaveRequestDefaultRole, LeaveAllocations
from roles.models import Role
from settings.models import CompanySettings, AttendanceSettings, SettingsCurrency, SettingsDateFormat, SettingsTimeZone, \
    SettingsTimeFormat, ModuleSettings
from holiday.holiday_module.tests.constants import EMAIL, USERNAME, USER_PASS, DELETE_PERMISSION, ADD_PERMISSION, CHANGE_PERMISSION

TODAY = date.today()


class TestLeaveDurationsOfHolidays(APITestCase):
    """test cases to create,delete,update leave duration accroding to Holiday """
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
            company_address="Testing address",
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
        self.leave_request_default_role = LeaveRequestDefaultRole.objects.create(role=role)
        self.leave_allocation = LeaveAllocations.objects.create(user_id=self.user.id, total_leave=17,
                                                                allocated_leave=17, allocated_year=16,
                                                                leave_allocation_start_date=TODAY - timedelta(days=3),
                                                                leave_allocation_end_date=TODAY - timedelta(days=10),
                                                                remaining_leave=16, is_active=True, exceed_leave=0,
                                                                used_leave=15)
        self.leave = Leave.objects.create(
            requested_by_id=self.user.id,
            request_from_id=self.user.id,
            type="half",
            start_date=TODAY + timedelta(days=3),
            end_date=TODAY + timedelta(days=8),
            reason="xyz",
            duration=5.00,
            isadhoc_leave=False,
            available_on_phone=False,
            available_on_city=False,
            emergency_contact="+919877665456"
        )
        self.module = ModuleSettings.objects.create(module="Holidays", sub_module="Holidays",
                                                    is_display=True, dependent_on=None,
                                                    display_module="Holidays",
                                                    display_sub_module="Holidays")
        self.module.permission.add(self.delete_permission)
        self.module = ModuleSettings.objects.create(module="Leave", sub_module="My Leaves",
                                                    is_display=True, dependent_on=None,
                                                    display_module="Leave",
                                                    display_sub_module="My Leaves")
        self.module.permission.add(self.delete_permission)
        self.module.save()
        self.holidays_url = reverse('retrieve_update_destroy_holidays',
                                    kwargs={'id': self.holidays.id})
        self.holidays_url1 = reverse('retrieve_update_destroy_holidays',
                                     kwargs={'id': self.holidays1.id})
        self.holidays_url2 = reverse('retrieve_update_destroy_holidays',
                                     kwargs={'id': self.holidays2.id})
        self.holidays_add_url = reverse('list_create_holidays')

    def test_delete_holiday_increment_duration_leave(self):
        """when holiday is deleted then increase leave duration """
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.holidays_url)
        leave = Leave.objects.get(id=self.leave.id)
        leave_allocation = LeaveAllocations.objects.get(id=self.leave_allocation.id)
        self.assertEquals(leave.duration, 5.5)
        self.assertEquals(leave_allocation.remaining_leave, 16)
        self.assertEquals(leave_allocation.used_leave, 15)

    def test_delete_holiday1_increment_duration_leave(self):
        """when holiday is deleted then increase leave duration """
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.holidays_url1)
        leave = Leave.objects.get(id=self.leave.id)
        leave_allocation = LeaveAllocations.objects.get(id=self.leave_allocation.id)
        self.assertEquals(leave.duration, 5.00)
        self.assertEquals(leave_allocation.remaining_leave, 16.00)
        self.assertEquals(leave_allocation.used_leave, 15)

    def test_delete_holiday2_increment_duration_leave(self):
        """when holiday is deleted then increase leave duration """
        self.user.user_permissions.add(self.delete_permission)
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.holidays_url2)
        leave = Leave.objects.get(id=self.leave.id)
        leave_allocation = LeaveAllocations.objects.get(id=self.leave_allocation.id)
        self.assertEquals(leave.duration, 5.00)
        self.assertEquals(leave_allocation.remaining_leave, 16.00)
        self.assertEquals(leave_allocation.used_leave, 15)

    def test_create_holiday_reduce_duration_leave(self):
        """when holiday is created then reduce leave duration """
        self.user.user_permissions.add(self.create_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": TODAY + timedelta(days=4)
        }
        self.client.post(self.holidays_add_url, data)
        leave = Leave.objects.get(id=self.leave.id)
        leave_allocation = LeaveAllocations.objects.get(id=self.leave_allocation.id)
        self.assertEquals(leave.duration, 5.00)
        self.assertEquals(leave_allocation.remaining_leave, 16.00)
        self.assertEquals(leave_allocation.used_leave, 15)

    def test_create_holiday1_reduce_duration_leave(self):
        """when holiday is created then reduce leave duration """
        self.user.user_permissions.add(self.create_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": TODAY + timedelta(days=2)
        }
        self.client.post(self.holidays_add_url, data)
        leave = Leave.objects.get(id=self.leave.id)
        leave_allocation = LeaveAllocations.objects.get(id=self.leave_allocation.id)
        self.assertEquals(leave.duration, 5.00)
        self.assertEquals(leave_allocation.remaining_leave, 16.00)
        self.assertEquals(leave_allocation.used_leave, 15)

    def test_create_holiday2_reduce_duration_leave(self):
        """when holiday is created then reduce leave duration """
        self.user.user_permissions.add(self.create_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": TODAY + timedelta(days=9)
        }
        self.client.post(self.holidays_add_url, data)
        leave = Leave.objects.get(id=self.leave.id)
        leave_allocation = LeaveAllocations.objects.get(id=self.leave_allocation.id)
        self.assertEquals(leave.duration, 5.00)
        self.assertEquals(leave_allocation.remaining_leave, 16.00)
        self.assertEquals(leave_allocation.used_leave, 15)

    def test_update_holiday_update_duration_leave(self):
        """when holiday is update then update leave duration """
        self.user.user_permissions.add(self.put_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "sty",
            "date": TODAY + timedelta(days=4)
        }
        response = self.client.put(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 200, body)

    def test_update1_holiday_update_duration_leave(self):
        """when holiday is update then update leave duration """
        self.user.user_permissions.add(self.put_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "styy",
            "date": TODAY + timedelta(days=1)
        }
        response = self.client.put(self.holidays_url1, data)
        body = response.json()
        self.assertEquals(response.status_code, 200, body)

    def test_update2_holiday_update_duration_leave(self):
        """when holiday is update then update leave duration """
        self.user.user_permissions.add(self.put_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "stui",
            "date": TODAY + timedelta(days=9)
        }
        response = self.client.put(self.holidays_url2, data)
        body = response.json()
        self.assertEquals(response.status_code, 200, body)
