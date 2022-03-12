import re
from queue import Queue
from collections import namedtuple
from typing import List

from ltpModel import *
from trie import Trie

TagResult = namedtuple('TagResult', 'tag value')
RaesResult = namedtuple('RaesResult', 'apply_tar, apply_cond, constraint')


class RaesParser:
  STOP_PUNCTS = ['。', '；', '，']
  ACT_PATTERNS: List[str] = []
  TRIE: Trie = None

  def __init__(self, sentence: str):
    if not RaesParser.TRIE:
      RaesParser.TRIE = Trie()
      with open('shared_output/domain_dict.txt', 'r', encoding='utf8') as fin:
        keywords = set(fin.read().split())
        for k in keywords:
          RaesParser.TRIE.insert(k[::-1])
    if not RaesParser.ACT_PATTERNS:
      with open('shared_output/行为.txt', 'r', encoding='utf8') as fin:
        for line in fin.readlines():
          line = line.strip()
          if line:
            RaesParser.ACT_PATTERNS.append(line)

    def dfs(seq, idx):
      if idx == len(RaesParser.STOP_PUNCTS):
        return seq
      return [dfs(p, idx+1) for p in filter(lambda s: s != '', seq.split(RaesParser.STOP_PUNCTS[idx]))]

    self._seq_tree = dfs(sentence, 0)

  def get_RAES(self) -> List[RaesResult]:
    '''
    return a list of triple: (apply_target, apply_condition, constraint)
    '''
    chains_RAE = RaesParser._get_RAE(self._seq_tree)
    res = RaesParser._get_RAES(chains_RAE)
    return res

  @staticmethod
  def _get_RAE(seq_tree: List[List]) -> List[List[TagResult]]:
    que = Queue()
    for el in seq_tree:
      que.put_nowait(el)

    def pop_que():
      res = que.get_nowait()
      if type(res) == list:
        for el in res:
          que.put_nowait(el)
      return res

    res = []
    chain = []

    def update(el):
      nonlocal res, chain
      if chain and chain[-1].tag == 'R' and el.tag != 'R':
        res.append(chain)
        chain = []
      chain.append(el)

    while not que.empty():
      for i in range(que.qsize()):
        cur = pop_que()
        if type(cur) != str:
          if chain:
            res.append(chain)
            chain = []
          continue
        if re.match('^(除.*)$', cur):
          update(TagResult('EC', cur))
        elif re.match('^([当在对].*|.*[时内外])$', cur):
          update(TagResult('AC', cur))
        elif re.match('^并|且', cur):
          try:
            update(TagResult(chain[-1].tag, cur))
          except Exception:
            pass
        elif RaesParser._is_apply_target(cur):
          update(TagResult('AT', cur))
        else:
          update(TagResult('R', cur))
    if chain:
      res.append(chain)
    return res

  @staticmethod
  def _get_RAES(chains_RAE: List[List[TagResult]]) -> List[RaesResult]:

    def split_selections(tagval: TagResult) -> List[TagResult]:
      tag, value = tagval
      ltp_result = get_ltp_results([value])[0]
      root = ltp_result.get_dep_root()
      if root == None:
        return [tagval]
      siblings = ltp_result.get_coo_list(root)
      if len(siblings) == 0:
        return [tagval]
      substrs = []
      substrs.append(
          ''.join(ltp_result.seg[i] for i in ltp_result.get_dep_children(root, True)))
      for sibling in siblings:
        substrs.append(
            ''.join(ltp_result.seg[i] for i in ltp_result.get_dep_children(sibling)))
      return [TagResult(tag+'S', s.strip('和或及、')) for s in substrs]

    res = []
    for chain in chains_RAE:
      apply_targets = [selection for app_tars in filter(lambda it: it.tag == 'AT', chain)
                       for selection in split_selections(app_tars)]
      apply_conditions = [selection for app_conds in filter(lambda it: it.tag in ['AC', 'EC'], chain)
                          for selection in split_selections(app_conds)]
      constraints = [selection for requires in filter(lambda it: it.tag == 'R', chain)
                     for selection in split_selections(requires)]
      for target in apply_targets if apply_targets else [TagResult('AT', '')]:
        for condition in apply_conditions if apply_conditions else [TagResult('AC', '')]:
          for constrain in constraints if constraints else [TagResult('R', '')]:
            res.append(RaesResult(target, condition, constrain))
    return res

  @staticmethod
  def _is_apply_target(string: str) -> bool:
    ltp_result = get_ltp_results([string])[0]
    root = ltp_result.get_dep_root()
    if root == None:
      return False
    if ltp_result.get_spo_quadruple(root):
      return False
    for ptn in RaesParser.ACT_PATTERNS:
      if re.match(ptn, ltp_result.seg[root]):
        return False
    return ltp_result.pos[root] == 'n' or RaesParser.TRIE.contain_pref(ltp_result.seg[root][::-1])
