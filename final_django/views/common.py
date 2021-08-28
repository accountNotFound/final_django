from django.http import JsonResponse


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
