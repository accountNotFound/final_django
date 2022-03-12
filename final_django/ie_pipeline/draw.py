import os
from graphviz import Digraph


def draw_ltptree(title: str, seg: list, pos: list, dep: list):
  graph_path = 'shared_output/tmp/graph'
  if not os.path.exists(graph_path):
    os.makedirs(graph_path)
  g = Digraph(title, directory=graph_path)
  g.node(name='Root')
  word_name = []
  for i in range(len(seg)):
    word_name.append(f'<{i}; {seg[i]}; { pos[i]}>')
    g.node(name=word_name[i], fontname="Fangsong")
  for arc in dep:
    if arc[2] != 'HED':
      g.edge(word_name[arc[0]], word_name[arc[1]], label=arc[2])
    elif arc[1] == -1:
      g.edge(word_name[arc[0]], 'Root', label=arc[2])
  g.view(cleanup=True, quiet_view=True)


def draw_triples(title: str, nodes: list, edges: list):
  graph_path = 'shared_output/tmp/graph'
  if not os.path.exists(graph_path):
    os.makedirs(graph_path)
  g = Digraph(title, directory=graph_path)
  id2name = {}
  for node in nodes:
    g.node(name=node.name, fontname='Fangsong')
    id2name[node.id] = node.name
  for edge in edges:
    g.edge(id2name[edge.start_id], id2name[edge.end_id],
           label=edge.name, fontname='Fangsong')
  g.view(cleanup=True, quiet_view=False)
