import os
import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from holiday.holiday_module.constants import CHECK_WEEKEND, ATTENDANCE_SETTING, COMPANY_SETTING, HOLIDAY_DELETE_ERROR, \
    DATE_MUST_BE_GREATER_THAN_TODAY, NAME_ERROR, BYTES
from holiday.holiday_module.models import Holidays
from holiday.holiday_module.utils import calculate_return_date, calculate_next_working_date
from leaves.models import Leave, LeaveAllocations
from settings.models import CompanySettings, AttendanceSettings
from work_from_home.models import WorkFromHome


def validate_image_extension(data):
    """
        check uploading image extension
    """
    extension_type = ['.jpg', '.jpeg', '.png']
    image_url = data.get('holiday_image')

    if not image_url:
        return True

    extension = os.path.splitext(str(image_url))[1]
    if extension.lower() in extension_type:
        return True


def validate_image_size(data):
    """
        check uploading image size
    """
    image_url = data.get('holiday_image')
    if not image_url:
        context = {
            'status': True,
        }
        return context
    upload_image_size = image_url.size
    image_file_size = CompanySettings.objects.first()
    if image_file_size:
        size = image_file_size.image_size
        type_choice = image_file_size.image_type

        if type_choice == "MB":
            byte_size = size * pow(BYTES, 2)
        elif type_choice == "GB":
            byte_size = size * pow(BYTES, 3)
        elif type_choice == "KB":
            byte_size = size * BYTES

        if upload_image_size <= byte_size:
            context = {
                'status': True,
                'upload_image_size': upload_image_size
            }
            return context
        context = {
            'status': False,
            'size': size,
            'type': type_choice
        }
        return context
    else:
        raise ValidationError({"validation_error": COMPANY_SETTING})


def check_weekday(date):
    """
        check weekend for adding date
    """
    if active_days := AttendanceSettings.objects.values(
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
    ):
        weeks = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4,
                 'saturday': 5, 'sunday': 6}
        off_days = [
            weeks[key]
            for key, value in list(active_days)[0].items()
            if not value
        ]
        if date.weekday() in off_days:
            raise serializers.ValidationError({"date": CHECK_WEEKEND})
    else:
        raise ValidationError({"validation_error": ATTENDANCE_SETTING})


def check_delete_date(date):
    """
        checking date when deleting holiday
    """
    if date <= datetime.date.today():
        raise ValidationError({"validation_error": [HOLIDAY_DELETE_ERROR]})



def date_before_today(data):
    """
        checking date when adding holiday
    """
    if data <= datetime.date.today():
        raise serializers.ValidationError({"validation_error": DATE_MUST_BE_GREATER_THAN_TODAY})


def delete_holiday_increment_duration_wfh(date):
    """function for when we delete holidsettingsay then increment in wfh duration"""
    work_from_home_request = WorkFromHome.objects.filter(start_date__lte=date, end_date__gte=date).exclude(
        status="cancelled")
    for wfh_obj in work_from_home_request:
        if wfh_obj.type == "half":
            wfh_obj.duration = float(wfh_obj.duration) + 0.5

        else:
            wfh_obj.duration = wfh_obj.duration + 1
        wfh_obj.save()
    next_working_date = calculate_next_working_date(date)
    wfh_request_return_dates = WorkFromHome.objects.filter(
        Q(return_date=next_working_date, type="full", duration__gt=1) | Q(return_date=next_working_date, type="half",
                                                                          duration__gte=1) | Q(
            return_date=next_working_date, type="half", duration=0.5, half_day_status="secondhalf") | Q(return_date=next_working_date, type="full", duration=1)).exclude(start_date=next_working_date, end_date=next_working_date).exclude(
        status="cancelled")
    for wfh_obj in wfh_request_return_dates:
        wfh_obj.return_date = date
        wfh_obj.save()


