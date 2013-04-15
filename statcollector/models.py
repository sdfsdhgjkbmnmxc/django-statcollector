# -*- coding: utf-8 -*-
import decimal, time

from django.db import models
from django.utils.translation import ugettext_lazy
from orderable.models import Orderable
import ujson

from statcollector import conf


default_kind = 'int'


class Source(models.Model):
    MAX_NAME_LENGTH = 512
    name = models.CharField(ugettext_lazy('name'), db_index=True,
                            max_length=MAX_NAME_LENGTH)
    description = models.TextField(ugettext_lazy('description'),
                                   blank=True, default='')
    creation_datetime = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get(cls, name):
        name = (name or '').strip()
        if not name:
            return None
        instance, _created = cls.objects.get_or_create(name=name)
        return instance

    def __unicode__(self):
        if self.description:
            return u'{} ({})'.format(self.name, self.description)
        else:
            return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = ugettext_lazy('data source')
        verbose_name_plural = ugettext_lazy('data sources')


class _Value(models.Model):
    metric = models.ForeignKey('Metric')
    datetime = models.DateTimeField()
    typecast = None

    def __unicode__(self):
        return unicode(self.value)

    def clean(self):
        self.value = self.typecast(self.value)

    class Meta:
        abstract = True
        ordering = ('datetime',)
        get_latest_by = 'datetime'
        verbose_name = ugettext_lazy('value')
        verbose_name_plural = ugettext_lazy('values')


class IntegerValue(_Value):
    typecast = int
    value = models.IntegerField()

    class Meta(_Value.Meta):
        verbose_name = ugettext_lazy('int value')
        verbose_name_plural = ugettext_lazy('int values')


class FloatValue(_Value):
    typecast = float
    value = models.FloatField()

    class Meta(_Value.Meta):
        verbose_name = ugettext_lazy('float value')
        verbose_name_plural = ugettext_lazy('float values')


class DecimalValue(_Value):
    typecast = decimal.Decimal
    value = models.DecimalField(max_digits=15, decimal_places=6)

    class Meta(_Value.Meta):
        verbose_name = ugettext_lazy('decimal value')
        verbose_name_plural = ugettext_lazy('decimal values')


class StringValue(_Value):
    MAX_NAME_LENGTH = 5000

    @classmethod
    def typecast(cls, x):
        return x[:cls.MAX_NAME_LENGTH]

    value = models.CharField(max_length=MAX_NAME_LENGTH)

    class Meta(_Value.Meta):
        verbose_name = ugettext_lazy('string value')
        verbose_name_plural = ugettext_lazy('string values')


typecast = {
    'int': IntegerValue,
    'float': FloatValue,
    'decimal': DecimalValue,
    'string': StringValue,
}


class Parameter(models.Model):
    MAX_NAME_LENGTH = 512
    name = models.CharField(ugettext_lazy('name'), db_index=True,
                            max_length=MAX_NAME_LENGTH)
    kind = models.CharField(ugettext_lazy('type'), max_length=16,
                            choices=[(x, x) for x in typecast])
    description = models.TextField(ugettext_lazy('description'),
                                   blank=True, default='')
    creation_datetime = models.DateTimeField(auto_now_add=True)
    min_value = models.IntegerField(blank=True, null=True)
    max_value = models.IntegerField(blank=True, null=True)
    max_lifetime_days = models.IntegerField(default=conf.MAX_LIFETIME_DAYS)
    max_num_entries = models.BigIntegerField(default=conf.MAX_NUM_ENTRIES)

    def __unicode__(self):
        if self.description:
            return u'{}:{} ({})'.format(self.kind, self.name, self.description)
        else:
            return u'{}:{}'.format(self.kind, self.name)

    @classmethod
    def get(cls, kind, name, description=None):
        if not kind in typecast:
            raise ValueError('Bad kind: {}'.format(kind))
        name = name[:cls.MAX_NAME_LENGTH]
        instance, _created = cls.objects.get_or_create(kind=kind, name=name)
        if description and instance.description != description:
            instance.description = description
            instance.save()
        return instance

    def clean(self):
        self.name = self.name.strip()

    def save(self, *args, **kwargs):
        self.clean()
        super(Parameter, self).save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = ugettext_lazy('parameter')
        verbose_name_plural = ugettext_lazy('parameters')


class Metric(Orderable):
    parameter = models.ForeignKey('Parameter', editable=False)
    source = models.ForeignKey('Source', editable=False, blank=True, null=True)

    @property
    def values_class(self):
        return typecast[self.parameter.kind]

    @classmethod
    def get(cls, parameter, source=None):
        instance, _created = cls.objects.get_or_create(
            parameter=parameter,
            source=source,
        )
        return instance

    def get_values(self):
        return self.values_class.objects.filter(metric=self)

    def export_values(self, mx=1000):
        values = self.get_values().values_list('datetime', 'value')[:mx]
        return [(int(time.mktime(d.timetuple())) * 1000, v) for d, v in values]

    def get_jsoned_values(self, mx=1000):
        exported = self.export_values(mx)
        return ujson.dumps(exported)

    def add_value(self, dt, value):
        value = self.values_class(
            metric=self,
            datetime=dt,
            value=value,
        )
        value.clean()
        value.save()
        return value

    def __unicode__(self):
        if self.source:
            return u'{}@{}'.format(self.parameter.name, self.source.name)
        else:
            return self.parameter.name

    class Meta(Orderable.Meta):
        verbose_name = ugettext_lazy('metric')
        verbose_name_plural = ugettext_lazy('metrics')


report_views = {
    'diagram': (1, ugettext_lazy('diagram')),
    'table': (2, ugettext_lazy('table')),
    'all': (3, ugettext_lazy('diagram and table')),
}


class Report(Orderable):
    MAX_NAME_LENGTH = 512
    name = models.CharField(ugettext_lazy('name'), db_index=True,
                            max_length=MAX_NAME_LENGTH)
    metrics = models.ManyToManyField(Metric)
    view = models.IntegerField(choices=report_views.values())

    @classmethod
    def get(cls, name, metrics, view):
        name = (name or '').strip()
        if not (name and metrics and view):
            return None
        instance, _created = cls.objects.get_or_create(
            name=name, metrics=metrics, view=view)
        return instance

    def __metric_series(self, metric, mx):
        return {
            'data':  metric.export_values(mx),
            'label': '{0}'.format(metric),
        }

    def get_metrics(self):
        return self.metrics.all()

    def export_metrics(self, mx=1000):
        metrics = self.get_metrics()[:mx]
        return [self.__metric_series(m, mx) for m in metrics]

    def get_jsoned_metrics(self, mx=1000):
        exported = self.export_metrics(mx)
        return ujson.dumps(exported)

    def is_diagram(self):
        return self.view & report_views['diagram'][0]

    def is_table(self):
        return self.view & report_views['table'][0]

    class Meta(Orderable.Meta):
        verbose_name = ugettext_lazy('report')
        verbose_name_plural = ugettext_lazy('reports')
