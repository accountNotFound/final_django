import json

from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn


def _neo_query(start_name, rel_type=None, end_name=None, group_ids=None, limit_num=50):
  cql_path = f'(a{{name:"{start_name}"}})'

  if rel_type == 'attr':
    cql_path += '<-[r:attrBy]-'
  elif rel_type == 'predicate':
    cql_path += '-[r:predicate]->'
  else:
    cql_path += '-[r]-'

  if end_name != None:
    cql_path += f'(b{{name:"{end_name}"}})'
  else:
    cql_path += '(b)'

  if group_ids != None:
    if len(group_ids) > 0:
      cql_filters = [f'r.group_id={gid}' for gid in group_ids]
      cql_filters = f'WHERE {" OR ".join(cql_filters)}'
    else:
      raise ExceptionWithCode('group_id empty, should not be happend', -1)
  else:
    cql_filters = ''

  cql = f'MATCH p={cql_path} {cql_filters} RETURN a,b,r LIMIT {limit_num}'
  print(cql)
  paths = neo4j_conn.run(cql).data()
  return [(p['a'], p['b'], p['r']) for p in paths]


def _rel2gid(relationships):
  if relationships == None:
    return None
  return [r['group_id'] for r in relationships]


@respons_wrapper
def post_xmind_source_expand(request):
  data = json.loads(request.body)
  node_name = data['node_name']
  prev_group_ids = _rel2gid(data['prev_relationships'])
  limit_num = data.get('limit_num', 50)
  paths = _neo_query(node_name, group_ids=prev_group_ids, limit_num=limit_num)

  node2rels = {}
  for (a, b, r) in paths:
    if b['name'] not in node2rels:
      node2rels[b['name']] = []
    node2rels[b['name']].append({
        'type': list(r.types())[0],
        **json.loads(json.dumps(r))
    })
  return node2rels


@respons_wrapper
def post_xmind_target_query_v1(request):
  data = json.loads(request.body)
  prev_node_name = data['prev_node_name']
  prev_group_ids = _rel2gid(data['prev_relationships'])
  query_node_name = data['query_node_name']
  query_edge_type = data['query_edge_type']
  limit_num = data.get('limit_num', 50)

  if prev_group_ids == None:
    if query_node_name == None:
      raise ExceptionWithCode('root node must be given', -1)
    cql = f'MATCH (n{{name:"{query_node_name}"}}) RETURN n LIMIT 1'
    res = neo4j_conn.run(cql)
    for n in res:
      return {query_node_name: []}
    return {}

  if query_node_name == query_edge_type == None:
    raise ExceptionWithCode('edge or node should be given', -1)

    # check whether (prev_node)-[edge_type]-(query_node) exists or ot
  paths = _neo_query(prev_node_name, query_edge_type,
                     query_node_name, prev_group_ids, limit_num)

  node2rels = {}
  for path in paths:
    triple = path['segments'][-1]
    rel = triple['relationship']
    end_name = triple['end']['properties']['name']
    if end_name not in node2rels:
      node2rels[end_name] = []
    node2rels[end_name].append(rel)
  return node2rels
