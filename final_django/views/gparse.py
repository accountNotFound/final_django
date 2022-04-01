import json

from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn
from ..ie_pipeline import pipeline


@respons_wrapper
def post_parse(request):
  data = json.loads(request.body)
  seq = data['seq'].split('。')[0]
  graphs = pipeline.pipeline(seq)

  nodes = set()
  links = set()
  for graph in graphs:
    nodes |= graph.nodes
    links |= graph.edges
  print('parse:\n', seq)
  return {
      'nodes': [
          {
              'id': n.id,
              'name': n.name,
              'type': n.index,
              'show': True
          } for n in nodes],
      'links': [
          {
              'source': e.start_id,
              'target': e.end_id,
              'data': {
                  'name': e.name,
                  'group_id': e.group_id,
                  'type': e.type
              },
              'show': True
          } for e in links]
  }
