const app = document.querySelector('#app')

const model = {
  manifest: null,
  view: 'home',
  selectedCapability: null,
  session: null,
  task: null,
  message: '',
  hint: null,
  errorType: null,
  events: [],
  loading: false,
  sessionToken: null,
}

const esc = (value = '') => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]))

const EVENT_LABELS = {
  session_started: '开始学习',
  task_planned: 'Agent 安排任务',
  answer_submitted: '提交答案',
  error_diagnosed: '定位 Logic Bug',
  hint_given: '给出最小提示',
  main_task_passed: '主任务修正',
  variant_answered: '迁移验证',
  patch_completed: '完成修复',
  learning_state_updated: '更新学习状态',
  next_task_selected: '选择下一任务',
  word_verified: '词根能力验证',
  demo_completed: '学习闭环完成',
}

function saveSessionAuth(id, token) {
  try {
    localStorage.setItem('learning-agent-session', JSON.stringify({id, token}))
  } catch {}
}

function readSessionAuth() {
  try {
    const raw = localStorage.getItem('learning-agent-session')
    if (!raw) return null
    const value = JSON.parse(raw)
    return value?.id && value?.token ? value : null
  } catch {
    return null
  }
}

function clearSessionAuth() {
  try { localStorage.removeItem('learning-agent-session') } catch {}
}

function newRequestId() {
  const token = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
  return `${model.session.session_id}:${token}`
}

function stageLabel() {
  if (!model.session) return '尚未开始'
  return ({TASK:'主任务', RETRY:'逻辑修复', VERIFY:'迁移验证', WORD_TASK:'词根迁移', DONE:'闭环完成'})[model.session.state] || model.session.state
}

function progress() {
  const state = model.session?.state
  if (state === 'TASK' || state === 'RETRY') return 20
  if (state === 'VERIFY') return 35 + (model.session.variant_index || 0) * 15
  if (state === 'WORD_TASK') return 85
  if (state === 'DONE') return 100
  return 0
}

function runtimeNodeStatus(nodeId) {
  if (!model.session) return 'UNKNOWN'
  if (nodeId === 'relative_clause.pointer') return model.session.node_status || 'UNKNOWN'
  if (nodeId === 'word.root.rupt') return model.session.word_status || 'UNKNOWN'
  return 'UNKNOWN'
}

function stateLabel(value) {
  return ({
    UNKNOWN: '未开始', LEARNING: '学习中', WEAK: '薄弱', PATCHING: '修复中',
    VERIFIED: '已验证', REVIEW_DUE: '待复习', LOCKED: '待解锁', preview: '功能预览', locked: '待解锁'
  })[value] || value
}

function statusBadge(status) {
  const label = model.manifest?.status_labels?.[status] || status
  return `<span class="badge badge-${esc(status)}">${esc(label)}</span>`
}

async function api(path, options = {}) {
  let response
  try {
    const authHeaders = model.sessionToken ? {'X-Session-Token': model.sessionToken} : {}
    response = await fetch(path, {
      headers: {'Content-Type':'application/json', ...authHeaders, ...(options.headers || {})},
      ...options,
    })
  } catch (cause) {
    const error = new Error('network_error')
    error.network = true
    error.cause = cause
    throw error
  }
  if (!response.ok) {
    const error = new Error(await response.text())
    error.status = response.status
    throw error
  }
  return response.json()
}

async function loadManifest() {
  try {
    const response = await fetch('/product-manifest.json', {cache:'no-store'})
    if (!response.ok) throw new Error('manifest_load_failed')
    model.manifest = await response.json()
  } catch {
    model.manifest = {version:'3.0', course:{grade:'高一',subject:'英语',book:'必修一',unit:'Unit 4'}, status_labels:{live:'可使用',limited:'部分开放',preview:'功能预览',locked:'待解锁'}, groups:[], assets:[], topology:[]}
  }
}

async function submitCommand(body) {
  const options = {method:'POST', body:JSON.stringify(body)}
  try {
    return await api('/api/v1/learning/step', options)
  } catch (error) {
    if (error.network) return api('/api/v1/learning/step', options)
    throw error
  }
}

function applyResult(data) {
  if (data.session_token) model.sessionToken = data.session_token
  model.session = data.session
  model.task = data.current_task || null
  model.message = data.message || ''
  model.hint = data.hint || null
  model.errorType = data.error_type || null
  saveSessionAuth(data.session.session_id, model.sessionToken)
}

