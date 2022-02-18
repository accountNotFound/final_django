import requests
import json
from .common import ExceptionWithCode, respons_wrapper, es_domain, neo4j_conn

EXAMPLE_DATA = [
    {
        "text": "双车道施工便道宽度宜不小于6.5m；如采用单车道，车道宽度不应小于3.5m,路基宽度不小于4.5m",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "双车道施工便道宽度不宜小于6.5m",
                "source": "公路工程施工安全技术规范 JTGF90-2015",
                "url": "http://www.jianbiaoku.com/webarbs/book/72252/1505250.shtml"
            },
            {
                "text": "单车道施工便道宽度不宜小于4.5m，并宜设置错车道，错车道应设置在视野良好的帝端，间距不宜大于300m",
                "source": "公路工程施工安全技术规范 JTGF90-2015",
                "url": "http://www.jianbiaoku.com/webarbs/book/72252/1505250.shtml"
            }
        ]
    },
    {
        "text": "配电柜正面的操作通道宽度，单列布置或双列背对背布置时不应小于1.5m；双列面对面布置时应不小于2m",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "配电柜正面的操作通道宽度，单列布置或双列背对背布置不小于1.5m，双列面对面布置不小于2m",
                "source": "施工现场临时用电安全技术规范 [附条文说明] JGJ46-2005",
                "url": "http://www.jianbiaoku.com/webarbs/book/194/1012888.shtml"
            }
        ]
    },
    {
        "text": "手提式灭火器宜设置在灭火箱内、挂钩或托架上，其顶部离地面高度不应大于1.5m，底部离地面高度不宜小于0.08m",
        "source": "施工现场临时用电安全技术规范 [附条文说明] JGJ46-2005",
        "traceback": [
            {
                "text": "手提式灭火器宜设置在灭火器箱内或挂钩、托架上",
                "source": "建筑灭火器配置验收及检查规范 [附条文说明] GB50444-2008",
                "url": "http://www.jianbiaoku.com/webarbs/book/12313/694922.shtml"
            },
            {
                "text": "嵌墙式灭火器箱及挂钩、托架的安装高度应满足手提式灭火器顶部离地面距离不大于1.50m，底部离地面距离不小于0.08m",
                "source": "建筑灭火器配置验收及检查规范 [附条文说明] GB50444-2008",
                "url": "http://www.jianbiaoku.com/webarbs/book/12313/694922.shtml"
            }
        ]
    },
    {
        "text": "塔身告于30m的塔机，应在塔顶和臂架端部设置红色警示灯",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "塔身高于30m的塔式起重机，应在塔顶和臂架端部设红色信号灯",
                "source": "施工现场临时用电安全技术规范 [附条文说明] JGJ46-2005",
                "url": "http://www.jianbiaoku.com/webarbs/book/194/1012888.shtml"
            }
        ]
    },
    {
        "text": "电焊机的一次侧电源线长度须不大于5m，二次侧焊接电缆线应采用防水绝缘胶护套铜芯软电缆，长度不宜大于30m",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "交流电焊机一次线长度不得超过5m，应穿管保护",
                "source": "施工现场机械设备检查技术规范 [附条文说明] JGJ160-2016",
                "url": "http://www.jianbiaoku.com/webarbs/book/10446/2830395.shtml"
            },
            {
                "text": "电焊机的二次线应采用防水橡皮护套铜芯软电缆，电缆长度不宜大于30m，一次线长度不宜大于5m",
                "source": "施工现场机械设备检查技术规范 [附条文说明] JGJ160-2016",
                "url": "http://www.jianbiaoku.com/webarbs/book/10446/2830395.shtml"
            }
        ]
    },
    {
        "text": "每道剪刀撑的宽度不应小于4跨，且不应小于6m，斜杆与水平杆夹角宜在45°~60°之间",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "每道剪刀撑宽度不应小于4跨，且不应小于6m，斜杆与地面的倾角应在45°～60°之间",
                "source": "建筑施工扣件式钢管脚手架安全技术规范 [附条文说明] JGJ130-2011",
                "url": "http://www.jianbiaoku.com/webarbs/book/10313/2733463.shtml"
            }
        ]
    },
    {
        "text": "长度小于300m的隧道，起爆站应设在洞口侧面50m以外；其余隧道洞内起爆站距爆破位置不得小于300m",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "长度小于300m的隧道，起爆站应设在洞口侧面50m以外；其余隧道洞内起爆站距爆破位置不得小于300m",
                "source": "公路工程施工安全技术规范 JTGF90-2015",
                "url": "http://www.jianbiaoku.com/webarbs/book/72252/1505250.shtml"
            }
        ]
    },
    {
        "text": "2m以上高处作业时作业人员应正确使用安全带",
        "source": "（粤交基函〔2017〕178号）广东省高速公路工程施工安全标准化指南（第二册安全技术篇）",
        "traceback": [
            {
                "text": "高处作业 ：在坠落高度基准面2m及以上有可能坠落的高处进行的作业",
                "source": "建筑施工高处作业安全技术规范 [附条文说明] JGJ80-2016",
                "url": "http://www.jianbiaoku.com/webarbs/book/10791/2633450.shtml"
            },
            {
                "text": "悬空高处作业人员应挂牢安全带",
                "source": "建筑施工安全技术统一规范[附条文说明]GB 50870-2013",
                "url": "http://www.jianbiaoku.com/webarbs/book/10791/2633450.shtml"
            }
        ]
    }
]

QUERY_INDEX = {}

for i, data in enumerate(EXAMPLE_DATA):
  res = requests.post(
      url=f'{es_domain}/_analyze',
      headers={'Content-Type': 'application/json; charset=utf8'},
      data=json.dumps({
          'analyzer': 'ik_max_word',
          'text': data['text']
      }).encode('utf8')
  ).json()

  for token in res['tokens']:
    token = token['token']
    if token not in QUERY_INDEX:
      QUERY_INDEX[token] = []
    QUERY_INDEX[token].append(i)


@respons_wrapper
def traceback_example(request):
  data = json.loads(request.body)
  src_type = data['src_type']
  query_str = data['query_str']
  page_from = data['page_from']
  page_size = data['page_size']
  tokens = list(query_str.split(' '))
  hits = set()
  for token in tokens:
    indexs = set(QUERY_INDEX.get(token, []))
    if not hits:
      hits = indexs
    elif 'AND' in tokens and indexs:
      hits &= indexs
    else:
      hits |= indexs
  return [EXAMPLE_DATA[hit] for hit in hits]
