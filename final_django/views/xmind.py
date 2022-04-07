import json

from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn


def _rel2str(link_name, link_type):
  if link_type == 'attrBy':
    return f'<-[{link_name}:attrBy]-'
  elif link_type == 'predicate':
    return f'-[{link_name}:predicate]->'
  else:
    return f'-[{link_name}]-'


@respons_wrapper
def post_xmind_source_expand(request):
  '''
  prev_path=[
    {
      'node_name': 'xxx',
      'link_type': 'attrBy' or 'predicate' or ''(default)
    }
  ]
  '''
  data = json.loads(request.body)
  prev_path = data['prev_path']
  last_node_name = data['last_node_name']
  query_link_gid = data['query_link_gid']  # ""
  limit_num = data['limit_num']  # 3

  cql_path = ''
  for i, p in enumerate(prev_path):
    node_name = p['node_name']
    link_type = p['link_type']
    cql_path += f'(n{i}{{name:"{node_name}"}})'
    cql_path += _rel2str(f'r{i}', link_type)
  cql_path += f'(nlast{{name:"{last_node_name}"}})-[rtarget]-(ntarget)'

  if not query_link_gid:
    cql_filters = [
        f'rtarget.group_id=r{i}.group_id' for i in range(len(prev_path))]
    cql_filters = f'WHERE {" AND ".join(cql_filters)}' if cql_filters else ''
  else:
    cql_filters = f'WHERE rtarget.group_id="{query_link_gid}"'

  cql =\
      f'MATCH {cql_path} {cql_filters} \
       WITH ntarget, rtarget LIMIT 300 \
       WITH ntarget, {{rdata: rtarget, rtype: type(rtarget)}} AS rel \
       WITH ntarget AS tgt, collect(DISTINCT rel) AS rels, count(rel) AS rcnt\
       ORDER BY rcnt\
       DESC \
       RETURN tgt, rels\
       LIMIT {limit_num}'
  print('xmind source expand:\n', cql)
  res = neo4j_conn.run(cql).data()
  print(res)
  return res


@respons_wrapper
def post_xmind_target_query(request):
  '''
  prev_path=[
    {
      'node_name': 'xxx',
      'link_type': 'attrBy' or 'predicate' or ''(default)
    }
  ]

  last_node_name: default as ''
  query_link_type: default as ''
  query_link_gid: default as ''
  query_node_name: default as ''
  '''
  data = json.loads(request.body)
  prev_path = data['prev_path']
  last_node_name = data['last_node_name']
  query_link_type = data['query_link_type']
  query_link_gid = data['query_link_gid']
  query_node_name = data['query_node_name']
  limit_num = data['limit_num']

  if not query_node_name:
    if not query_link_type:
      raise ExceptionWithCode(
          'query_link_type or query_node_name should be given', -1)
    if not last_node_name:
      raise ExceptionWithCode('root node must be given', -1)
  elif not last_node_name:
    return neo4j_conn.run(
        f'MATCH (target{{name:"{query_node_name}"}}) RETURN NULL AS rel, target AS tgt LIMIT 1').data()

  cql_path = ''
  for i, p in enumerate(prev_path):
    node_name = p['node_name']
    link_type = p['link_type']
    cql_path += f'(n{i}{{name:"{node_name}"}})'
    cql_path += _rel2str(f'r{i}', link_type)
  cql_path += f'(nlast{{name:"{last_node_name}"}})'
  cql_path += _rel2str("rtarget", query_link_type)
  cql_path += f'(ntarget{{name:"{query_node_name}"}})' if query_node_name else '(ntarget)'

  if not query_link_gid:
    cql_filters = [
        f'rtarget.group_id=r{i}.group_id' for i in range(len(prev_path))]
    cql_filters = f'WHERE {" AND ".join(cql_filters)}' if cql_filters else ''
  else:
    cql_filters = f'WHERE rtarget.group_id="{query_link_gid}"'

  cql =\
      f'MATCH {cql_path} {cql_filters} \
       WITH ntarget, rtarget LIMIT 300 \
       WITH ntarget, {{rdata: rtarget, rtype: type(rtarget)}} AS rel\
       WITH ntarget AS tgt, collect(DISTINCT rel) AS rels, count(rel) AS rcnt\
       ORDER BY rcnt\
       DESC \
       RETURN tgt, rels\
       LIMIT 1'
  print('xmind target query:\n', cql)
  return neo4j_conn.run(cql).data()
