# -*- coding:utf-8 -*-
import datetime

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponseNotFound, HttpResponseServerError, \
    HttpResponse
from django.shortcuts import get_object_or_404

from statcollector.models import Parameter, default_type


def description(request, name, type_=None, source=None):
    if request.method == 'POST':
        param = Parameter.get(
            name=name,
            type_=type_,
            description=request.body.strip(),
        )
    else:
        param = get_object_or_404(Parameter, name=name, type_=type_)
    return HttpResponse(param.description + '\n')


def data(request, name, type_=None, source=None):
    kw = dict(name=name, type_=type_ or default_type)
    if request.method == 'POST':
        param = Parameter.get(**kw)
        raw = request.body.strip()
        for i, line in enumerate(raw.split('\n'), start=1):
            try:
                _store_line(line)
            except ValueError, value:
                msg = 'Invalid {}: {} at line #{}'.format(type_, value, i)
                return HttpResponseServerError(msg)
    else:
        try:
            param = Parameter.objects.get(**kw)
        except Parameter.DoesNotExist:
            name = unicode(Parameter(**kw))
            return HttpResponseNotFound('Unknown param: {}'.format(name))

        try:
            value = param.get_values().latest()
        except ObjectDoesNotExist:
            return HttpResponseServerError('No data for {} yet'.format(param))

    return HttpResponse(str(value.value) + '\n')


def _store_line(param, line, type_):
    bits = line.split()
    if len(bits) == 1:
        dt = datetime.datetime.now()
        value = bits[0]
    else:
        dt = datetime.datetime.strptime()
    try:
        value = param.add_value(dt, value)
    except (ValidationError, ValueError):
        raise ValueError(value)

