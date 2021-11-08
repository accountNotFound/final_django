import json
from datetime import datetime
import requests
import itertools

from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn


@respons_wrapper
def get_top_refs(request):
  k = int(request.GET.get('k', 1))

  with open('assets/name_specif.json', 'r', encoding='utf8') as fin:
    id2names = json.load(fin)
  with open('assets/refs_specif.json', 'r', encoding='utf8') as fin:
    id2refs = json.load(fin)
  id2ref_by = {}
  for from_, tos in id2refs.items():
    for to in tos:
      if to not in id2ref_by:
        id2ref_by[to] = set()
      id2ref_by[to].add(from_)

  top_k_ref_by = list(id2ref_by.items())
  top_k_ref_by.sort(key=lambda it: -len(it[1]))
  top_k_ref_by = top_k_ref_by[0: k]

  nodes = set()
  links = set()
  for to, froms in top_k_ref_by:
    nodes.add(to)
    for ref in id2refs.get(to, []):
      nodes.add(ref)
      links.add((to, ref))
    for from_ in froms:
      nodes.add(from_)
      links.add((from_, to))

  show_nodes = set([it[0] for it in top_k_ref_by])
  nodes = [
      {
          'id': n,
          'name': id2names[n],
          'show': n in show_nodes,
          'type': 'specif'
      } for n in nodes]
  links = [{'source': e[0], 'target': e[1]} for e in links]
  print(f'[{datetime.now()}] get top_refs: {len(nodes)} nodes, {len(links)} links')
  return {
      'nodes': nodes,
      'links': links
  }


@respons_wrapper
def post_graph_queries(request):
  data = json.loads(request.body)
  query_str = data['query_str']

  res = requests.post(
      url=f'{es_domain}/meta_specif/_search',
      headers={'Content-Type': 'application/json; charset=utf8'},
      data=json.dumps({
          'query': {
              'bool': {
                  'must': [
                      {
                          'query_string': {
                              'default_field': 'title',
                              'query': query_str
                          }
                      }
                  ]
              }
          },
          'size': 10,
          'from': 0
      }).encode('utf8')
  ).json()
  nodes = [
      {
          'id': d['_source']['id'],
          'name': d['_source']['title'],
          'type': 'specif',
          'show': False
      } for d in res['hits']['hits']]

  links = set()
  for i in range(len(nodes)):
    for j in range(len(nodes)):
      if i == j:
        continue
      pairs = neo4j_conn.run(
          f'match (a)-[r]->(b) where a.id="{nodes[j]["id"]}" and b.id="{nodes[i]["id"]}" \
          return startNode(r), endNode(r) limit 10'
      )
      for a, b in pairs:
        links.add((a['id'], b['id']))
        nodes[i]['show'] = True

  print(f'[{datetime.now()}] post_graph_queries: {query_str}')
  return {
      'nodes': nodes,
      'links': [{'source': e[0], 'target': e[1]} for e in links]
  }


@respons_wrapper
def post_cypher_queries(request):
  data = json.loads(request.body)
  head = f'name:"{data["head"]}"' if 'head' in data else ''
  tail = f'name:"{data["tail"]}"' if 'tail' in data else ''
  filter_dict = data.get('filterDict', {})

  nodes = set()
  links = set()
  for comb in itertools.product(filter_dict.items()) if filter_dict else [[(0, 0)]]:
    head_type = tail_type = rel_type = ''
    head_id = tail_id = rel_group_id = ''
    for k, v in comb:
      if k == 'head_type':
        head_type = f':{v}'
      elif k == 'tail_type':
        tail_type = f':{v}'
      elif k == 'rel_type':
        rel_type = f':{v}'
      elif k == 'head_id':
        head_id = f',id:{v}'
      elif k == 'tail_id':
        tail_id = f',id:{v}'
      elif k == 'rel_group_id':
        rel_group_id = f'{{group_id:{v}}}'
    cql = f'match \
          ({head_type}{{{head}{head_id}}})\
          -[r{rel_type}{rel_group_id}]->\
          ({tail_type}{{{tail}{tail_id}}}) \
        return startNode(r), endNode(r) limit 100'
    pairs = neo4j_conn.run(cql)
    for a, b in pairs:
      nodes.add(a)
      nodes.add(b)
      links.add((a['id'], b['id']))
  print(f'[{datetime.now()}] post_cypher_queries, count {len(nodes)}')
  return {
      'nodes': [
          {
              'id': n['id'],
              'name': n['name'],
              'type': str(n.labels).strip(':'),
              'show': True
          } for n in nodes],
      'links': [{'source': e[0], 'target': e[1]} for e in links]
  }


@respons_wrapper
def get_center_relations(request):
  node_id = request.GET.get('node_id', '')
  if not node_id:
    return {}
  pairs = neo4j_conn.run(
      f'match (a)-[r]-() where a.id="{node_id}" \
      return startNode(r), endNode(r) limit 10'
  )
  nodes = set()
  links = set()
  for a, b in pairs:
    nodes.add(a)
    nodes.add(b)
    links.add((a['id'], b['id']))
  print(f'[{datetime.now()}] get_center_relations: {node_id}, count {len(nodes)}')
  return {
      'nodes': [
          {
              'id': n['id'],
              'name': n['title'],
              'type': 'specif',
              'show': False
          } for n in nodes],
      'links': [{'source': e[0], 'target': e[1]} for e in links]
  }
