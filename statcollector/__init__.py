from django.conf import settings


if not'orderable' in settings.INSTALLED_APPS:
    raise Exception("Add 'orderable' to settings.INSTALLED_APPS")
