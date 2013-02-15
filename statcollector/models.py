# -*- coding: utf-8 -*-
import decimal

from django.db import models
from django.utils.translation import ugettext_lazy

from statcollector import conf


default_type = 'int'


class Source(models.Model):
    MAX_NAME_LENGTH = 512
    name = models.CharField(ugettext_lazy('name'), db_index=True,
                            max_length=MAX_NAME_LENGTH)
    creation_datetime = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'@{}'.format(self.name)

    class Meta:
        ordering = ('name',)
        verbose_name = ugettext_lazy('data source')
        verbose_name_plural = ugettext_lazy('data sources')


class _Value(models.Model):
    param = models.ForeignKey('Parameter')
    src = models.ForeignKey('Source', blank=True, null=True)
    datetime = models.DateTimeField()
    typecast = None

    def __unicode__(self):
        return str(self.value)

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
    type_ = models.CharField(ugettext_lazy('type'), max_length=16,
                             choices=[(x, x) for x in typecast])
    description = models.TextField(ugettext_lazy('description'),
                                   blank=True, default='')
    creation_datetime = models.DateTimeField(auto_now_add=True)
    min_value = models.IntegerField(blank=True, null=True)
    max_value = models.IntegerField(blank=True, null=True)
    max_lifetime_days = models.IntegerField(default=conf.MAX_LIFETIME_DAYS)
    max_num_entries = models.BigIntegerField(default=conf.MAX_NUM_ENTRIES)

    def __unicode__(self):
        return u'{}:{}'.format(self.type_, self.name)

    @classmethod
    def get(cls, name, type_=None, description=None):
        if not type_:
            type_ = default_type
        assert type_ in typecast
        name = name[:cls.MAX_NAME_LENGTH]
        instance, _created = cls.objects.get_or_create(type_=type_, name=name)
        if description and instance.description != description:
            instance.description = description
            instance.save()
        return instance

    def get_values(self):
        return typecast[self.type_].objects.filter(data=self)

    def add_value(self, dt, value):
        value = typecast[self.type_](data=self, datetime=dt, value=value)
        value.clean()
        value.save()
        return value

    def clean(self):
        self.name = self.name.strip()

    def save(self, *args, **kwargs):
        self.clean()
        super(Parameter, self).save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = ugettext_lazy('parameter')
        verbose_name_plural = ugettext_lazy('parameters')


