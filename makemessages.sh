#!/bin/sh
cd statcollector
django-admin.py makemessages --locale ru
mcedit locale/ru/LC_MESSAGES/django.po
django-admin.py compilemessages
