import json
import re
from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn
from ..ie_pipeline import pipeline
from .traceback import _traceback_check


def _is_question_key(name: str):
  for key in '谁 什 么 怎 何 哪 多少 几'.split():
    if key in name:
      return True
  return False


@respons_wrapper
def post_question(request):
  question = json.loads(request.body)['question']
  check_on_doc = _traceback_check(
      question, 'specif', each_check_num=10, is_question_key=_is_question_key)

  status2data = {}
  for uid, data in check_on_doc.items():
    text = data['raw_text']
    results = data.get('check_result', [])
    for res in results:
      for details in res.get('checks', []):
        for detail in details:
          status = detail['status']
          if status != None:
            if status not in status2data:
              status2data[status] = []
            status2data[status].append({
                'raw': text,
                'src': res['source'],
                'detail': detail['detail']
            })
  res = []
  for key in ['q&a', 'pass']:
    for d in status2data.get(key, []):
      detail = d['detail']
      src_triple, tgt_triple = detail.split(' && ')
      answer = tgt_triple.split('->')[-1]
      res.append({
          **d,
          'answer': answer
      })
  return res
