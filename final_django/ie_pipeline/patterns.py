import re

PATTERNS = [
    [
        '\d+[、\s]',
        '\d+(\s*[.．~\-]\s*\d+){1,1}[、\s]',
        '\d+(\s*[.．~\-]\s*\d+){2,2}[、\s]',
        '\d+、\s*',
        '[\(]?\d+[\)]\s*',
    ],
    [
        '附录[a-zA-Z][、\s]',
        '[a-zA-Z](\s*[.．~\-]\s*\d+){1,1}[、\s]',
        '[a-zA-Z](\s*[.．~\-]\s*\d+){2,2}[、\s]',
        '\d+、\s*',
        '\(?\d+\)\s*',
    ],
    [
        '第[一二三四五六七八九十]+章[、\s]',
        '第[一二三四五六七八九十]+条[、\s]',
        '[一二三四五六七八九十]+[、\s]',
        '\d+[、\s]',
        '\d+(\s*[.．~\-]\s*\d+){1,1}[、\s]',
        '\d+(\s*[.．~\-]\s*\d+){2,2}[、\s]',
        '\(?\d+\)\s*',
    ]
]


def get_indent(string) -> int:
  blanks = 0
  i = 0
  while i < len(string):
    if string[i] == ' ':
      blanks += 1
    elif string[i] == '\t':
      blanks += 4
    elif string[i] == '\xa0':
      blanks += 2
    else:
      break
    i += 1
  return i


def parse_string(s: str) -> (str, str):
  for i, patterns in enumerate(PATTERNS):
    for j, p in enumerate(patterns):
      m = re.match(f'^{p}', s)
      if m:
        return (s[0: m.end()].strip(), s[m.end():].strip())
  return ('', s)


def is_sibling(idx1: str, idx2: str) -> bool:
  for patterns in PATTERNS:
    for p in patterns:
      if re.match(p, idx1) and re.match(p, idx2):
        return True
  return False


def is_parent(idx1: str, idx2: str) -> bool:
  idx1 = idx1.strip()+' '
  idx2 = idx2.strip()+' '
  if idx1 == ' ':
    return True
  for patterns in PATTERNS:
    for i, p in enumerate(patterns):
      if re.match(f'^{p}$', idx2):
        for j in range(i):
          if re.match(f'^{patterns[j]}$', idx1):
            return True
  return False
