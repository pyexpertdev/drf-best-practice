from django.urls import path
from holiday.holiday_module import views

urlpatterns = [
    path('', views.ListCreateAPIView.as_view(), name='list_create_holidays'),
    path('<int:id>', views.RetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_destroy_holidays'),
    path('dashboard/current_months/holidays', views.DashboardCurrentMonthHolidayListAPIView.as_view(),
         name='current_month_holiday'),
    path('dashboard/upcoming/holidays', views.DashboardUpcomingHolidayListAPIView.as_view(), name='upcoming_holiday'),
]
