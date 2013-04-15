# -*- coding: utf-8 -*-
from django import template

register = template.Library()


class MetricsTableNode(template.Node):
    def __init__(self, metrics, var_name):
        self.metrics = metrics
        self.var_name = var_name

    def __first_or_none(self, data, metric, datetime):
        values = [value for value in data
                  if value['metric'] == metric and value['datetime'] == datetime]
        if len(values) > 0:
            return values[0]['value']
        else:
            return None

    def render(self, context):
        data = [{
            'metric': "{0}".format(metric),
            'datetime': value.datetime.replace(microsecond=0),
            'value': value.value
        } for metric in self.metrics.resolve(context, True)
            for value in metric.get_values()]
        cols = sorted(set([value['datetime'] for value in data]))
        rows = [{
            'title': row,
            'cells': [self.__first_or_none(data, row, col) for col in cols]
        } for row in sorted(set([value['metric'] for value in data]))]
        context[self.var_name] = {
            'cols': cols,
            'rows': rows
        }
        return ''


@register.tag
def metrics_table(parser, token):
    bits = token.split_contents()[1:]
    metrics = parser.compile_filter(bits[0])
    value_name = bits[1]
    return MetricsTableNode(metrics, value_name)