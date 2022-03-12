class Trie:
  class _Node:
    def __init__(self, valid=False):
      self.valid = valid
      self.nexts = {}

  @staticmethod
  def _move(node, seq):
    idx = 0
    while idx < len(seq) and seq[idx] in node.nexts:
      node = node.nexts[seq[idx]]
      idx += 1
    return node, idx

  def __init__(self):
    self._root = Trie._Node()
    self._size = 0

  def insert(self, seq):
    node, idx = Trie._move(self._root, seq)
    while idx < len(seq):
      node.nexts[seq[idx]] = Trie._Node()
      node = node.nexts[seq[idx]]
      idx += 1
    node.valid = True
    self._size += 1

  def find_all(self, pref):
    def dfs(node, string):
      if node.valid:
        yield string
      for c, nxt in node.nexts.items():
        yield from dfs(nxt, string+c)

    node, idx = Trie._move(self._root, pref)
    for ret in dfs(node, pref):
      yield ret

  def contain_pref(self, pref):
    node, idx = Trie._move(self._root, pref)
    return idx == len(pref)
