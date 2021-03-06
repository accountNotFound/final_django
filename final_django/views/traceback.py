import requests
import json
import re
import itertools
from typing import List, Tuple, Dict

from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn
from ..ie_pipeline import pipeline


def _es_query(db_index, method, key, query_str):
  index_from = 0
  page_size = 50
  while True:
    res = requests.post(
        url=f'{es_domain}/{db_index}/_search',
        headers={
            'Content-Type': 'application/json; charset=utf8'
        },
        data=json.dumps({
            'query': {
                'bool': {
                    'must': [
                        {
                            method: {
                                key: query_str
                            }
                        }
                    ]
                }
            },
            'size': page_size,
            'from': index_from
        }, ensure_ascii=False).encode('utf8')
    ).json()

    total = res['hits']['total']['value']
    buffer = res['hits']['hits']

    for el in buffer:
      yield el
    if index_from+page_size < total:
      index_from += page_size
    else:
      return


def _get_raes_list(detail_source) -> List[pipeline.RaesResult]:
  '''only for database'''
  src = detail_source
  if src.get('raes_count', 0) > 0 or src.get('struct_count', 0) > 0:
    res = []
    for triple in src['raes_list']:
      tags = [pipeline.TagResult(*it) for it in triple]
      res.append(pipeline.RaesResult(*tags))
    return res

  # TODO: persist these results
  tree = pipeline.doc2tree(src['text'])
  return pipeline.tree2completes(tree, src['id'])[src['id']+'@-0']


def _get_graph(group_id: str, raes: pipeline.RaesResult) -> pipeline.Graph:
  '''only for database'''
  # records = neo4j_conn.run(
  #     f'MATCH ()-[r]-() \
  #     WHERE r.group_id="{group_id}"\
  #     RETURN a, b, r'
  # )
  # res = pipeline.Graph(group_id, [])
  # for a, b, r in records:
  #   a = pipeline.Graph.Node(a['id'], str(a.labels).strip(':'), a['name'])
  #   b = pipeline.Graph.Node(b['id'], str(b.labels).strip(':'), b['name'])
  #   r = pipeline.Graph.Edge(a['id'], b['id'], list(e[2].types())[0],
  #                           r['name'], r['group_id'], r['specif'])
  #   res.nodes.add(a)
  #   res.nodes.add(b)
  #   res.edges.add(r)
  # if len(res.edges) > 0:
  #   return res

  # TODO: persist these results
  res = pipeline.completes2graphs({group_id: [raes]})
  if len(res) > 0:
    res = res[0]
    res.uid = '*'.join(res.uid.split('*')[:-1])
    return res
  return pipeline.Graph(group_id, [])


def _str(triple):
  a, b, r = triple
  return f'({a.name})-[{r.name.replace("/", "")}]->({b.name})'


def _match_spo(src_triple: tuple, tgt_triple: tuple, tgt_head_joins: List[pipeline.Graph.Node], is_question_key=None) -> (str, str):
  '''triple should be (headNode, tailNode, Edge)'''
  head, tail, edge = src_triple
  a, b, r = tgt_triple

  def is_constant(token):
    return bool(re.match('.*[0-9a-zA-Z].*', token))

  def parse_constant(token):
    m = re.search(
        '.*?(?P<quant>[0-9]+([\.???][0-9]+)?).*?(?P<dim>[a-zA-Z])?.*',
        token
    )
    quant = m.group('quant').replace('???', '.')
    dim = m.group('dim')
    try:
      quant = float(quant)
      if re.match('k[a-zA-Z]+', dim):
        dim = dim[1:]
        quant *= 1000
    except:
      pass
    return quant, dim

  def parse_range(token: str, quant: float):
    not_op = 'not' if '???' in token else ''
    deontic_op = 'should' if '???' in token or '???' in token else 'must'

    low = -1e9
    high = 1e9
    if '???' in token or '>' in token:
      if not_op:
        high = quant
      else:
        low = quant
    elif '???' in token or '<' in token:
      if not_op:
        low = quant
      else:
        high = quant
    return low, high, deontic_op

  if not head.name[-2:] == a.name[-2:]:
    found = False
    for join in tgt_head_joins:
      if head.name[-2:] == join.name[-2:]:
        a = join
        tgt_triple = (a, b, r)
        found = True
        break
    if not found:
      return 'ignore', f'obj dismatch: {_str(src_triple)} && {_str(tgt_triple)}'

  # the qa.py will exceute this condition logic
  if is_question_key != None:
    edge_elements = set((edge.name.replace('/', '')))
    r_elements = set((r.name.replace('/', '')))
    if len(edge_elements & r_elements)/len(edge_elements | r_elements) > 0.5:
      return 'q&a', f'{_str(src_triple)} && {_str(tgt_triple)}'

  if not is_constant(b.name):
    if tail.name[-2:] != b.name[-2:]:
      return 'ignore', f'sbj dismatch: {_str(src_triple)} && {_str(tgt_triple)}'
    else:
      edge_elements = set((edge.name.replace('/', '')))
      r_elements = set((r.name.replace('/', '')))
      if len(edge_elements & r_elements)/len(edge_elements | r_elements) < 0.5:
        status = 'warning' if '???' in r_elements or '???' in r_elements else 'error'
        return status, f'relation dismatch: {_str(src_triple)} && {_str(tgt_triple)}'
      else:
        return 'pass', f'sbj match: {_str(src_triple)} && {_str(tgt_triple)}'
    # return 'ignore', f'unsupport match: {_str(src_triple)} && {_str(tgt_triple)}'

  # ????????????????????????????????????
  tail_quant, tail_dim = parse_constant(tail.name)
  b_quant, b_dim = parse_constant(b.name)
  if tail_dim != b_dim:  # ????????????
    return 'ignore', f'const_dim dismatch: {_str(src_triple)} && {_str(tgt_triple)}'
  if type(tail_quant) != type(b_quant):  # ??????????????????
    return 'ignore', f'const_quant_type dismatch: {_str(src_triple)} && {_str(tgt_triple)}'
  if type(tail_quant) == str and tail_quant != b_quant:  # ??????????????????????????????
    return'error', f'const check failed: {tail.name} and {b.name}'

  # ???????????????????????????
  range_ = parse_range(edge.name, tail_quant)
  tgt_range = parse_range(r.name, b_quant)
  if tgt_range[0] <= range_[0] and range_[1] <= tgt_range[1]:
    return 'pass', f'quant match {_str(src_triple)} && {_str(tgt_triple)}'
  elif tgt_range[2] == 'should':
    return 'warning', \
        f'const check failed (should): {_str(src_triple)} && {_str(tgt_triple)}'
  else:
    return 'error', \
        f'const check failed (must): {_str(src_triple)} && {_str(tgt_triple)}'