async function refreshSnapshot() {
  if (!model.session) return
  const snapshot = await api(`/api/v1/session/${model.session.session_id}`)
  model.session = snapshot.session
  model.task = snapshot.current_task
  model.events = snapshot.events || []
}

async function startLearning() {
  model.loading = true
  model.view = 'learn'
  render()
  try {
    applyResult(await api('/api/v1/session/start', {method:'POST'}))
    await refreshSnapshot()
  } catch (error) {
    model.message = `启动失败：${error.message}`
  } finally {
    model.loading = false
    render()
  }
}

async function ensureLearning() {
  if (!model.session) return startLearning()
  model.view = 'learn'
  render()
}

async function restore() {
  const auth = readSessionAuth()
  if (!auth) return
  model.sessionToken = auth.token
  try {
    const data = await api(`/api/v1/session/${auth.id}`)
    model.session = data.session
    model.task = data.current_task
    model.events = data.events || []
    model.message = data.session.state === 'DONE' ? '上次学习闭环已完成。' : '已恢复上次学习现场。'
  } catch {
    clearSessionAuth()
    model.sessionToken = null
  }
}

async function answer(choice) {
  if (!model.session || !model.task || model.loading) return
  model.loading = true
  render()
  try {
    let event = 'ANSWER_SUBMITTED'
    const payload = {answer: choice}
    if (model.session.state === 'VERIFY') {
      event = 'VERIFY_ANSWER'
      payload.variant_id = model.task.id
    } else if (model.session.state === 'WORD_TASK') {
      event = 'WORD_ANSWER'
    }

    const command = {
      session_id: model.session.session_id,
      event,
      event_id: newRequestId(),
      expected_version: model.session.version,
      payload,
    }
    applyResult(await submitCommand(command))
    await refreshSnapshot()
  } catch (error) {
    if (error.status === 409) {
      try {
        await refreshSnapshot()
        model.message = '学习状态已更新，请按当前任务继续。'
      } catch {
        model.message = `状态恢复失败：${error.message}`
      }
    } else {
      model.message = `请求失败：${error.message}`
    }
  } finally {
    model.loading = false
    render()
  }
}

function resetLearning() {
  clearSessionAuth()
  Object.assign(model, {session:null, task:null, message:'', hint:null, errorType:null, events:[], loading:false, sessionToken:null, view:'home'})
  render()
}

function findCapability(id) {
  for (const group of model.manifest?.groups || []) {
    const item = group.capabilities.find(capability => capability.id === id)
    if (item) return {...item, groupName:group.name}
  }
  return (model.manifest?.assets || []).find(item => item.id === id) || null
}

function openCapability(id) {
  const capability = findCapability(id)
  if (!capability) return
  if (capability.action === 'gold_loop') return ensureLearning()
  if (capability.action === 'repair') {
    model.view = 'repair'
    return render()
  }
  if (capability.action === 'assets') {
    model.view = 'assets'
    return render()
  }
  model.selectedCapability = capability
  model.view = 'preview'
  render()
}

function courseLine() {
  const course = model.manifest?.course || {}
  return [course.grade, course.subject, course.book, course.unit].filter(Boolean).join(' · ')
}

function header() {
  return `<header class="topbar">
    <button class="brand" data-nav="home"><span class="brand-mark">∴</span><span><b>文科实验室</b><small>LEARNING AGENT</small></span></button>
    <div class="top-actions">
      <span class="course-chip">${esc(model.manifest?.course?.unit || 'Unit 4')}</span>
      <button class="profile-button" data-nav="profile">我的</button>
    </div>
  </header>`
}

function bottomNav() {
  const items = [
    ['home','首页','⌂'], ['today','今日','◉'], ['lab','实验室','◇'],
    ['repair','修复','⊕'], ['topology','拓扑','⌘'], ['assets','资产','▦'],
  ]
  return `<nav class="bottom-nav">${items.map(([id,label,icon]) => `<button data-nav="${id}" class="${model.view===id?'active':''}"><span>${icon}</span><small>${label}</small></button>`).join('')}</nav>`
}

function shell(content) {
  return `<main class="product-shell">${header()}<div class="page">${content}</div>${bottomNav()}</main>`
}

