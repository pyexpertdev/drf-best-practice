from datetime import date
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response

from holiday.holiday_module.pagination import CustomPagination
from common.search import get_query
from holiday.holiday_module.constants import HOLIDAYS_CREATED, HOLIDAYS_UPDATED_SUCCESSFULLY, HOLIDAYS_DELETED_SUCCESSFULLY, \
    COMPANY_SETTING, PUBLIC_ACCESS
from holiday.holiday_module.filter import YearFilter
from holiday.holiday_module.models import Holidays
from holiday.holiday_module.serializers import HolidaysListCreateSerializer, HolidaysRetrieveUpdateSerializer, \
    DashboardHolidayListSerializer, HolidayPublicSerializer
from holiday.holiday_module.utils import delete_object_from_bucket
from holiday.holiday_module.validations import delete_holiday_increment_duration_wfh, check_delete_date, \
    delete_holiday_increment_duration_leave
from holiday.holiday_module.permissions import IsAuthorizedForListModel, IsAuthorizedForModel
from settings.models import CompanySettings


class ListCreateAPIView(generics.ListCreateAPIView):
    """
    View to Add holiday and view list of holidays
    """
    serializer_class = HolidaysListCreateSerializer
    queryset = Holidays.objects.all().order_by('-id')
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsAuthorizedForListModel]
    filterset_class = YearFilter

    def get_queryset(self):
        """Method to return queryset according to login user."""
        if self.request.GET.get(PUBLIC_ACCESS) == "true":
            self.pagination_class = None
            return Holidays.objects.filter(is_active=True).values('id', 'date').order_by("-id")
        return Holidays.objects.all().order_by('-id')

    def get_serializer_class(self):
        """Method to return serializer according to login user."""
        if self.request.GET.get(PUBLIC_ACCESS) == "true":
            return HolidayPublicSerializer
        return HolidaysListCreateSerializer

    def post(self, request, *args, **kwargs):
        """post request to create holiday"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by_id=request.user.id)
        return Response({'data': serializer.data, 'message': HOLIDAYS_CREATED},
                        status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        """get request to view list of holiday"""
        start_year = request.GET.get('start_year')
        end_year = request.GET.get('end_year')
        if start_year and end_year:
            self.queryset = self.filter_queryset(self.get_queryset())
        else:
            company_settings = CompanySettings.objects.first()
            if company_settings:
                financial_start_year = company_settings.financial_year_start_date
                financial_end_year = company_settings.financial_year_end_date
                self.queryset = self.get_queryset().filter(date__range=[financial_start_year, financial_end_year])
            else:
                raise ValidationError({"validation_error": [COMPANY_SETTING]})
        search = request.GET.get('search')
        if search:
            entry_query = get_query(search, ['name'])
            self.queryset = self.queryset.filter(entry_query)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            res = self.get_paginated_response(serializer.data)
            return res
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)


class RetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update and delete holiday
    """
    serializer_class = HolidaysRetrieveUpdateSerializer
    queryset = Holidays.objects.all()
    permission_classes = [IsAuthenticated, IsAuthorizedForModel]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        """pu request to update holiday"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        today = timezone.now()
        current_time = today.strftime('%Y-%m-%d %H:%M:%S.%f')
        serializer.save(modified_by_id=request.user.id, modified_at=current_time)
        return Response({'data': serializer.data, 'message': HOLIDAYS_UPDATED_SUCCESSFULLY},
                        status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """delete request to inactivate holiday"""
        instance = self.get_object()
        check_delete_date(instance.date)
        if instance.holiday_image:
            delete_object_from_bucket(instance)
        delete_holiday_increment_duration_wfh(instance.date)
        delete_holiday_increment_duration_leave(instance.date)
        instance.delete()
        return Response({'message': HOLIDAYS_DELETED_SUCCESSFULLY},
                        status=status.HTTP_200_OK)


class DashboardCurrentMonthHolidayListAPIView(generics.ListAPIView):
    """
    View to list current and upcoming holiday.
    """
    serializer_class = DashboardHolidayListSerializer
    permission_classes = [IsAuthenticated, IsAuthorisedForViewDashboard]
    queryset = Holidays.objects.all()

    def get(self, request, *args, **kwargs):
        """get request to view list of current month holiday"""
        self.queryset = self.queryset.filter(date__month=date.today().month, date__year=date.today().year)
        count = self.queryset.count()
        serializer = self.get_serializer(self.queryset, many=True)
        return Response({'count': count, 'data': serializer.data}, status=status.HTTP_200_OK)