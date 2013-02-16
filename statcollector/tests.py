# -*- coding: utf-8 -*-
import unittest
from django.core.urlresolvers import reverse
from django.test.client import Client
from statcollector.api_views import data, description
from statcollector.models import Parameter, Metric, Source


class RawPostClient(Client):
    def rawpost(self, path, content):
        return self.post(path, content, content_type='text/plain')


class TestCase(unittest.TestCase):
    def test_001_api_description(self):
        c = RawPostClient()

        response = c.get(reverse(description, kwargs=dict(name='xx.yy')))
        self.assertEqual(response.status_code, 404)

        response = c.rawpost(
            reverse(description, kwargs=dict(name='xx.yy')),
            'description',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), 'description')

        response = c.rawpost(
            reverse(description, kwargs=dict(name='xx.yy')),
            u'описание',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), 'описание')

        response = c.rawpost(
            reverse(description, kwargs=dict(name='xx.yy')),
            u'описание ',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), 'описание')

        self.assertEqual(Parameter.objects.count(), 1)

        response = c.rawpost(
            reverse(description, kwargs=dict(name='xx.yy', kind='int')),
            u'описание',
        )
        self.assertEqual(Parameter.objects.count(), 1)

        response = c.rawpost(
            reverse(description, kwargs=dict(name='xx.yy', kind='float')),
            u'описание',
        )
        self.assertEqual(Parameter.objects.count(), 2)

        response = c.rawpost(
            reverse(description, kwargs=dict(name='xx.yy', kind='decimal')),
            u'описание',
        )
        self.assertEqual(Parameter.objects.count(), 3)

    def test_002_api_param(self):
        c = RawPostClient()

        # set description x to int:xx
        response = c.rawpost(reverse(description, kwargs=dict(name='xx')), 't')
        self.assertEqual(response.status_code, 200, response.content)

        # get data from int:zz.f (does not exist)
        response = c.get(reverse(data, kwargs=dict(name='zz.f')))
        self.assertEqual(response.status_code, 404, response.content)

        # get description from int:zz.f (does not exist)
        response = c.get(reverse(description, kwargs=dict(name='zz.f')))
        self.assertEqual(response.status_code, 404, response.content)

        # set data to int:zz.f
        response = c.rawpost(reverse(data, kwargs=dict(name='zz.f')), '123')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')

        # get description of int:zz.f (empty desctiption)
        response = c.get(reverse(description, kwargs=dict(name='zz.f')))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), '')

        # set data to int:zz.f
        response = c.rawpost(reverse(data, kwargs=dict(name='zz.f')), '123')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')

        # set data to int:zz.f
        response = c.rawpost(
            reverse(data, kwargs=dict(kind='int', name='zz.f')),
            '1234',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')
        self.assertEqual(
            map(str, Metric.get(Parameter.get('int', 'zz.f')).get_values()),
            ['123', '123', '1234'],
        )

        response = c.rawpost(
            reverse(data, kwargs=dict(kind='float', name='zz.f')),
            '777',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')

        response = c.rawpost(
            reverse(data, kwargs=dict(kind='float', name='zz.f')),
            '1.01',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')
        self.assertEqual(
            map(str, Metric.get(Parameter.get('float', 'zz.f')).get_values()),
            ['777.0', '1.01'],
        )

        response = c.rawpost(
            reverse(data, kwargs=dict(kind='decimal', name='zz.f')),
            '888',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')

        response = c.rawpost(
            reverse(data, kwargs=dict(kind='decimal', name='zz.f')),
            '888.123',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')
        self.assertEqual(
            map(str, Metric.get(Parameter.get('decimal', 'zz.f')).get_values()),
            ['888', '888.123'],
        )

        response = c.rawpost(
            reverse(data, kwargs=dict(kind='string', name='zz.f')),
            'some event',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')
        self.assertEqual(
            map(unicode, Metric.get(Parameter.get('string', 'zz.f')).get_values()),
            ['some event'],
        )

        response = c.rawpost(
            reverse(data, kwargs=dict(kind='string', name='zz.f')),
            u'какое-то событие',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK', response.content)
        metric = Metric.get(Parameter.get('string', 'zz.f')).get_values()
        self.assertEqual(
            map(unicode, metric),
            ['some event', u'какое-то событие'],
        )

    def test_003_source(self):
        c = RawPostClient()

        # set data to int:zz.f@host1
        url = reverse(data, kwargs=dict(name='zz.f', source='host1'))
        response = c.rawpost(url, '42')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.content.strip(), 'OK')

        metric = Metric.get(Parameter.get('int', 'zz.f'), Source.get('host1'))
        self.assertEqual(map(unicode, metric.get_values()), ['42'])