from django.http import JsonResponse
from py2neo import Graph

from manage import PRODUCT_ENV
if PRODUCT_ENV:
  es_domain = 'http://192.168.100.217:9200'
else:
  es_domain = 'http://127.0.0.1:9200'

neo4j_conn = Graph('http://127.0.0.1:7474', auth=('neo4j', 'admin'))


class ExceptionWithCode(Exception):
  def __init__(self, message, code):
    self.message = message
    self.code = code

  def __str__(self):
    return self.message


def respons_wrapper(handler):
  def wrapper(request):
    try:
      res = handler(request)
      return JsonResponse({
          'code': 0,
          'message': '',
          'data': res
      })
    except ExceptionWithCode as e:
      return JsonResponse({
          'code': e.code,
          'message': e.message,
          'data': {}
      })
    except Exception as e:
      return JsonResponse({
          'code': -1,
          'message': str(e),
          'data': {}
      })
  return wrapper
