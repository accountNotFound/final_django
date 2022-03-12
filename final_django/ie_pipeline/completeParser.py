import re
from typing import Dict, List

from ltpModel import get_ltp_results, LtpModel
from raesParser import RaesParser, TagResult, RaesResult


class CompleteParser:
  DEONTICS = ['应', '宜', '可', '需', '须', '确需',
              '不应', '不宜', '不可', '不需', '不得', '必须', '严禁']
  CO_REF_PATTERNS = []

  def __init__(self, id2seq: Dict[str, str]):
    if not CompleteParser.CO_REF_PATTERNS:
      for d in CompleteParser.DEONTICS:
        CompleteParser.CO_REF_PATTERNS.extend([d, '均'+d, '都'+d])

    self._id2seq = id2seq

  def get_RAES_complete(self) -> Dict[str, List[RaesResult]]:
    res = {}

    def traceback(uid):
      nonlocal res
      for apply_tar, apply_cond, constraint in reversed(res.get(uid, [])):
        if not apply_tar.value and not apply_cond.value:
          sbj = CompleteParser._pick_target(constraint.value)
          if sbj:
            return TagResult('AT', sbj)
        elif apply_tar.value:
          return apply_tar
      path = list(uid.split('-'))
      if len(path) == 1:
        raise Exception('not found apply target')
      return traceback('-'.join(path[0:-1]))

    def foreach(uid, seq):
      nonlocal res
      # for i, substr in enumerate(seq.split('。')):
      #   if not substr:
      #     continue
      for i in range(1):
        substr = seq
        ans = []
        raes_parser = RaesParser(substr)
        for apply_tar, apply_cond, constraint in raes_parser.get_RAES():
          if not constraint.value:
            continue
          if not apply_tar.value and apply_cond.value:
            if CompleteParser._is_coref(constraint.value) or not CompleteParser._pick_target(constraint.value):
              try:
                apply_tar = traceback(uid)
              except Exception:
                pass
          if constraint.value:
            ans.append(RaesResult(apply_tar, apply_cond, constraint))
        res[f'{uid}'] = ans
        # for tar, cond, req in ans:
        #   print(f'{tar.value}-({cond.value})->{req.value}')

    for uid, seq in self._id2seq.items():
      try:
        foreach(uid, seq)
        # print(f'tears size={len(res)}, {seq}', end='\r')
      except Exception as e:
        print(e)
        pass
    return res

  @staticmethod
  def _is_coref(string: str) -> bool:
    if re.match('^(其|该)', string):
      return True
    for p in CompleteParser.CO_REF_PATTERNS:
      if re.match('^'+p, string):
        return True
    return False

  @staticmethod
  def _pick_target(string: str) -> str:
    if not string:
      return ''
    ltp_model = get_ltp_results([string])[0]
    root = ltp_model.get_dep_root()
    if root == None:
      return ''
    spo = ltp_model.get_spo_quadruple(root)
    if spo:
      if ltp_model.pos[spo[2]] != 'n':
        return ''
      atts = ltp_model.get_att_list(spo[2], False)
      return ''.join(ltp_model.seg[i] for i in [*atts, spo[2]])
    else:
      fobs = ltp_model.get_firsts_where(
          root, lambda i: ltp_model.dep[i][2] == 'FOB', 2)
      if len(fobs) != 1:
        return ''
      atts = ltp_model.get_att_list(fobs[0], False)
      return ''.join(ltp_model.seg[i] for i in [*atts, fobs[0]])