function homePage() {
  const pointer = runtimeNodeStatus('relative_clause.pointer')
  const rupt = runtimeNodeStatus('word.root.rupt')
  const currentState = model.session ? stageLabel() : '尚未开始'
  const latestError = [...model.events].reverse().find(event => event.event_type === 'error_diagnosed')
  const verified = [pointer, rupt].filter(value => value === 'VERIFIED').length
  return shell(`
    <section class="welcome">
      <div><p class="eyebrow">AI 学习调试系统</p><h1>把文科学成一套<br>可以调试的逻辑系统</h1><p>${esc(courseLine())}</p></div>
      <div class="system-orbit"><span>观察</span><span>诊断</span><span>修复</span><span>验证</span></div>
    </section>

    <section class="hero-task">
      <div class="hero-task-copy">
        <div class="section-kicker">今日优先任务</div>
        <h2>${model.session?.state === 'DONE' ? '本轮修复已完成' : '定语从句 · which 指向关系'}</h2>
        <p>${model.session?.state === 'DONE' ? '查看本轮修复证据和知识拓扑变化。' : 'Learning Agent 先处理当前可验证的薄弱节点，再进入词根逻辑能力。'}</p>
        <div class="task-facts"><span>当前：${esc(currentState)}</span><span>pointer：${esc(stateLabel(pointer))}</span><span>rupt：${esc(stateLabel(rupt))}</span></div>
      </div>
      <button class="primary" data-action="learn">${model.session?.state === 'DONE' ? '查看学习结果' : model.session ? '继续学习' : '开始今日学习'}</button>
    </section>

    <section class="stats-grid">
      <article><small>真实知识节点</small><strong>2</strong><span>当前 MVP 内容</span></article>
      <article><small>已验证组件</small><strong>${verified}</strong><span>来自真实迁移证据</span></article>
      <article><small>Learning Events</small><strong>${model.events.length}</strong><span>事实层记录</span></article>
      <article><small>最近 Logic Bug</small><strong class="small-strong">${latestError ? 'POINTER_ERROR' : '暂无'}</strong><span>${latestError ? '可进入错误档案' : '完成任务后生成'}</span></article>
    </section>

    <div class="section-head"><div><p class="section-kicker">学习实验室</p><h2>完整能力框架</h2></div><button data-nav="lab" class="text-button">查看全部 →</button></div>
    <section class="home-labs">
      ${(model.manifest?.groups || []).map(group => `<article class="group-preview"><div class="group-icon">${group.id==='decode'?'⌘':group.id==='causal'?'⇢':'⊕'}</div><div><h3>${esc(group.name)}</h3><p>${esc(group.description)}</p><div class="mini-statuses">${group.capabilities.map(item => statusBadge(item.status)).join('')}</div></div></article>`).join('')}
    </section>

    <section class="split-panels">
      <button class="panel-card" data-nav="topology"><span class="panel-icon">⌘</span><div><small>知识拓扑</small><h3>${esc(stateLabel(pointer))} · relative_clause.pointer</h3><p>查看 Unit 4 的能力地图、前置节点与待解锁方向。</p></div><b>→</b></button>
      <button class="panel-card" data-nav="assets"><span class="panel-icon">▦</span><div><small>学习资产</small><h3>${model.events.length ? `${model.events.length} 条真实学习证据` : '等待第一次学习记录'}</h3><p>错误档案、修复日志、学习记录和逻辑组件库。</p></div><b>→</b></button>
    </section>
  `)
}

function todayPage() {
  return shell(`
    <div class="page-title"><p class="section-kicker">TODAY</p><h1>今日学习</h1><p>Agent 只根据真实状态安排当前 MVP 中存在的任务。</p></div>
    <section class="timeline-card current">
      <span class="timeline-dot"></span>
      <div><small>01 · 当前优先级</small><h2>修复 which 指向关系</h2><p>目标节点：<code>relative_clause.pointer</code> · 状态：${esc(stateLabel(runtimeNodeStatus('relative_clause.pointer')))}</p></div>
      <button class="primary compact" data-action="learn">${model.session ? '继续' : '开始'}</button>
    </section>
    <section class="timeline-card ${runtimeNodeStatus('relative_clause.pointer')==='VERIFIED'?'current':'muted'}">
      <span class="timeline-dot"></span><div><small>02 · 下一能力</small><h2>词根逻辑拆解 · rupt</h2><p>当前内容通过 Gold Loop 在 pointer 修复后解锁。</p></div>${statusBadge('limited')}
    </section>
    <section class="timeline-card muted"><span class="timeline-dot"></span><div><small>03 · 后续内容</small><h2>定语从句约束 / 文章结构 / 因果链</h2><p>产品框架已存在，当前内容包尚未开放。</p></div>${statusBadge('locked')}</section>
    <div class="info-note"><b>推荐规则</b><span>阻断错误 ＞ 重复错误 ＞ 脆弱节点 ＞ 到期复习 ＞ 新知识。当前版本只对已有真实节点执行调度。</span></div>
  `)
}

