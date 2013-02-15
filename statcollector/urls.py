from django.conf.urls import patterns, include, url

from statcollector import views
from statcollector.models import typecast, Parameter, Source


urlpatterns = patterns(
    '',
    url(
        '^api/'
        '(?:(?P<type_>%s):)?'
        '(?P<name>[^:/ ]{1,%d})'
        '(?:@(?P<source>[^/ ]{1,%d}))?'
        '/' % (
            '|'.join(typecast),
            Source.MAX_NAME_LENGTH,
            Parameter.MAX_NAME_LENGTH,
        ),
        include(patterns(
            '',
            url('^$', views.data),
            url('^description/$', views.description),
        )),
    ),
)
