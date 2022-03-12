import requests
import json
from queue import Queue
from typing import List


class LtpModel:
  def __init__(self, seg, pos, dep):
    self.seg = seg
    self.pos = pos
    self.dep = [(a-1, b-1, r) for (a, b, r) in dep]
    self.froms = {}
    for head, tail, _ in self.dep:
      if tail not in self.froms:
        self.froms[tail] = []
      self.froms[tail].append(head)

  def get_dep_root(self) -> int:
    '''
    return the root index || None
    '''
    roots = self.froms.get(-1, [])
    if len(roots) == 1:
      return roots[0]
    return None

  def get_dep_children(self, target: int, private=False) -> int:
    '''
    return index list of target's children [c1, c2, ..., target]
    if private==True, then only subtree whose rel_name!='COO' will be serialized
    '''
    def dfs(cur, private):
      res = set([cur])
      for from_ in self.froms.get(cur, []):
        if from_ in res:
          continue
        if not private or self.dep[from_][2] != 'COO':
          res |= dfs(from_, False)
      return res

    return list(sorted(dfs(target, private)))

  def get_att_list(self, target: int, contain_target=True) -> List[int]:
    '''
    return index list [adj1, adj2,..., target] || []
    '''
    res = []
    for from_ in self.froms.get(target, []):
      if self.dep[from_][2] in ['ATT', 'ADV']:
        res.extend(self.get_att_list(from_))
    res = sorted(set(res))
    if contain_target and self.dep[target][2] in ['ATT', 'ADV']:
      res.append(target)
    return res

  def get_coo_list(self, target: int) -> List[int]:
    '''
    return index list [coo1, coo2, ...] || []
    '''
    froms = self.froms.get(target, [])
    res = []
    for from_ in froms:
      if self.dep[from_][2] == 'COO':
        res.append(from_)
    return list(sorted(res))

  def get_spo_quadruple(self, target: int) -> (int, int, int, List[int]):
    '''
    return index quadruple : (subject, target as predicate, object, deontic||[]) || None
    '''
    froms = self.froms.get(target, [])
    subject = 'placeholder'
    object_ = 'placeholder'
    deontic = []

    def find(from_, rel_name):
      targets = self.get_firsts_where(
          from_, lambda i: self.dep[i][2] == rel_name)
      if targets:
        if len(targets) == 1:
          return targets[0]
        else:
          raise Exception(f'multi {rel_name}')
      return None

    for from_ in froms:
      if self.dep[from_][2] == 'SBV':
        subject = from_
      elif self.dep[from_][2] in ['VOB', 'FOB']:
        object_ = from_
      elif self.dep[from_][2] in ['ATT', 'ADV']:
        # if subject == None:
        #   subject = find(from_, 'SBV')
        # elif object_ == None:
        #   object_ = find(from_, 'VOB')
        deontic.extend(self.get_att_list(from_))
      if object_ != 'placeholder':
        return (subject, target, object_, deontic)
    return None

  def get_firsts_where(self, target: int, func: callable, max_depth=None) -> List[int]:
    '''
    return a list of index where func(target)==True from target,
    which has the minimum depth in dep tree.
    if max_depth is given and greater than 0, search not more that max_depth layers (target is the first layer)
    return [] if there is not valid result
    '''
    if func(target):
      return [target]
    if not max_depth:
      max_depth = 100  # large enough
    que = Queue()
    que.put_nowait(target)
    vis = set([target])  # there may be circle in dep graph
    while not que.empty() and max_depth > 0:
      res = []
      max_depth -= 1
      for i in range(que.qsize()):
        cur = que.get_nowait()
        if func(cur):
          res.append(cur)
        for from_ in self.froms.get(cur, []):
          if from_ not in vis:
            que.put_nowait(from_)
            vis.add(from_)
        if res:
          return res
    return res


def get_ltp_results(seqs: list) -> List[LtpModel]:
  seqs = list(map(lambda s: s if s else '#', seqs))
  resp = requests.post(
      url='http://127.0.0.1:6789',
      data=json.dumps({
          'seqs': seqs
      }).encode('utf8')
  ).json()
  res = []
  for seg, pos, dep in zip(resp['segs'], resp['poses'], resp['deps']):
    res.append(LtpModel(seg, pos, dep))
  return res