function capabilityCard(item) {
  return `<button class="capability-card" data-capability="${esc(item.id)}">
    <div class="cap-icon">${esc(item.icon || '◇')}</div>
    <div class="cap-copy"><div class="cap-title"><h3>${esc(item.name)}</h3>${statusBadge(item.status)}</div><p>${esc(item.description)}</p>${item.node?`<code>${esc(item.node)}</code>`:''}</div>
    <span class="chevron">→</span>
  </button>`
}

function labPage() {
  return shell(`
    <div class="page-title"><p class="section-kicker">LAB</p><h1>学习实验室</h1><p>完整能力地图全部保留；只有 LIVE / LIMITED 且有真实内容的入口会改变学习状态。</p></div>
    ${(model.manifest?.groups || []).map(group => `<section class="lab-group"><div class="section-head"><div><h2>${esc(group.name)}</h2><p>${esc(group.description)}</p></div></div><div class="cap-list">${group.capabilities.map(capabilityCard).join('')}</div></section>`).join('')}
  `)
}

function repairPage() {
  const errors = model.events.filter(event => event.event_type === 'error_diagnosed')
  const hints = model.events.filter(event => event.event_type === 'hint_given')
  const patched = model.events.some(event => event.event_type === 'patch_completed')
  return shell(`
    <div class="page-title"><p class="section-kicker">DEBUG</p><h1>逻辑修复中心</h1><p>错误不是一张错题截图，而是一条可以追踪和验证的 Logic Bug。</p></div>
    <section class="bug-card ${errors.length?'has-bug':''}">
      <div class="bug-code">${errors.length ? 'POINTER_ERROR' : 'NO BUG YET'}</div>
      <div><small>当前真实错误模型</small><h2>${errors.length ? 'which 指向关系错误' : '还没有真实错误记录'}</h2><p>${errors.length ? `已触发 ${hints.length} 次提示；修复状态：${patched?'VERIFIED':'处理中'}` : '完成当前长难句任务后，这里会出现真实诊断。'}</p></div>
      <button class="secondary" data-action="learn">${errors.length?'回到修复现场':'进入当前任务'}</button>
    </section>
    <div class="section-head"><div><p class="section-kicker">ERROR MODEL</p><h2>完整错误分类</h2></div></div>
    <section class="error-model-grid">
      ${['POINTER_ERROR','CONSTRAINT_OMISSION','VARIABLE_SUBSTITUTION','CAUSAL_CHAIN_BREAK','OVERLOAD'].map((name,index)=>`<article class="error-model ${index===0?'active':''}"><b>${name}</b><span>${index===0?'当前真实支持':'框架保留 · 内容待开放'}</span></article>`).join('')}
    </section>
    <section class="regression-card"><div><p class="section-kicker">错一订三</p><h2>修复必须经过 Regression Test</h2><p>原题修正之后，系统用三道表层不同、底层变量相同的新题验证迁移。</p></div><div class="three-tests"><span>${model.session?.variant_passes?.includes('pointer-v1')?'✓':'1'}</span><span>${model.session?.variant_passes?.includes('pointer-v2')?'✓':'2'}</span><span>${model.session?.variant_passes?.includes('pointer-v3')?'✓':'3'}</span></div></section>
  `)
}

function topologyPage() {
  const nodes = model.manifest?.topology || []
  const groups = [...new Set(nodes.map(node => node.group))]
  return shell(`
    <div class="page-title"><p class="section-kicker">TOPOLOGY</p><h1>知识拓扑</h1><p>这里展示完整课程结构，但只有真实 Learning Events 能改变节点状态。</p></div>
    <section class="topology-summary"><div><small>课程</small><strong>${esc(courseLine())}</strong></div><div><small>当前真实节点</small><strong>2 / ${nodes.length}</strong></div><div><small>事实来源</small><strong>Learning Events</strong></div></section>
    <section class="topology-map">
      ${groups.map(group => `<div class="topology-column"><h3>${esc(group)}</h3>${nodes.filter(node=>node.group===group).map(node => {
        const status = node.status === 'runtime' ? runtimeNodeStatus(node.id) : node.status
        return `<article class="node node-${esc(String(status).toLowerCase())}"><span class="node-dot"></span><div><b>${esc(node.name)}</b><code>${esc(node.id)}</code></div><small>${esc(stateLabel(status))}</small></article>`
      }).join('')}</div>`).join('')}
    </section>
    <div class="info-note"><b>拓扑原则</b><span>Learning Events → Derived Learning State → Topology View。拓扑不直接修改事实。</span></div>
  `)
}

