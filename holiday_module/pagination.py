from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    custom pagination for list API
    """
    page_size_query_param = 'page_size'
