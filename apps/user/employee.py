"""
Single place where `user` references the production employee. Accounts are
linked to an EmployeeLocal (UserEmployeeLink), but `user` must not import
`apps.production` directly: both are resolved by reference here.
"""
from django.apps import apps
from django.utils.module_loading import import_string

EMPLOYEE_MODEL = "production.EmployeeLocal"
EMPLOYEE_SERIALIZER = "apps.production.serializers.EmployeeLocalSerializer"


def get_employee_model():
    return apps.get_model(EMPLOYEE_MODEL)


def get_employee_serializer_class():
    return import_string(EMPLOYEE_SERIALIZER)
