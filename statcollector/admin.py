# -*- coding:utf-8 -*-
from django.contrib import admin
import models


class SrcAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'name',
    )


class ParamAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'type_',
        'name',
        'description',
    )
    list_display_links = (
        'name',
    )


admin.site.register(models.Src, SrcAdmin)
admin.site.register(models.Param, ParamAdmin)
