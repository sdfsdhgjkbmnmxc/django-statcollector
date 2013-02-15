# -*- coding:utf-8 -*-
from django.conf import settings


entry_size = 20
max_size_per_param = 300e+6  # 300 Mb
num = max_size_per_param / entry_size
MAX_NUM_ENTRIES = getattr(settings, 'STATCOLLECTOR_MAX_NUM_ENTRIES', num)
MAX_LIFETIME_DAYS = getattr(settings, 'STATCOLLECTOR_MAX_LIFETIME_DAYS', 0)
