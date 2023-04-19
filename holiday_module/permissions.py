from rest_framework.permissions import DjangoModelPermissions, DjangoObjectPermissions

from holiday.holiday_module.constants import PUBLIC_ACCESS

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class IsAuthorizedForModel(DjangoModelPermissions):
    """
        Permission check class for retrieve, update and add methods.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class CheckSamePermissionForPostPut(DjangoModelPermissions):
    """
        Permission check class for check same permission for add, update.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.change_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class IsAuthorizedForListModel(DjangoObjectPermissions):
    """
        Permission for list model.
    """
    def has_permission(self, request, view):
        """
            Override this method to check list permission for log in user.
        """
        if request.method != 'GET':
            return True
        if request.GET.get(PUBLIC_ACCESS) == "true":
            return True
        queryset = self._queryset(view)
        app_label = queryset.model._meta.app_label
        model_name = queryset.model._meta.model_name
        perm = f'list_{model_name}'
        return bool(request.user.has_perm(f"{app_label}.{perm}"))
