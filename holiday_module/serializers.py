import calendar
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from holiday.holiday_module.constants import IMAGE_EXTENSION, IMAGE_SIZE
from holiday.holiday_module.models import Holidays
from holiday.holiday_module.utils import get_aws_holiday_image_url, strip_string,convert_date_format, convert_datetime_format
from holiday.holiday_module.validations import (validate_image_size, validate_image_extension, check_weekday,
                                                create_holiday_reduce_duration_wfh, update_holiday_update_duration_wfh,
                                                date_before_today,
                                                create_holiday_reduce_duration_leave,
                                                update_holiday_update_duration_leave,
                                                check_holiday_already_exists_or_not)


class HolidaysListCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to View List of holidays and Add holiday
    """
    holiday_image_data = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()

    class Meta:
        model = Holidays
        fields = ['id', 'name', 'date', 'is_active', 'holiday_image', 'holiday_image_data', 'created_at', 'modified_at',
                  'month', 'deleted_at', 'year', 'count', 'day']
        read_only_fields = ('created_at', 'modified_at', 'deleted_at', 'month', 'year', 'count', 'day')
        write_only_fields = ['holiday_image']

    def to_representation(self, instance):
        """function  to convert date according to company setting"""
        rep = super(HolidaysListCreateSerializer, self).to_representation(instance)
        rep['created_at'] = convert_datetime_format(rep['created_at'])
        rep['modified_at'] = convert_datetime_format(rep['modified_at'])
        rep['deleted_at'] = convert_datetime_format(rep['deleted_at'])
        rep['date'] = convert_date_format(rep['date'])
        return rep

    def validate(self, data):
        """ function to check week day, check holiday already exist or not,
        validate image extension, check file size, create holiday reduce
        duration with work from home and leave
        """
        data['name'] = strip_string(data.get('name'))

        check_weekday(data['date'])

        check_holiday_already_exists_or_not(data['name'], data['date'])

        if not validate_image_extension(data):
            raise ValidationError({"holiday_image": IMAGE_EXTENSION})

        file_size = validate_image_size(data)

        if not file_size['status']:
            raise ValidationError({"holiday_image": f"{IMAGE_SIZE} {file_size['size']}{file_size['type']}!"})
        create_holiday_reduce_duration_wfh(data['date'])
        create_holiday_reduce_duration_leave(data['date'])

        return data

    def get_holiday_image_data(self, obj):
        """used to update holiday image link of aws"""
        return get_aws_holiday_image_url(obj)

    def get_month(self, obj):
        """ get month name"""
        return calendar.month_name[obj.date.month]

    def get_year(self, obj):
        """ get year"""
        return obj.date.year

    def get_day(self, obj):
        """ get year"""
        return obj.date.day

    def get_count(self, obj):
        """return count of holidays in month"""
        return {
            "active": Holidays.objects.filter(date__year=obj.date.year, date__month=obj.date.month,
                                              is_active=True).count(),
            "inactive": Holidays.objects.filter(date__year=obj.date.year, date__month=obj.date.month,
                                                is_active=False).count()
             }


class HolidayPublicSerializer(serializers.ModelSerializer):
    """Serializer for Holiday public api."""

    class Meta:
        model = Holidays
        fields = ['id', 'date']


class HolidaysRetrieveUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve and Update holiday
    """
    holiday_image_data = serializers.SerializerMethodField()

    class Meta:
        model = Holidays
        fields = ['id', 'name', 'date', 'is_active', 'holiday_image', 'holiday_image_data']

    def validate(self, data):
        """ function to check financial year, date before today, check week day, check holiday already exist or not,
            validate image extension, check file size, update holiday update duration with work from home and leave"""
        old_date = self.instance.date
        data['name'] = strip_string(data.get('name'))
        if old_date != data['date']:
            date_before_today(data['date'])
            check_weekday(data['date'])
            check_holiday_already_exists_or_not(data['name'], data['date'], self.instance.id)

        if not validate_image_extension(data):
            raise ValidationError({"holiday_image": IMAGE_EXTENSION})

        file_size = validate_image_size(data)

        if not file_size['status']:
            raise ValidationError({"holiday_image": f"{IMAGE_SIZE} {file_size['size']}{file_size['type']}!"})
        update_holiday_update_duration_wfh(old_date, data['date'])
        update_holiday_update_duration_leave(old_date, data['date'])
        return data

    def get_holiday_image_data(self, obj):
        """used to update holiday image link of aws"""
        return get_aws_holiday_image_url(obj)

    def to_representation(self, instance):
        """function  to convert date according to company setting"""
        rep = super(HolidaysRetrieveUpdateSerializer, self).to_representation(instance)
        rep['date'] = convert_date_format(rep['date'])
        return rep


class HolidaysDestroySerializer(serializers.ModelSerializer):
    """
    Serializer to Delete holiday
    """

    class Meta:
        model = Holidays
        fields = []


class DashboardHolidayListSerializer(serializers.ModelSerializer):
    """
        Serializer to list holiday in dashboard
    """
    holiday_image = serializers.SerializerMethodField()

    class Meta:
        model = Holidays
        fields = ['id', 'name', 'date', 'holiday_image']

    def get_holiday_image(self, obj):
        """used to update holiday image link of aws"""
        return get_aws_holiday_image_url(obj)

    def to_representation(self, instance):
        """function to convert date according to company setting"""
        rep = super(DashboardHolidayListSerializer, self).to_representation(instance)
        rep['date'] = convert_date_format(rep['date'])
        return rep
