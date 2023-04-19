import os
import datetime
import re

import dateutil
import boto3

from holiday.holiday_module.models import Holidays
from holiday.holiday import settings


def get_aws_holiday_image_url(obj, expiration=settings.expiration_time):
    """
        getting holiday image from s3 bucket
    """
    if image_name := obj.holiday_image:
        object_name = str(image_name)
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        return s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': os.environ.get('AWS_STORAGE_BUCKET_NAME'),
                'Key': f'media/{object_name}',
            },
            ExpiresIn=expiration,
        )


def delete_object_from_bucket(instance):
    """
        deleting image from s3 bucket
    """
    image_name = str(instance.holiday_image)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    s3_client.delete_object(
        Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME'),
        Key=f'media/{image_name}',
    )


def attendance_setting_data():
    """
    this function validate attendance setting date according to active days
    """
    active_days = AttendanceSettings.objects.values('monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                                                    'saturday',
                                                    'sunday')
    if not active_days:
        raise ValidationError(ATTENDANCE_SETTING_ERROR)
    weeks = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4,
             'saturday': 5, 'sunday': 6}
    return [weeks[key] for key, value in list(active_days)[0].items() if not value]


def calculate_return_date(date, return_date, type, half_day_status):
    """
    Function to calculate return date from start date and end date
    """
    if type != "half" or half_day_status != "firsthalf":
        off_days = attendance_setting_data()
        while True:
            check_if_holiday = Holidays.objects.filter(is_active=True).values_list('date', flat=True).order_by(
                'date')
            if (return_date.weekday() not in off_days) and (
                    return_date not in check_if_holiday) and date != return_date:
                break
            return_date = return_date + datetime.timedelta(days=1)
    return return_date


def convert_date_format(db_date):
    """
    this function convert date according to company date formate setting
    """
    if db_date is None:
        return None
    try:
        date_format = CompanySettings.objects.first().date_format.date_format
    except AttributeError:
        return db_date
    db_date = dateutil.parser.parse(db_date)
    return db_date.strftime(date_format)


def convert_time_format(db_time):
    """
    this function convert time according to company time formate setting
    """
    if db_time is None:
        return None
    try:
        time_format = CompanySettings.objects.first().time_format.time_format
        time_type = CompanySettings.objects.first().time_type
        if time_type == "12 Hour":
            time_format = time_format.replace("H", "I")
    except AttributeError:
        return db_time
    db_time = dateutil.parser.parse(db_time)
    return db_time.strftime(time_format)


def calculate_next_working_date(date):
    """
        function to calculate next working date
    """
    off_days = attendance_setting_data()
    while True:
        date = date + datetime.timedelta(days=1)
        check_if_holiday = Holidays.objects.filter(is_active=True).values_list('date', flat=True).order_by(
            'date')
        if (date.weekday() not in off_days) and (date not in check_if_holiday):
            break
    return date


def convert_datetime_format(db_datetime):
    """
    this function convert date time according to company date time formate setting
    """

    try:
        if db_datetime:
            db_datetime = dateutil.parser.parse(db_datetime)
            return f"{convert_date_format(db_datetime.strftime('%Y-%m-%d'))} {convert_time_format(db_datetime.strftime('%H:%M:%S'))}"
    except ValueError:
        return db_datetime


def strip_string(data):
    if data:
        string_with_single_spaces = re.sub('\s+', ' ', data).strip()
        return string_with_single_spaces
