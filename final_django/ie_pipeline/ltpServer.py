from flask import Flask, request
import json
from ltp import LTP

app = Flask(__name__)
model = LTP()
# model.init_dict(path='shared_output/domain_dict.txt')
# print(f'model inited with shared_output/domain_dict.txt')


@app.route('/', methods=['POST'])
def parse():
  data = json.loads(request.data.decode('utf8'))
  seqs = data.get('seqs', [])
  segs, hidden = model.seg(seqs)
  poses = model.pos(hidden)
  deps = model.dep(hidden)
  print(f'parse {len(seqs)} sentences')
  return {
      'segs': segs,
      'poses': poses,
      'deps': deps
  }


if __name__ == '__main__':
  app.run(host='127.0.0.1', port='6789')