function assetsPage() {
  const errorEvents = model.events.filter(event => event.event_type === 'error_diagnosed')
  const verified = [
    ['relative_clause.pointer', runtimeNodeStatus('relative_clause.pointer')],
    ['word.root.rupt', runtimeNodeStatus('word.root.rupt')],
  ].filter(([,status])=>status==='VERIFIED')
  const recent = [...model.events].slice(-12).reverse()
  return shell(`
    <div class="page-title"><p class="section-kicker">ASSETS</p><h1>学习资产</h1><p>只沉淀真实发生过的错误、修复、验证和已掌握组件。</p></div>
    <section class="asset-grid">
      ${(model.manifest?.assets || []).map(item => `<article class="asset-card"><div><h3>${esc(item.name)}</h3>${statusBadge(item.status)}</div><p>${esc(item.description)}</p></article>`).join('')}
    </section>
    <div class="section-head"><div><p class="section-kicker">COMPONENTS</p><h2>已获得逻辑组件</h2></div></div>
    <section class="component-strip">${verified.length ? verified.map(([id])=>`<article><span>✓</span><div><b>${esc(id)}</b><small>VERIFIED</small></div></article>`).join('') : '<p class="empty">完成迁移验证后，真实组件会出现在这里。</p>'}</section>
    <div class="section-head"><div><p class="section-kicker">BUG ARCHIVE</p><h2>错误档案</h2></div></div>
    <section class="archive-card">${errorEvents.length ? errorEvents.map(event => `<div class="archive-row"><span class="danger-dot"></span><div><b>POINTER_ERROR</b><small>${esc(event.created_at || event.timestamp || '本次 Session')}</small></div><span>${model.events.some(item=>item.event_type==='patch_completed')?'已修复':'待修复'}</span></div>`).join('') : '<p class="empty">当前没有真实 Logic Bug 记录。</p>'}</section>
    <div class="section-head"><div><p class="section-kicker">EVENT STREAM</p><h2>学习记录</h2></div><span>${model.events.length} events</span></div>
    <section class="event-list">${recent.length ? recent.map(event => `<article><span class="event-dot"></span><div><b>${esc(EVENT_LABELS[event.event_type] || event.event_type)}</b><small>${esc(event.event_type)}</small></div></article>`).join('') : '<p class="empty">开始第一次学习后生成真实事件流。</p>'}</section>
  `)
}

function profilePage() {
  return shell(`
    <div class="page-title"><p class="section-kicker">PROFILE</p><h1>我的学习系统</h1><p>当前版本没有账号体系，只展示本地 Demo Session 与产品配置。</p></div>
    <section class="profile-card"><div class="avatar">∴</div><div><small>当前课程</small><h2>${esc(courseLine())}</h2><p>Product Shell V${esc(model.manifest?.version || '3.0')} · Deterministic Learning Core</p></div></section>
    <section class="settings-list">
      <article><span>Learning Agent</span><b>${model.session ? stageLabel() : 'Ready'}</b></article>
      <article><span>当前 Session</span><b>${model.session ? esc(model.session.session_id.slice(0,8))+'…' : '未开始'}</b></article>
      <article><span>内容范围</span><b>Unit 4 MVP</b></article>
      <article><span>AI 正确性依赖</span><b>OFF</b></article>
      <article><span>产品框架</span><b>FULL SHELL</b></article>
    </section>
    ${model.session ? '<button class="danger-button" data-action="reset">清除本地学习 Session</button>' : ''}
  `)
}