def _match_graph(src_graph: pipeline.Graph, tgt_graph: pipeline.Graph, is_question_key=None) -> List[Tuple[str, str]]:
  def id2node(graph):
    return {n.id: n for n in graph.nodes}

  def id2edge(graph):
    return {(e.start_id, e.end_id): e for e in graph.edges}

  def id2joins(graph):
    res = {}
    for e in graph.edges:
      for a, b in [(e.start_id, e.end_id), (e.end_id, e.start_id)]:
        if a not in res:
          res[a] = set([a])
        if e.type == 'joinOn':
          res[a].add(b)
    return res

  src_nodes = id2node(src_graph)
  tgt_nodes = id2node(tgt_graph)
  src_joins = id2joins(src_graph)
  tgt_joins = id2joins(tgt_graph)

  res = []
  vis = set()
  for src_edge, tgt_edge in itertools.product(src_graph.edges, tgt_graph.edges):
    src_head, src_tail = src_nodes[src_edge.start_id], src_nodes[src_edge.end_id]
    tgt_head, tgt_tail = tgt_nodes[tgt_edge.start_id], tgt_nodes[tgt_edge.end_id]
    if src_edge.type == tgt_edge.type == 'predicate':
      for join_id in src_joins.get(src_head.id, []):
        check_res = reason = None
        try:
          check_res, reason = _match_spo(
              (src_nodes[join_id], src_tail, src_edge),
              (tgt_head, tgt_tail, tgt_edge),
              [tgt_nodes[j] for j in tgt_joins.get(tgt_head.id, [])],
              is_question_key
          )
        except Exception as e:
          reason = str(e)
        finally:
          if reason not in vis:
            vis.add(reason)
            res.append({'status': check_res, 'detail': reason})
    else:
      # TODO
      pass
  return res


def _traceback_check(doc, src_type, each_check_num=30, is_question_key=None):
  '''
  @args:
  is_question_key:  None | Callable(str)->bool, it will be used in _match_spo finally. 
                    if this arg is given, then it means a question-str parse and query task need to be solved.
                    this arg will be specified in qa.py 
  '''
  tree = pipeline.doc2tree(doc)
  id2seq = pipeline.tree2dict(tree, '.CHECK')
  id2completes = pipeline.tree2completes(tree, '.CHECK')

  check_on_doc = {}
  for uid, text in id2seq.items():
    if uid.split('@') == '':
      continue

    check_on_text = []
    vis = set()
    specif_iter = _es_query('detail_specif', 'match', 'text', text)
    graphs = pipeline.completes2graphs({'': id2completes[uid]})
    for specif in specif_iter:
      if len(vis) > each_check_num*2:
        break

      check_on_specif = []
      tf_idf = specif['_score']
      specif = specif['_source']
      if specif['text'] in vis:
        continue

      vis.add(specif['text'])
      print(specif['text'])
      specif_raes_list = _get_raes_list(specif)
      specif_graphs = [_get_graph(f'{specif["id"]}*{i}', raes)
                       for i, raes in enumerate(specif_raes_list)]
      specif_graphs = list(filter(bool, specif_graphs))
      for graph, specif_graph in itertools.product(graphs, specif_graphs):
        check_on_graph = _match_graph(graph, specif_graph, is_question_key)
        check_on_graph = list(
            filter(lambda it: it['status'] != 'ignore', check_on_graph))
        check_on_specif.append(check_on_graph)

      meta = next(_es_query('meta_specif', 'term',
                            'id', specif['id'].split('@')[0]))['_source']
      check_on_text.append({
          'checks': check_on_specif,
          'source': {
              'id': specif['id'],
              'text': specif['text'],
              'title': meta['title'],
              'tf_idf': tf_idf,
              'page_rank': meta['page_rank'],
          }
      })

    if len(check_on_text) > 0:
      check_on_doc[uid] = {
          'check_result': list(
              sorted(check_on_text,
                     key=lambda it: -it['source']['tf_idf']*20-it['source']['page_rank'])
          )[:each_check_num],
          'raw_text': text
          # check_on_doc[uid] = check_on_text[:each_check_num]
      }
  return check_on_doc


@respons_wrapper
def post_traceback_check(request):
  data = json.loads(request.body)
  doc = data['doc']
  src_type = data['src_type']
  each_check_num = data.get('each_check_num', 30)
  return _traceback_check(doc, src_type, each_check_num)
