import json
from pipeline import pipeline, doc2tree
from draw import draw_triples, draw_ltptree

# 先运行ltpServer

if 0:
  # doc = '盖梁施工交底要关注哪些方面'
  # doc = '在什么时候，框架柱轴压比应小于0.6'
  # doc = '框架柱轴压比不应大于多少'
  # doc = '配电柜操作通道宽度应满足什么'
  # doc = '甲类仓库与高层仓库的防火间距不应小于13m'
  doc = '轴压比不大于0.5时，宜比普通混凝土柱大0.2'
  graphs = pipeline(doc)
  print(graphs)
  draw_triples(doc[:10], graphs[0].nodes, graphs[0].edges)

if 1:
  from ltpModel import get_ltp_results
  # sent = '热力除氧器应配备水位自动调节装置'
  # sent = '其边沿与动载之间应留有不小于1m宽的护道'
  # sent = '扣索宜采用钢绞线和带镦头锚的高强钢丝等高强材料'
  # sent = '甲类仓库与高层仓库的防火间距不应小于13m'
  sent = '宜比普通混凝土柱大0.2'
  model = get_ltp_results([sent])[0]
  print(model.dep)
  # model.dep = [(0, 1, 'ATT'), (1, 2, 'ATT'), (2, 1, 'VOB')]
  draw_ltptree(sent, model.seg, model.pos, model.dep)

if 0:
  import re

  tokens = [
      "GB", "JGJ", "CJJ", "CECS", "CCES", "DB", "QB",
      "SL", "YB", "YS", "ST", "HG", "SH", "JC", "DZ",
      "TD", "CH", "JB", "TB", "JT", "LD", "DL", "CJ",
      "JG", "DB"
  ]
  punct = "！？｡＂＃＄％＆＇\(\)＊＋－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃「」〜〝〞〟〰–—‘'‛“”„‟…‧﹏"
  # pattern = f"《(?P<name>[\u4E00-\u9FA5\s{punct}]+)》\s*(?P<type>({'|'.join(tokens)})(/T|_T)?)\s*(?P<version>[\d-/]*)"
  pattern = f"《(?P<name>[0-9\u4E00-\u9FA5\s{punct}]+)》\s*(?P<type>({'|'.join(tokens)})(/T|_T\-T)?)?\s*(?P<version>[\d\-_/]*)?"

  title = '（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）'
  text = open('crawler\jianbiaoku\output\广东高速安全指南依赖\建设工程施工现场消防安全技术规范[附条文说明]GB50720-2011.txt',
              'r', encoding='utf8').read()

  names = set()
  for i, it in enumerate(re.finditer(pattern, text, flags=re.M)):
    name = it.group('name')
    names.add(name.replace(' ', ''))

  for name in names:
    print(name)
  print(len(names))

if 0:
  doc = open(
      'crawler\jianbiaoku\output\广东高速安全指南依赖\施工现场临时用电安全技术规范[附条文说明]JGJ46-2005.txt',
      'r',
      encoding='utf8').read()
  tree = doc2tree(doc)
  with open('tmp/tree.json', 'w', encoding='utf8') as fout:
    json.dump(tree, fout, ensure_ascii=False, indent=2)
