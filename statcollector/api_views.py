# -*- coding:utf-8 -*-
import datetime

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponseNotFound, HttpResponseServerError, \
    HttpResponse

from statcollector.models import Parameter, default_kind, Metric, Source


def description(request, name, kind=None, source=None):
    kw = dict(
        name=name,
        kind=kind or default_kind,
    )
    if request.method == 'POST':
        param = Parameter.get(
            description=request.body.strip().decode('utf-8'),
            **kw
        )
    else:
        try:
            param = Parameter.objects.get(**kw)
        except Parameter.DoesNotExist:
            msg = u'Invalid parameter: {}\n'.format(Parameter(**kw))
            return HttpResponseNotFound(msg)
    return HttpResponse(u'{}\n'.format(param.description))


def data(request, name, kind=None, source=None):
    kw = dict(
        name=name,
        kind=kind or default_kind,
    )

    if request.method == 'POST':
        metric = Metric.get(
            parameter=Parameter.get(**kw),
            source=Source.get(source),
        )
        raw = request.body.strip()
        for i, line in enumerate(raw.split('\n'), start=1):
            try:
                _store_line(metric, line, maybe_with_spaces=(kind == 'string'))
            except ValueError, value:
                msg = u'Invalid {}: {} at line #{}\n'.format(kind, value, i)
                return HttpResponseServerError(msg)
        return HttpResponse('OK')

    try:
        value = Parameter.objects.get(**kw).get_values().latest()
    except Parameter.DoesNotExist:
        msg = u'Invalid parameter: {}\n'.format(Parameter(**kw))
        return HttpResponseNotFound(msg)
    except ObjectDoesNotExist:
        msg = u'No data for {} yet'.format(Parameter(**kw))
        return HttpResponseServerError(msg)
    else:
        return HttpResponse(unicode(value))


def _store_line(metric, line, maybe_with_spaces):
    bits = line.split(None, 2)
    if len(bits) == 1:
        dt = datetime.datetime.now()
        value = line
    else:
        try:
            dt = datetime.datetime.strptime(bits[0], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            if not maybe_with_spaces:
                raise
            dt = datetime.datetime.now()
            value = line
    try:
        value = metric.add_value(dt, value)
    except (ValidationError, ValueError):
        raise ValueError(value)

