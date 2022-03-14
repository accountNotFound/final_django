import json
from typing import Dict, List, Union, Iterable
from collections import namedtuple
from functools import lru_cache
from hashlib import md5
from docFormat import load, align, parse
from raesParser import RaesParser, TagResult, RaesResult
from completeParser import CompleteParser
from ieStruct import get_triples_by_RAES


class Graph:

  SOURCE = 'specif'

  Node = namedtuple('Node', 'id index name')
  Edge = namedtuple('Edge', 'start_id end_id type name group_id index')

  def __init__(self, uid, triples):
    self.uid = uid
    self.triples = triples
    self.nodes = set()
    self.edges = set()

    @lru_cache(maxsize=64, typed=True)
    def get_node_id(name: str, label: str) -> str:
      return md5((name+label).encode('utf8')).hexdigest().upper()

    def dump_node(rule_id, node_dict):
      name = node_dict.get('name', '').strip()
      attrs = node_dict.get('attrs', [])
      label = node_dict['type'].strip()
      node_id = get_node_id(name, label)
      self.nodes.add(Graph.Node(node_id, label, name))
      # for i, att in enumerate(attrs):
      #   att = att.strip()
      #   att_id = get_node_id(att, 'attribute')
      #   self.nodes.add(Graph.Node(att_id, 'attribute', att))
      #   self.edges.add(
      #       Graph.Edge(node_id, att_id, 'attr_by',
      #                  f'attr*{i}', rule_id, Graph.SOURCE)
      #   )

      # 修复att为链状结构
      pre_id = node_id
      for i in range(len(attrs)-1, -1, -1):
        att_id = get_node_id(attrs[i], 'attribute')
        self.nodes.add(Graph.Node(att_id, 'attribute', attrs[i]))
        self.edges.add(
            Graph.Edge(pre_id, att_id, 'attrBy',
                       'attrBy', rule_id, Graph.SOURCE)
        )
        pre_id = att_id

    def dump_edge(rule_id, triple):
      head_name = triple['head'].get('name', '')
      head_label = triple['head']['type']
      tail_name = triple['tail'].get('name', '')
      tail_label = triple['tail']['type']
      rel_name = '/'.join([*triple['rel'].get('attrs', []),
                           triple['rel'].get('name', '')])
      rel_label = triple['rel']['type']

      # 重命名关系类型，删除joinBy（逆序）
      if '_' in rel_label:
        w1, w2 = rel_label.split('_')
        rel_label = w1+w2[0].upper()+w2[1:]
      if rel_label == 'joinBy':
        head_name, tail_name = tail_name, head_name
        head_label, tail_label = tail_label, head_label

      if get_node_id(head_name, head_label) != get_node_id(tail_name, tail_label):
        self.edges.add(
            Graph.Edge(get_node_id(head_name, head_label), get_node_id(tail_name, tail_label),
                       rel_label, (rel_name if rel_name else rel_label).strip(), rule_id, Graph.SOURCE)
        )

    for triple in triples:
      dump_node(self.uid, triple['head'])
      dump_node(self.uid, triple['tail'])
      dump_edge(self.uid, triple)

  def __repr__(self):
    res = {'nodes': self.nodes, 'edges': self.edges}
    return res.__repr__()

  def __bool__(self):
    return bool(self.nodes)

  def list(self):
    self.nodes = list(self.nodes)
    self.edges = list(self.edges)


def doc2tree(doc: str) -> Dict[str, Dict]:
  seqs = load(doc)
  seqs = align(seqs)
  return {
      'text': '',
      'children': parse(seqs)
  }


def tree2dict(tree: Dict[str, Dict], namespace='.ROOT') -> Dict[str, str]:
  def dfs(node, path):
    yield node['text'], path
    for i, child in enumerate(node['children']):
      yield from dfs(child, f'{path}-{i}')

  return {f'{namespace}@{path}': text for text, path in dfs(tree, '')}


def tree2completes(tree: Dict[str, Dict], namespace='.ROOT') -> Dict[str, List[RaesResult]]:
  id2seq = tree2dict(tree, namespace)
  parser = CompleteParser(id2seq)
  return parser.get_RAES_complete()


def completes2graphs(completes: Dict[str, List[RaesResult]]) -> List[Graph]:
  graphs = []
  for uid, raes_list in completes.items():
    for i, raes in enumerate(raes_list):
      try:
        triples = get_triples_by_RAES(*raes)
        graphs.append(Graph(f'{uid}*{i}', triples))
      except Exception as e:
        # print(raes)
        graphs.append([])
  return list(filter(bool, graphs))


def pipeline(doc: str, namespace='.ROOT') -> Dict[str, Graph]:
  tree = doc2tree(doc)
  completes = tree2completes(tree)
  graphs = completes2graphs(completes)
  return list(filter(bool, graphs))


TEXT_TYPE = None


def get_types(data: Iterable) -> List[str]:
  global TEXT_TYPE
  if TEXT_TYPE == None:
    with open('shared_output/classes.json', 'r', encoding='utf8') as fin:
      TEXT_TYPE = json.load(fin)[0]['topic']['topics']

  res = []

  def dfs(node):
    if 'topics' in node:
      for nxt in node['topics']:
        if dfs(nxt):
          return True
    if node['title'] in data:
      res.append(node['title'])
      return True
    return False
  return res
