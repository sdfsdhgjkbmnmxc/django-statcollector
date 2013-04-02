from django.conf.urls import patterns, include, url

from statcollector import api_views
from statcollector.models import typecast, Parameter, Source


urlpatterns = patterns(
    '',
    url(
        '^'
        '(?:(?P<kind>%s):)?'
        '(?P<name>[^:/@ ]{1,%d})'
        '(?:@(?P<source>[^/ ]{1,%d}))?'
        '/?' % (
            '|'.join(typecast),
            Parameter.MAX_NAME_LENGTH,
            Source.MAX_NAME_LENGTH,
        ),
        include(patterns(
            '',
            url('^$', api_views.data,
                name='statcollector_api_data'),
            url('^description/$', api_views.description,
                name='statcollector_api_description'),
        )),
    ),
)