def create_holiday_reduce_duration_wfh(date):
    """function for when we create holiday then decrement in wfh duration"""
    work_from_home_request = WorkFromHome.objects.filter(start_date__lte=date, end_date__gte=date).exclude(
        status="cancelled")
    for wfh_obj in work_from_home_request:
        if wfh_obj.type == "half":
            wfh_obj.duration = float(wfh_obj.duration) - 0.5
        else:
            wfh_obj.duration = wfh_obj.duration - 1
        wfh_obj.save()

    wfh_request_return_dates = WorkFromHome.objects.filter(return_date=date).exclude(
        status="cancelled")
    for wfh_obj in wfh_request_return_dates:
        wfh_obj.return_date = calculate_return_date(date, wfh_obj.return_date, wfh_obj.type, wfh_obj.half_day_status)
        wfh_obj.save()


def update_holiday_update_duration_wfh(old_date, new_date):
    """function for when we update holiday then update duration in wfh"""
    if old_date != new_date:
        delete_holiday_increment_duration_wfh(old_date)
        create_holiday_reduce_duration_wfh(new_date)


def delete_holiday_increment_duration_leave(date):
    """function for when delete holiday then change duration in leave allocation and leave fields"""
    leave_request = Leave.objects.filter(start_date__lte=date, end_date__gte=date).exclude(
        status="cancelled")

    for leave_obj in leave_request:
        user = leave_obj.request_from.id
        leave_allocation = LeaveAllocations.objects.filter(user=user, is_active=True).first()
        if leave_allocation:
            if leave_obj.status == "approved":
                if leave_obj.type == "full":
                    if leave_allocation.exceed_leave == 0:
                        leave_allocation.remaining_leave = leave_allocation.remaining_leave - 1
                        leave_allocation.used_leave = leave_allocation.used_leave + 1
                        leave_obj.duration = leave_obj.duration + 1
                    elif leave_allocation.exceed_leave > 0:
                        leave_allocation.exceed_leave = leave_allocation.exceed_leave + 1
                        leave_allocation.used_leave = leave_allocation.used_leave + 1
                        leave_obj.duration = leave_obj.duration + 1
                else:
                    if leave_allocation.exceed_leave == 0:
                        leave_allocation.remaining_leave = float(leave_allocation.remaining_leave) - 0.5
                        leave_allocation.used_leave = float(leave_allocation.used_leave) + 0.5
                        leave_obj.duration = float(leave_obj.duration) + 0.5
                    elif leave_allocation.exceed_leave > 0:
                        leave_allocation.exceed_leave = float(leave_allocation.exceed_leave) + 0.5
                        leave_allocation.used_leave = float(leave_allocation.used_leave) + 0.5
                        leave_obj.duration = float(leave_obj.duration) + 0.5
            elif leave_obj.status == "pending" or leave_obj.status == "rejected":
                if leave_obj.type == "full":
                    leave_obj.duration = leave_obj.duration + 1
                else:
                    leave_obj.duration = float(leave_obj.duration) + 0.5
            Leave.objects.filter(id=leave_obj.id).update(duration=leave_obj.duration)
            LeaveAllocations.objects.filter(id=leave_allocation.id).update(exceed_leave=leave_allocation.exceed_leave,
                                                                           used_leave=leave_allocation.used_leave,
                                                                           remaining_leave=leave_allocation.remaining_leave)

    next_working_date = calculate_next_working_date(date)
    leave_request_return_dates = Leave.objects.filter(
        Q(return_date=next_working_date, type="full", duration__gt=1) | Q(return_date=next_working_date, type="half",
                                                                          duration__gte=1) | Q(
            return_date=next_working_date, type="half", duration=0.5, half_day_status="secondhalf") | Q(return_date=next_working_date, type="full", duration=1)).exclude(start_date=next_working_date, end_date=next_working_date).exclude(
        status="cancelled")

    for leave_obj in leave_request_return_dates:
        Leave.objects.filter(id=leave_obj.id).update(return_date=date)


