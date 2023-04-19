import django_filters
from django_filters import CharFilter

from holiday.holiday_module.models import Holidays
from settings.models import CompanySettings


class YearFilter(django_filters.FilterSet):
    """year filter data on provided start year and end year. also used for ordering holiday model  """
    start_year = CharFilter(field_name='date', method='filter_startyear')
    end_year = CharFilter(field_name='date', method='filter_endyear')
    ordering = CharFilter(method='filter_ordering')

    def filter_startyear(self, queryset, start_year, value):
        """filter start year according to company settings of start year"""
        company_settings = CompanySettings.objects.first()
        self.queryset = self.queryset.filter(
            date__gte=f'{value}-{company_settings.financial_year_start_date.month}-{company_settings.financial_year_start_date.day}')
        return self.queryset

    def filter_endyear(self, queryset, end_year, value):
        """filter start year according to company settings of end year"""
        company_settings = CompanySettings.objects.first()
        self.queryset = self.queryset.filter(
            date__lte=f'{value}-{company_settings.financial_year_end_date.month}-{company_settings.financial_year_end_date.day}')
        return self.queryset

    def filter_ordering(self, queryset, ordering, value):
        """filter used for ordering the holiday fields"""
        holiday_fields = ['id', 'date', 'name', '-date', '-id', '-name', 'is_active', '-is_active']
        if value in holiday_fields:
            self.queryset = self.queryset.order_by(value)
        return self.queryset

    class Meta:
        model = Holidays
        fields = ['date']
