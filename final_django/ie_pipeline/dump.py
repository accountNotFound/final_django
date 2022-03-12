import requests
import os
import json
import pipeline as pp
from hashlib import md5
from datetime import datetime

pp.Graph.SOURCE = 'specif'

# OUTPUT_DIR='shared_output/tmp/ie'
OUTPUT_DIR = 'tmp/small'


# 未完成的
# RANGE = (1341, 1500)
RANGE = ''


if not os.path.exists(OUTPUT_DIR):
  os.makedirs(OUTPUT_DIR)

ES_DETAIL = open(
    f'{OUTPUT_DIR}/es_detail_{RANGE}.json', 'w', encoding='utf8')
ES_META = open(
    f'{OUTPUT_DIR}/es_meta_{RANGE}.json', 'w', encoding='utf8')
NEO_NODES = open(
    f'{OUTPUT_DIR}/neo_nodes_{RANGE}.json', 'w', encoding='utf8')
NEO_EDGES = open(
    f'{OUTPUT_DIR}/neo_edges_{RANGE}.json', 'w', encoding='utf8')

DETAIL_COUNT = 0
NODE_COUNT = 0
EDGE_COUNT = 0

NEO_NODES.write('id:ID,index:LABEL,name:string\n')
NEO_EDGES.write(
    ':START_ID,:END_ID,:TYPE,name:string,group_id:string,index:string\n')


def dump_meta(namespace: str, title: str):
  ES_META.write(json.dumps(
      {
          'index': {
              '_index': f'meta_{pp.Graph.SOURCE}',
              '_id': namespace
          }
      },
  )+'\n')
  ES_META.write(json.dumps(
      {
          'id': namespace,
          'title': title,
          'refs': []
      },
      ensure_ascii=False
  )+'\n')


def dump_detail(namespace: str, doc: str):
  global DETAIL_COUNT, NODE_COUNT, EDGE_COUNT
  count_base = (DETAIL_COUNT, NODE_COUNT, EDGE_COUNT)
  tree = pp.doc2tree(doc)
  id2seq = pp.tree2dict(tree, namespace)
  id2completes = pp.tree2completes(tree, namespace)

  ok_cnt = 1
  tot_cnt = 1
  for i, (uid, text) in enumerate(id2seq.items()):
    print(f'{i}/{len(id2seq)}, success rate={ok_cnt/tot_cnt}', end='\r')
    try:
      nodes = set()
      graphs = pp.completes2graphs({uid: id2completes[uid]})
      for graph in graphs:
        for node in graph.nodes:
          nodes.add(node.name)
      ok_cnt += len(graphs)
      tot_cnt += len(id2completes[uid])

      # raw_types = pp.get_types(text)
      # graph_types = pp.get_types(nodes)

    except Exception as e:
      print(uid, text, e)
    finally:
      ES_DETAIL.write(json.dumps(
          {
              'index': {
                  '_index': f'detail_{pp.Graph.SOURCE}',
                  '_id': uid
              }
          },
          ensure_ascii=False
      )+'\n')
      ES_DETAIL.write(json.dumps(
          {
              'id': uid,
              'text': text,
              # 'raw_types': raw_types if raw_types else [],
              # 'graph_types': graph_types if graph_types else [],
              # 'tears': id2completes.get(uid, []),
              'struct_count': len(id2completes.get(uid, [])),
              'raes_list': id2completes.get(uid, []),
          },
          ensure_ascii=False
      )+'\n')
      for graph in graphs:
        for node in graph.nodes:
          NEO_NODES.write(','.join(node)+'\n')
        for edge in graph.edges:
          NEO_EDGES.write(','.join(edge)+'\n')
        NODE_COUNT += len(graph.nodes)
        EDGE_COUNT += len(graph.edges)
      DETAIL_COUNT += 1

  print(
      f'\ndump {DETAIL_COUNT-count_base[0]} details, {NODE_COUNT-count_base[1]} nodes, {EDGE_COUNT-count_base[2]} edges')
  print(
      f'totally {DETAIL_COUNT} details, {NODE_COUNT} nodes, {EDGE_COUNT} edges')


if 0:
  def get_specif_data():
    with open('已有建筑规范/建标库规范.json', 'r', encoding='utf8') as fin:
      while True:
        line = fin.readline()
        if not line:
          return
        obj = json.loads(line)
        yield obj['标题'], obj['内容']

  begin = datetime.now()
  for i, (title, doc) in enumerate(get_specif_data()):
    if i < RANGE[0]:
      continue
    elif i < RANGE[1]:
      print(f'[{i}] {title}')
      namespace = md5(title.encode('utf8')).hexdigest().upper()
      dump_meta(namespace, title)
      dump_detail(namespace, doc)
    else:
      break
  end = datetime.now()
  print(f'begin at {begin}, time cost {end-begin}')

if 1:
  def get_small_data():
    INPUT_DIR = 'crawler/jianbiaoku/output/广东高速安全指南依赖'
    for f in os.listdir(INPUT_DIR):
      doc = open(f'{INPUT_DIR}/{f}', 'r', encoding='utf8').read()
      yield f.replace('.txt', ''), doc

  begin = datetime.now()
  for i, (title, doc) in enumerate(get_small_data()):
    print(f'[{i}] {title}')
    namespace = md5(title.encode('utf8')).hexdigest().upper()
    dump_meta(namespace, title)
    dump_detail(namespace, doc)
  end = datetime.now()
  print(f'time cost {end-begin}')