def create_holiday_reduce_duration_leave(date):
    """function for when delete holiday then change duration in leave allocation and leave fields"""

    leave_request = Leave.objects.filter(start_date__lte=date, end_date__gte=date).exclude(
        status="cancelled")

    for leave_obj in leave_request:
        user = leave_obj.request_from.id
        leave_allocation = LeaveAllocations.objects.filter(user=user, is_active=True).first()
        if leave_allocation:

            if leave_obj.status == "approved":
                if leave_obj.type == "full":
                    if leave_allocation.exceed_leave == 0:
                        leave_allocation.remaining_leave = leave_allocation.remaining_leave + 1
                        leave_allocation.used_leave = leave_allocation.used_leave - 1
                        leave_obj.duration = leave_obj.duration - 1
                    elif leave_allocation.exceed_leave > 0:
                        leave_allocation.exceed_leave = leave_allocation.exceed_leave - 1
                        leave_allocation.used_leave = leave_allocation.used_leave - 1
                        leave_obj.duration = leave_obj.duration - 1
                else:
                    if leave_allocation.exceed_leave == 0:
                        leave_allocation.remaining_leave = float(leave_allocation.remaining_leave) + 0.5
                        leave_allocation.used_leave = float(leave_allocation.used_leave) - 0.5
                        leave_obj.duration = float(leave_obj.duration) - 0.5
                    elif leave_allocation.exceed_leave > 0:
                        leave_allocation.exceed_leave = float(leave_allocation.exceed_leave) - 0.5
                        leave_allocation.used_leave = float(leave_allocation.used_leave) - 0.5
                        leave_obj.duration = float(leave_obj.duration) - 0.5
            elif leave_obj.status == "pending" or leave_obj.status == "rejected":
                if leave_obj.type == "full":
                    leave_obj.duration = leave_obj.duration - 1
                else:
                    leave_obj.duration = float(leave_obj.duration) - 0.5
            Leave.objects.filter(id=leave_obj.id).update(duration=leave_obj.duration)
            LeaveAllocations.objects.filter(id=leave_allocation.id).update(exceed_leave=leave_allocation.exceed_leave,
                                                                           used_leave=leave_allocation.used_leave,
                                                                           remaining_leave=leave_allocation.remaining_leave)

    leave_request_return_dates = Leave.objects.filter(return_date=date).exclude(
        status="cancelled")
    for leave_obj in leave_request_return_dates:
        leave_obj.return_date = calculate_return_date(date, leave_obj.return_date, leave_obj.type,
                                                      leave_obj.half_day_status)
        Leave.objects.filter(id=leave_obj.id).update(return_date=leave_obj.return_date)


def update_holiday_update_duration_leave(old_date, new_date):
    """update leave duration from holiday"""
    if old_date != new_date:
        delete_holiday_increment_duration_leave(old_date)
        create_holiday_reduce_duration_leave(new_date)


def check_holiday_already_exists_or_not(holiday_name, new_date, holiday_id=None):
    """
        checking duplicate name while adding holiday
    """
    if not (company_settings := CompanySettings.objects.first()):
        raise ValidationError({"validation_error": [COMPANY_SETTING]})
    financial_start_year = company_settings.financial_year_start_date
    financial_end_year = company_settings.financial_year_end_date

    if financial_start_year <= new_date <= financial_end_year:
        if Holidays.objects.filter(name=holiday_name, date__lte=financial_end_year,
                                   date__gte=financial_start_year).exclude(id=holiday_id).first():
            raise ValidationError({"name": NAME_ERROR})
    else:
        next_financial_end_year = financial_end_year + relativedelta(years=1)
        next_financial_start_year = financial_start_year + relativedelta(years=1)
        if next_financial_start_year < new_date <= next_financial_end_year and Holidays.objects.filter(
                name=holiday_name, date__lte=next_financial_end_year, date__gte=next_financial_start_year).exclude(
            id=holiday_id).first():
            raise ValidationError({"name": NAME_ERROR})
