import datetime
from datetime import date, timedelta
from holiday.holiday_module.tests.constants import EMAIL, USERNAME, USER_PASS, ADD_PERMISSION
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from holiday.holiday_module.models import Holidays
from holiday.holiday_module.tests.test_common import upload_image, upload_invalid_image
from roles.models import Role
from settings.models import CompanySettings, SettingsDateFormat, SettingsTimeZone, SettingsCurrency, AttendanceSettings, \
    SettingsTimeFormat
from holiday.holiday_module.tests.test_common import upload_image_company_logo, upload_image_favicon

TODAY = date.today()

class TestAddHolidays(APITestCase):
    """test cases to create holidays"""
    holidays_url = reverse('list_create_holidays')
    email = EMAIL
    username = USERNAME
    user_pass = USER_PASS

    def setUp(self):
        """set up to create user, role, attendance, currency, time-format, timezone, company, holiday"""
        user = get_user_model()
        role = Role.objects.create(name='Testing', code='TT', type='test')
        self.add_permission = Permission.objects.get(codename=ADD_PERMISSION)
        self.user = user.objects.create_user(
            email=self.email,
            password=self.user_pass,
            username=self.username,
            role=role,
            is_active=True
        )
        self.attendance = AttendanceSettings.objects.create(
            created_by_id=self.user.id,
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
            company_name="Test",
            company_email="admin@test.com",
            company_logo=upload_image_company_logo(),
            favicon=upload_image_favicon(),
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
            time_format=self.timeformat,
            date_format=self.dateformat,
            currency=self.currency,
            daily_sod_defaulter_execution_time=used_time,
            is_active=True
        )
        self.holiday = Holidays.objects.create(
            created_by_id=self.user.id,
            name="diwali",
            date="2023-09-16",
            holiday_image=upload_image(),
        )

    def test_add_holidays_with_valid_data(self):
        """test cases to create holidays with valid data"""
        self.user.user_permissions.add(self.add_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": "2022-09-14",
            "holiday_image": upload_image(),
        }
        response = self.client.post(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 400, body)

    def test_add_holidays_with_no_data(self):
        """test cases to create holidays with no data"""
        self.user.user_permissions.add(self.add_permission)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.holidays_url)
        body = response.json()
        self.assertEquals(response.status_code, 400, body)

    def test_add_holidays_with_no_name(self):
        """test cases to create holidays with no name"""
        self.user.user_permissions.add(self.add_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "date": "2023-09-14"
        }
        response = self.client.post(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 400, body)

    def test_add_holidays_with_valid_data_but_no_permission(self):
        """test cases to create holidays with no permissions"""
        data = {
            "created_by_id": self.user,
            "name": "test",
            "date": "2023-09-14"
        }
        response = self.client.post(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 401, body)

    def test_add_duplicate_holidays(self):
        """test cases to create holidays with valid duplicate data"""
        self.user.user_permissions.add(self.add_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "diwali",
            "date": "2023-09-16",
        }
        response = self.client.post(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 400, body)

    def test_selected_date_as_declare_already_weekend(self):
        """test cases to create holidays where day is weekend"""
        self.user.user_permissions.add(self.add_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "diwali",
            "date": "2023-11-14"
        }
        response = self.client.post(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 400, body)

    def test_upload_invalid_image(self):
        """test cases to create holidays with invalid image"""
        self.user.user_permissions.add(self.add_permission)
        self.client.force_authenticate(user=self.user)
        data = {
            "created_by_id": self.user,
            "name": "diwali",
            "date": "2023-11-15",
            "upload_image": upload_invalid_image(),
        }
        response = self.client.post(self.holidays_url, data)
        body = response.json()
        self.assertEquals(response.status_code, 400, body)