function previewPage() {
  const item = model.selectedCapability || {}
  return shell(`
    <button class="back-button" data-nav="lab">← 返回学习实验室</button>
    <section class="preview-hero"><div class="preview-icon">${esc(item.icon || '◇')}</div>${statusBadge(item.status || 'preview')}<p class="section-kicker">${esc(item.groupName || 'PRODUCT CAPABILITY')}</p><h1>${esc(item.name)}</h1><p>${esc(item.description)}</p></section>
    <section class="preview-content"><h2>这个能力会解决什么问题</h2><p>${esc(item.description)}</p>${item.future_interactions?.length ? `<h3>计划交互</h3><div class="interaction-tags">${item.future_interactions.map(value=>`<span>${esc(value)}</span>`).join('')}</div>`:''}<div class="info-note"><b>当前状态</b><span>此页面用于展示完整产品框架。当前内容包没有对应真实训练数据，因此不会生成假题目、假成绩或假学习记录。</span></div></section>
  `)
}

function taskCard() {
  const task = model.task || {}
  const choices = (task.choices || []).map(choice => `<button class="choice" data-choice="${esc(choice)}" ${model.loading?'disabled':''}>${esc(choice)}</button>`).join('')
  return `<section class="learning-stage">
    <div class="learning-head"><button class="back-button" data-nav="today">← 今日学习</button><div class="learning-state"><span>${esc(stageLabel())}</span><b>${progress()}%</b></div></div>
    <div class="track"><div class="bar" style="width:${progress()}%"></div></div>
    <section class="task-card">
      <div class="task-meta"><span>${esc(task.id)}</span>${model.errorType?`<span class="error-tag">${esc(model.errorType)}</span>`:''}</div>
      ${task.sentence?`<p class="sentence">${esc(task.sentence)}</p>`:''}
      ${task.word?`<div class="word">${esc(task.word)}</div>`:''}
      <h2>${esc(task.prompt)}</h2>
      <p class="message">${esc(model.message)}</p>
      ${model.hint?`<div class="hint"><b>最小提示</b><span>${esc(model.hint)}</span></div>`:''}
      <div class="choices">${choices}</div>
      ${model.session?.state==='TASK'?'<p class="demo-tip">演示错误路径可先选择 <b>trapped</b>，观察 Logic Bug 如何被修复。</p>':''}
    </section>
  </section>`
}

function learnPage() {
  if (!model.session) return shell(`<section class="empty-state"><div class="preview-icon">∴</div><h1>当前还没有学习 Session</h1><p>从今日任务进入当前唯一真实 Gold Loop。</p><button class="primary" data-action="start">开始学习</button></section>`)
  if (model.session.state !== 'DONE') return shell(taskCard())
  return shell(`<section class="result-page"><div class="success-mark">✓</div><p class="eyebrow">CLOSED LOOP</p><h1>本轮学习修复完成</h1><p>${esc(model.message)}</p><div class="result-grid"><div><small>relative_clause.pointer</small><strong>${esc(model.session.node_status)}</strong></div><div><small>word.root.rupt</small><strong>${esc(model.session.word_status)}</strong></div><div><small>Learning Events</small><strong>${model.events.length}</strong></div></div><div class="result-actions"><button class="secondary" data-nav="assets">查看学习资产</button><button class="secondary" data-nav="topology">查看知识拓扑</button><button class="primary compact" data-nav="home">返回首页</button></div><p class="evidence">CLOSED LOOP · Observe → Diagnose → Intervene → Verify → Update</p></section>`)
}

function render() {
  if (!model.manifest) {
    app.innerHTML = '<main class="boot"><div class="brand-mark">∴</div><p>加载文科实验室…</p></main>'
    return
  }
  const pages = {
    home:homePage, today:todayPage, lab:labPage, repair:repairPage,
    topology:topologyPage, assets:assetsPage, profile:profilePage,
    preview:previewPage, learn:learnPage,
  }
  app.innerHTML = (pages[model.view] || homePage)()

  app.querySelectorAll('[data-nav]').forEach(button => button.addEventListener('click', () => {
    model.view = button.dataset.nav
    render()
  }))
  app.querySelectorAll('[data-capability]').forEach(button => button.addEventListener('click', () => openCapability(button.dataset.capability)))
  app.querySelectorAll('[data-choice]').forEach(button => button.addEventListener('click', () => answer(button.dataset.choice)))
  app.querySelectorAll('[data-action="learn"]').forEach(button => button.addEventListener('click', ensureLearning))
  app.querySelectorAll('[data-action="start"]').forEach(button => button.addEventListener('click', startLearning))
  app.querySelectorAll('[data-action="reset"]').forEach(button => button.addEventListener('click', resetLearning))
}

async function boot() {
  render()
  await loadManifest()
  await restore()
  render()
}

boot()
