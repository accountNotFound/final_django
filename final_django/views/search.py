import json
from datetime import datetime
import requests

from .common import ExceptionWithCode, respons_wrapper, es_domain


@respons_wrapper
def post_abs_queries(request):
  data = json.loads(request.body)
  src_type = data['src_type']
  query_str = data['query_str']
  page_from = data['page_from']
  page_size = data['page_size']
  prefix = data.get('prefix', '')

  res = requests.post(
      url=f'{es_domain}/detail_{src_type}/_search',
      headers={'Content-Type': 'application/json; charset=utf8'},
      data=json.dumps({
          'query': {
              'bool': {
                  'must': [
                      {
                          'query_string': {
                              'default_field': 'text',
                              'query': query_str
                          }
                      },
                      {
                          'prefix': {
                              'id': prefix
                          }
                      }
                  ]
              }
          },
          'size': page_size,
          'from': page_from-1
      }).encode('utf8')
  ).json()
  details = res['hits']['hits']
  total_size = res['hits']['total']['value']
  ids = [d['_id'] for d in details]

  meta_ids = [uid.split('@')[0] for uid in ids]
  res = requests.post(
      url=f'{es_domain}/_mget',
      headers={'Content-Type': 'application/json; charset=utf8'},
      data=json.dumps({
          'docs': [{'_index': f'meta_{src_type}', '_id': meta_id} for meta_id in meta_ids]
      }).encode('utf8')
  ).json()
  metas = res['docs']

  items = [
      {
          'id': uid,
          'title': m['_source']['title'],
          'text': d['_source']['text']
      }
      for uid, m, d in zip(ids, metas, details)]
  print(f'[{datetime.now()}] get_abs_query: {query_str}, from {page_from-1} size {page_size}')
  return {
      'items': items,
      'total_size': total_size
  }


@respons_wrapper
def get_tree_doc(request):
  src_type = request.GET['src_type']
  prefix = request.GET['prefix']

  page_from = 0
  page_size = 50
  data = []
  while True:
    res = requests.post(
        url=f'{es_domain}/detail_{src_type}/_search',
        headers={'Content-Type': 'application/json; charset=utf8'},
        data=json.dumps({
            'query': {
                'bool': {
                    'must': [
                        {
                            'prefix': {
                                'id': prefix
                            }
                        }
                    ]
                }
            },
            'size': page_size,
            'from': page_from
        }).encode('utf8')
    ).json()
    total = res['hits']['total']['value']
    buffer = res['hits']['hits']
    data.extend(buffer)
    if page_from+page_size < total:
      page_from += page_size
    else:
      break
  print(f'[{datetime.now()}] get_tree_doc: {prefix}')
  return [{'id': d['_source']['id'], 'text': d['_source']['text']} for d in data]
