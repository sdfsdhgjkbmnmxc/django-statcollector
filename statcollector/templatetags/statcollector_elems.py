# -*- coding: utf-8 -*-
import datetime
from django import template

register = template.Library()


class ReportTableNode(template.Node):
    def __init__(self, row_field, col_field, val_field, metrics, var_name):
        self.row_field = row_field
        self.col_field = col_field
        self.val_field = val_field
        self.metrics = metrics
        self.var_name = var_name

    def __normalize(self, value):
        if isinstance(value, datetime.datetime):
            return value.replace(microsecond=0)
        else:
            return '{0}'.format(value)

    def __get_data(self, context):
        return [{
            self.col_field: self.__normalize(getattr(value, self.col_field)),
            self.row_field: self.__normalize(getattr(value, self.row_field)),
            self.val_field: getattr(value, self.val_field)
        } for metric in self.metrics.resolve(context, True)
            for value in metric.get_values()]

    def __first_or_empty(self, data, row, col):
        values = [value for value in data
                  if value[self.row_field] == row and
                     value[self.col_field] == col]
        if len(values) > 0:
            return values[0]['value']
        else:
            return ''

    def __sorted_and_unique(self, field, data):
        return sorted(set([value[field] for value in data]))

    def _make_table(self, data):
        cols = self.__sorted_and_unique(self.col_field, data)
        rows = [{
            'title': row,
            'cells': [self.__first_or_empty(data, row, col) for col in cols]
        } for row in self.__sorted_and_unique(self.row_field, data)]
        return cols, rows

    def render(self, context):
        data = self.__get_data(context)
        cols, rows = self._make_table(data)
        context[self.var_name] = {
            'cols': cols,
            'rows': rows
        }
        return ''


class ReportTableDefaultNode(ReportTableNode):
    def __init__(self, metrics, var_name):
        super(ReportTableDefaultNode, self).__init__(
            'datetime', 'metric', 'value', metrics, var_name)


class ReportTableByMetricsNode(ReportTableNode):
    def __init__(self, metrics, var_name):
        super(ReportTableByMetricsNode, self).__init__(
            'metric', 'datetime', 'value', metrics, var_name)


def _parse_report_table_token(parser, token):
    bits = token.split_contents()[1:]
    metrics = parser.compile_filter(bits[0])
    value_name = bits[1]
    return metrics, value_name


@register.tag
def report_table_by_metrics(parser, token):
    metrics, value_name = _parse_report_table_token(parser, token)
    return ReportTableByMetricsNode(metrics, value_name)


@register.tag
def report_table(parser, token):
    metrics, value_name = _parse_report_table_token(parser, token)
    return ReportTableDefaultNode(metrics, value_name)