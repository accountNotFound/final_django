import json
import re
import patterns as ptn


def load(content: str) -> list:
  res = []
  for line in content.split('\n'):
    clear = line.strip()
    if not clear:
      continue
    if clear.startswith('注：'):
      res.append('注：')
      clear = clear.strip('注：')
    res.append(clear)
  return res


def align(lines: list) -> list:
  '''
  尝试修正成环的编号项，目前只考虑规范，删除前面的无意义作者单位等内容
  '''

  def is_main_index(a):
    return a.isnumeric()

  def is_sub_index(a):
    return re.match('^\d+(\s*[.．~\-]\s*\d+){1,2}$', a) != None

  # 只用来处理二三级数字目录
  def find_range_end(start_idx, begin):
    start_path = list(map(int, re.split('[.．~\-]', start_idx)))
    note_order = 1
    for i in range(begin+1, len(lines)):
      idx, ctx = ptn.parse_string(lines[i])
      if not idx:
        continue
      if is_sub_index(idx):
        path = list(map(int, re.split('[.．~\-]', idx)))
        if len(path) <= len(start_path):
          return i
      elif is_main_index(idx):
        if idx == '1':
          if re.match('^\s*总\s*则\s*$', ctx):
            return i
          note_order = 1
        if re.match('[0-9]+', idx) and int(idx) != note_order:
          return i
        note_order += 1
    return len(lines)

  i = 0
  while i < len(lines):
    print(f'{i}/{len(lines)}', end='\r')
    if lines[i].startswith('6．2．9  抗震设计时'):
      a = 1

    idx, ctx = ptn.parse_string(lines[i])
    if not idx or not is_sub_index(idx):
      i += 1
      continue
    next_i = find_range_end(idx, i)
    while i < next_i:
      idx, ctx = ptn.parse_string(lines[i])
      if idx and is_main_index(idx):
        lines[i] = f'{idx}、 {ctx}'
      i += 1
  return lines


def parse(lines: list) -> list:
  '''
  解析对齐列表为嵌套字典 {text, children}, 目前只考虑规范，删除前面的无意义作者单位等内容
  '''
  i = 0
  # while i < len(lines):
  #   idx, _ = ptn.parse_string(lines[i])
  #   if not idx:
  #     i += 1
  #   else:
  #     break

  def dfs(parent_index) -> list:
    nonlocal i
    res = []
    while i < len(lines):
      if lines[i].startswith('附录B'):
        a = 1
      idx, _ = ptn.parse_string(lines[i])
      if not idx:
        res.append({'text': lines[i], 'children': []})
        i += 1
      elif ptn.is_parent(parent_index, idx):
        res.append({'text': lines[i], 'children': []})
        i += 1
        ans = dfs(idx)
        res[-1]['children'].extend(ans)
      else:
        break
    return res
  return dfs('')
