import datetime
from decimal import Decimal

from django.utils import simplejson


def more_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime.datetime):
        return {
            '__class__': 'datetime.datetime',
            'year': obj.year,
            'month': obj.month,
            'day': obj.day,
            'hour': obj.hour,
            'minute': obj.minute,
            'second': obj.second,
            }
    if isinstance(obj, datetime.time):
        return {
            '__class__': 'datetime.time',
            'hour': obj.hour,
            'minute': obj.minute,
            'second': obj.second,
            }
    if isinstance(obj, datetime.date):
        return {
            '__class__': 'datetime.date',
            'year': obj.year,
            'month': obj.month,
            'day': obj.day,
            }
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError("%r is not JSON serializable" % (obj,))


def to_json(a):
    return simplejson.dumps(a, default=more_json)
