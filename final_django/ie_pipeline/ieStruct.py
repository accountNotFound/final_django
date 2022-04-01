from ltpModel import LtpModel, get_ltp_results

# get target whether it is an object or a conception
# no necessary to consider COO anymore, since RAES has already parse the COO


def get_targets(ltp_model: LtpModel, idx: int):
  if type(idx) != int:
    return {'name': 'placeholder', 'type': 'object', 'attrs': []}, []
  head = {
      'name': ltp_model.seg[idx],
      'type': 'object',
      'attrs': [ltp_model.seg[i] for i in ltp_model.get_att_list(idx)]
  }
  multis = ltp_model.get_firsts_where(
      idx, lambda i: ltp_model.dep[i][2] == 'COO', 3)
  if multis:
    multis = [
        {
            'name': ltp_model.seg[obj],
            'type': 'object',
            'attrs': [ltp_model.seg[i] for i in ltp_model.get_att_list(obj, False)]
        }
        for obj in [*multis, ltp_model.dep[multis[0]][1]]]
    head['type'] = 'conception'
    head['attrs'] = []
    return head, multis
  else:
    return head, []


def _get_triples_by_model(ltp_model: LtpModel) -> list:
  '''
  extract SPO and FOB structure from root, if exists
  the first element of ret value is the very basic spo triple 
  '''
  root = ltp_model.get_dep_root()
  if len(ltp_model.seg) <= 1 or root == None:
    return None, [], []

  sbj = obj = {
      'type': 'placeholder'
  }
  sbj_multis = obj_multis = []
  # try SPO first, SPO and FOB cannot exist simultaneously
  spo = ltp_model.get_spo_quadruple(root)
  if spo:
    sbj, sbj_multis = get_targets(ltp_model, spo[0])
    obj, obj_multis = get_targets(ltp_model, spo[2])
  else:
    fobs = ltp_model.get_firsts_where(
        root, lambda i: ltp_model.dep[i][2] == 'FOB', 2)
    if len(fobs) == 1:
      obj, obj_multis = get_targets(ltp_model, fobs[0])
    else:
      return None, [], []

  basic_spo = {
      'head': sbj,
      'tail': obj,
      'rel': {
          'name': ltp_model.seg[root],
          'type': 'predicate',
          'attrs': [ltp_model.seg[i] for i in ltp_model.get_att_list(root, False)]
      }
  }
  sbj_joins = []
  for sbj_multi in sbj_multis:
    sbj_joins.append(
        {
            'head': sbj_multi,
            'tail': sbj,
            'rel': {
                'type': 'join_on'
            }
        }
    )
  obj_joins = []
  for obj_multi in obj_multis:
    obj_joins.append(
        {
            'head': obj,
            'tail': obj_multi,
            'rel': {
                'type': 'join_by'
            }
        }
    )
  return basic_spo, sbj_joins, obj_joins


def _get_triples_by_RAES_old(app_tar, app_cond, constraint):
  # handle with target+requirement first, organizing them as connected triples
  constraint_model = get_ltp_results([constraint.value])[0]
  basic_spo, sbj_joins, obj_joins = _get_triples_by_model(constraint_model)
  if basic_spo == None:
    return []
  if app_tar.value:
    app_tar_model = get_ltp_results([app_tar.value])[0]
    head, joins = get_targets(app_tar_model, app_tar_model.get_dep_root())
    basic_spo['head'] = head
    sbj_joins = joins

  if not app_cond.value:
    return [basic_spo, *sbj_joins, *obj_joins]

  # handle with condition/exception, organizing it as other connected triples
  else:
    app_cond_model = get_ltp_results([app_cond.value.strip('当在对时内外')])[0]
    cond_spo, cond_sbj_joins, cond_obj_joins = _get_triples_by_model(
        app_cond_model)

    if cond_spo != None:
      condition_connect = []
      for node in cond_obj_joins if cond_obj_joins else [cond_spo['head']]:
        condition_connect.append({
            'head': basic_spo['head'],
            'tail': node,
            'rel': {
                'type': app_cond.tag
            }
        })
      return [
          basic_spo, *sbj_joins, *obj_joins,
          cond_spo, *cond_sbj_joins, *cond_obj_joins,
          *condition_connect
      ]
    else:
      return [
          basic_spo, *sbj_joins, *obj_joins
      ]


def get_triples_by_RAES(app_tar, app_cond, constraint) -> list:
  res = []
  model = get_ltp_results([constraint.value])[0]
  basic_spo, sbj_joins, obj_joins = _get_triples_by_model(model)
  if basic_spo == None:
    return res

  res.extend([basic_spo, *sbj_joins, *obj_joins])

  if app_tar.value:
    model = get_ltp_results([app_tar.value])[0]
    head, joins = get_targets(model, model.get_dep_root())
    for join in joins:
      res.append(
          {
              'head': join,
              'tail': head,  # @1: head和tail应该换一下位置
              'rel': {
                  'type': 'join_on'
              }
          }
      )
    res.append(
        {
            'head': basic_spo['head'],
            'tail': head,
            'rel': {
                'type': 'apply_target'
            }
        }
    )
  if app_cond.value:
    model = get_ltp_results([app_cond.value.strip('当在对时内外')])[0]
    cond_spo, cond_sbj_joins, cond_obj_joins = _get_triples_by_model(model)
    if cond_spo != None:
      res.extend([cond_spo, *cond_sbj_joins, *cond_obj_joins])
      for node in cond_obj_joins if cond_obj_joins else [cond_spo['head']]:
        res.append({
            'head': basic_spo['head'],
            'tail': node,  # @2: 这里有问题，node 实际上是 SPO triple，需要在后面修正
            'rel': {
                'type': 'apply_condition' if 'AC' in app_cond.tag else 'apply_exception'
            }
        })
    else:
      # 无法解析condition为SPO，视为一个简单target形式的短语
      head, joins = get_targets(model, model.get_dep_root())
      for join in joins:
        res.append(
            {
                'head': join,
                'tail': head,  # @1: head和tail应该换一下位置
                'rel': {
                    'type': 'join_on'
                }
            }
        )
      res.append(
          {
              'head': basic_spo['head'],
              'tail': head,
              'rel': {
                  'type': 'apply_condition'
              }
          }
      )

  def flattern_triples(triples):
    # 修复 @2
    res = []
    for triple in triples:
      head = triple['head']
      if 'rel' in triple['head']:
        res.append(triple['head'])
        head = triple['tail']
      tail = triple['tail']
      if 'rel' in triple['tail']:
        res.append(triple['tail'])
        tail = triple['head']
      res.append({
          'head': head,
          'tail': tail,
          'rel': triple['rel']
      })
    return res

  def reverse_apply_tar(triples):
    # 修复 @1
    apply_tar = None
    for triple in triples:
      if triple['rel']['type'] == 'apply_target':
        apply_tar = triple['tail']
        break
    if apply_tar:
      for triple in triples:
        if triple['rel']['type'] == 'join_on' \
                and triple['tail']['type'] == apply_tar['type'] \
                and triple['tail'].get('name', '1') == apply_tar.get('name', '2'):
          triple['head'], triple['tail'] = triple['tail'], triple['head']
          triple['rel']['type'] = 'join_by'
    return triples

  res = flattern_triples(res)
  res = reverse_apply_tar(res)
  return res
