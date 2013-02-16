# -*- coding:utf-8 -*-
from django.contrib import admin
from orderable.admin import OrderableAdmin

from statcollector import models


class SourceAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'name',
    )


class MetricAdmin(OrderableAdmin):
    save_on_top = True
    list_display = (
        'parameter',
        'source',
    )


class ParameterAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'type_',
        'name',
        'description',
    )
    list_display_links = (
        'name',
    )


admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.Parameter, ParameterAdmin)
admin.site.register(models.Metric, MetricAdmin)
