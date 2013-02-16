from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


if not'orderable' in settings.INSTALLED_APPS:
    raise ImproperlyConfigured("Put 'orderable' in settings.INSTALLED_APPS")
