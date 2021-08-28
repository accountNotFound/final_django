import json
from datetime import datetime

from .common import ExceptionWithCode, respons_wrapper


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
  nodes = [{'id': n, 'name': id2names[n], 'show': n in show_nodes}
           for n in nodes]
  links = [{'source': e[0], 'target': e[1]} for e in links]
  print(f'[{datetime.now()}] get top_refs: {len(nodes)} nodes, {len(links)} links')
  return {
      'nodes': nodes,
      'links': links
  }
