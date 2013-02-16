# -*- coding:utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms import widgets
from django.utils.translation import ugettext_lazy
from orderable.admin import OrderableAdmin
from statcollector.models import Parameter, Metric, Source


class SourceAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        # 'creation_datetime',
        'name',
        'description',
    )
    list_editable = (
        'description',
    )
    list_display_links = (
        'name',
    )
    formfield_overrides = {
        models.TextField: {
            'widget': widgets.Input(attrs={'style': 'width:97.5%'}),
        },
    }


class MetricAdmin(OrderableAdmin):
    change_form_template = 'admin/metric_change_form.html'
    list_display = (
        'sort_order_display',
        'parameter',
        'source',
        'num_entries',
        'last_entry_datetime',
    )
    list_display_links = (
        'parameter',
    )
    list_filter = (
        'source',
    )
    readonly_fields = (
        'num_entries',
        'parameter',
        'source',
    )

    def num_entries(self, obj):
        return obj.get_values().count()

    def last_entry_datetime(self, obj):
        try:
            return obj.get_values().latest().datetime
        except obj.values_class.DoesNotExist:
            return '-'

    last_entry_datetime.short_description = ugettext_lazy('last entry')
    num_entries.short_description = ugettext_lazy('entries number')

    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     extra_context = {
    #
    #     }
    #     return super(MetricAdmin, self).change_view(
    #             request, object_id, form_url, extra_context)

    class Media:
        js = (
            'jquery.min.js',
            'jquery-ui.min.js',
            'flot/jquery.flot.js',
            'flot/jquery.flot.time.js',
        )


class ParameterAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'kind',
        'name',
        'description',
    )
    list_editable = (
        'description',
    )
    list_display_links = (
        'name',
    )
    readonly_fields = (
        'name',
        'kind',
    )
    formfield_overrides = {
        models.TextField: {
            'widget': widgets.Input(attrs={'style': 'width:98.5%'}),
        },
    }


admin.site.register(Source, SourceAdmin)
admin.site.register(Parameter, ParameterAdmin)
admin.site.register(Metric, MetricAdmin)
