/* 文科实验室 · 学习闭环：观察 → 诊断 → 修复 → 验证 · CLOSED LOOP */
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
  onboarded: false,
}

const esc = (value = '') => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]))

const EVENT_LABELS = {
  session_started: '开始学习',
  task_planned: '系统安排了任务',
  answer_submitted: '提交答案',
  error_diagnosed: '找到了错误原因',
  hint_given: '给出提示',
  main_task_passed: '主任务通过',
  variant_answered: '变式题作答',
  patch_completed: '完成修复',
  learning_state_updated: '更新学习状态',
  next_task_selected: '选择下一任务',
  word_verified: '词根能力验证',
  demo_completed: '本轮学习完成',
}

/* ---------- 本地存储 ---------- */
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

function readOnboarded() {
  try { return localStorage.getItem('learning-agent-onboarded') === '1' } catch { return false }
}

function markOnboarded() {
  try { localStorage.setItem('learning-agent-onboarded', '1') } catch {}
}

/* ---------- 工具 ---------- */
function newRequestId() {
  const token = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
  return `${model.session.session_id}:${token}`
}

function stageLabel() {
  if (!model.session) return '尚未开始'
  return ({TASK:'主任务进行中', RETRY:'修复错误中', VERIFY:'变式验证中', WORD_TASK:'词根迁移中', DONE:'本轮已完成'})[model.session.state] || model.session.state
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
    VERIFIED: '已掌握', REVIEW_DUE: '待复习', LOCKED: '待解锁', preview: '即将上线', locked: '待解锁'
  })[value] || value
}

function statusBadge(status) {
  const label = model.manifest?.status_labels?.[status] || status
  return `<span class="badge badge-${esc(status)}">${esc(label)}</span>`
}

/* ---------- API ---------- */
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
    const response = await fetch('product-manifest.json', {cache:'no-store'})
    if (!response.ok) throw new Error('manifest_load_failed')
    model.manifest = await response.json()
  } catch {
    model.manifest = {version:'3.0', course:{grade:'高一',subject:'英语',book:'必修一',unit:'Unit 4'}, status_labels:{live:'可使用',limited:'部分开放',preview:'即将上线',locked:'待解锁'}, groups:[], assets:[], topology:[]}
  }
}

async function submitCommand(body) {
  const options = {method:'POST', body:JSON.stringify(body)}
  try {
    return await api('api/v1/learning/step', options)
  } catch (error) {
    if (error.network) return api('api/v1/learning/step', options)
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
  const snapshot = await api(`api/v1/session/${model.session.session_id}`)
  model.session = snapshot.session
  model.task = snapshot.current_task
  model.events = snapshot.events || []
}

/* ---------- 行为 ---------- */
async function startLearning() {
  model.loading = true
  model.view = 'learn'
  render()
  try {
    applyResult(await api('api/v1/session/start', {method:'POST'}))
    await refreshSnapshot()
  } catch (error) {
    model.message = `启动失败，请检查网络后重试`
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
    const data = await api(`api/v1/session/${auth.id}`)
    model.session = data.session
    model.task = data.current_task
    model.events = data.events || []
    model.message = data.session.state === 'DONE' ? '上次的学习已经完成。' : '已恢复上次的学习进度。'
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
        model.message = '状态同步失败，请刷新页面重试。'
      }
    } else {
      model.message = '网络异常，请重试一次。'
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

function dismissOnboard() {
  model.onboarded = true
  markOnboarded()
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

/* ---------- 骨架 ---------- */
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
    ['home','首页','⌂'], ['today','今日','◉'], ['lab','实验室','✦'], ['profile','我的','☺'],
  ]
  return `<nav class="bottom-nav">${items.map(([id,label,icon]) => `<button data-nav="${id}" class="${model.view===id?'active':''}"><span>${icon}</span><small>${label}</small></button>`).join('')}</nav>`
}

function shell(content) {
  return `<main class="product-shell">${header()}<div class="page">${content}</div>${bottomNav()}</main>`
}

function onboardBar() {
  if (model.onboarded) return ''
  return `<aside class="onboard">
    <span class="ob-icon">✦</span>
    <div><h3>第一次来？花 10 秒了解它</h3><p>做一道语法题 → 系统找出你错在哪 → 给你提示修好它 → 再用三道变式题确认你真的会了。</p></div>
    <button data-action="dismiss-onboard">知道了</button>
  </aside>`
}

/* ---------- 首页 ---------- */
function homePage() {
  const pointer = runtimeNodeStatus('relative_clause.pointer')
  const rupt = runtimeNodeStatus('word.root.rupt')
  const currentState = model.session ? stageLabel() : '尚未开始'
  const latestError = [...model.events].reverse().find(event => event.event_type === 'error_diagnosed')
  const verified = [pointer, rupt].filter(value => value === 'VERIFIED').length
  const started = !!model.session
  return shell(`
    ${onboardBar()}
    <section class="welcome">
      <div class="reveal">
        <p class="eyebrow">AI 语法纠错教练</p>
        <h1>每道错题，都帮你找到<span class="hl">真正的病因</span></h1>
        <p class="lead">做对不算完——答错后系统会指出你卡在哪一步，给提示带你修好，再用三道变式题确认你是真的会了。</p>
        <p class="course-line">${esc(courseLine())}</p>
        <div class="hero-steps">
          <span><i>1</i>做一道题</span><span><i>2</i>定位错因</span><span><i>3</i>针对修复</span><span><i>4</i>三题验证</span>
        </div>
      </div>
      <div class="hero-art reveal" data-d="1"><img src="assets/hero-synthesis.jpg" alt="学生正在学习语法，周围是知识节点图谱" /></div>
    </section>

    <section class="hero-task reveal" data-d="1">
      <div class="hero-task-copy">
        <div class="section-kicker">今日优先任务</div>
        <h2>${model.session?.state === 'DONE' ? '本轮学习已完成' : '定语从句 · which 指向关系'}</h2>
        <p>${model.session?.state === 'DONE' ? '看看这一轮修好了什么、知识图谱有什么变化。' : '先修复当前最影响理解的语法点，修好后再进入词根逻辑训练。'}</p>
        <div class="task-facts"><span>进度：${esc(currentState)}</span><span>定语从句：${esc(stateLabel(pointer))}</span><span>词根 rupt：${esc(stateLabel(rupt))}</span></div>
      </div>
      <button class="primary" data-action="learn">${model.session?.state === 'DONE' ? '查看学习结果' : model.session ? '继续学习' : '开始今日学习'}</button>
    </section>

    <section class="stats-grid">
      <article class="reveal" data-d="1"><small>当前知识点</small><strong>2</strong><span>本单元核心内容</span></article>
      <article class="reveal" data-d="2"><small>已掌握</small><strong>${verified}</strong><span>${started ? '通过三题验证才算掌握' : '开始学习后这里会更新'}</span></article>
      <article class="reveal" data-d="3"><small>学习记录</small><strong>${model.events.length}</strong><span>${model.events.length ? '每一步都有据可查' : '完成第一题后生成'}</span></article>
      <article class="reveal" data-d="4"><small>最近的错误</small><strong class="small-strong">${latestError ? '指向关系错误' : '暂无'}</strong><span>${latestError ? '可在修复中心查看' : '答错后这里会记录'}</span></article>
    </section>

    <div class="section-head reveal"><div><p class="section-kicker">学习实验室</p><h2>还能练什么</h2></div><button data-nav="lab" class="text-button">查看全部 →</button></div>
    <section class="home-labs">
      ${(model.manifest?.groups || []).map((group, i) => `<article class="group-preview reveal" data-d="${(i%4)+1}"><div class="group-icon">${group.id==='decode'?'⌘':group.id==='causal'?'⇢':'⊕'}</div><div><h3>${esc(group.name)}</h3><p>${esc(group.description)}</p><div class="mini-statuses">${group.capabilities.map(item => statusBadge(item.status)).join('')}</div></div></article>`).join('')}
    </section>

    <section class="split-panels">
      <button class="panel-card reveal" data-nav="topology"><span class="panel-icon">⌘</span><div><small>知识地图</small><h3>${esc(stateLabel(pointer))} · 定语从句指向</h3><p>看看本单元的能力地图，先学什么、后学什么一目了然。</p></div><b>→</b></button>
      <button class="panel-card reveal" data-d="1" data-nav="assets"><span class="panel-icon">▦</span><div><small>学习档案</small><h3>${model.events.length ? `${model.events.length} 条真实学习记录` : '等待第一次学习'}</h3><p>你的错题档案、修复日志和已掌握的语法组件都在这。</p></div><b>→</b></button>
    </section>
  `)
}

/* ---------- 今日 ---------- */
function todayPage() {
  return shell(`
    <div class="page-title reveal"><p class="section-kicker">TODAY</p><h1>今日学习</h1><p>系统只根据你的真实掌握情况安排任务，不凑数、不重复。</p></div>
    <section class="timeline-card current reveal">
      <span class="timeline-dot"></span>
      <div><small>01 · 当前优先</small><h2>修复 which 指向关系</h2><p>知识点：<code>定语从句指向</code> · 状态：${esc(stateLabel(runtimeNodeStatus('relative_clause.pointer')))}</p></div>
      <button class="primary compact" data-action="learn">${model.session ? '继续' : '开始'}</button>
    </section>
    <section class="timeline-card ${runtimeNodeStatus('relative_clause.pointer')==='VERIFIED'?'current':'muted'} reveal" data-d="1">
      <span class="timeline-dot"></span><div><small>02 · 下一项</small><h2>词根逻辑拆解 · rupt</h2><p>修好上面的语法点后自动解锁。</p></div>${statusBadge('limited')}
    </section>
    <section class="timeline-card muted reveal" data-d="2"><span class="timeline-dot"></span><div><small>03 · 后续内容</small><h2>从句约束 / 文章结构 / 因果链</h2><p>框架已就绪，内容正在制作中。</p></div>${statusBadge('locked')}</section>
    <section class="split-panels reveal" data-d="2">
      <button class="panel-card" data-nav="repair"><span class="panel-icon">⊕</span><div><small>修复中心</small><h3>查看错误诊断</h3><p>你错在哪、提示了几次、修没修好，都有记录。</p></div><b>→</b></button>
    </section>
    <div class="info-note reveal" data-d="3"><b>任务怎么排？</b><span>正在阻断你的错误优先，其次是反复错的、掌握不牢的、到期该复习的，最后才是新内容。</span></div>
  `)
}

/* ---------- 实验室 ---------- */
function capabilityCard(item) {
  return `<button class="capability-card" data-capability="${esc(item.id)}">
    <div class="cap-icon">${esc(item.icon || '◇')}</div>
    <div class="cap-copy"><div class="cap-title"><h3>${esc(item.name)}</h3>${statusBadge(item.status)}</div><p>${esc(item.description)}</p></div>
    <span class="chevron">→</span>
  </button>`
}

function labPage() {
  return shell(`
    <div class="page-title reveal"><p class="section-kicker">LAB</p><h1>学习实验室</h1><p>这里能看到产品的完整能力规划；标注「可使用」的入口会真实改变你的学习状态。</p></div>
    ${(model.manifest?.groups || []).map((group, i) => `<section class="lab-group reveal" data-d="${(i%3)+1}"><div class="section-head"><div><h2>${esc(group.name)}</h2><p>${esc(group.description)}</p></div></div><div class="cap-list">${group.capabilities.map(capabilityCard).join('')}</div></section>`).join('')}
  `)
}

/* ---------- 修复中心 ---------- */
function repairPage() {
  const errors = model.events.filter(event => event.event_type === 'error_diagnosed')
  const hints = model.events.filter(event => event.event_type === 'hint_given')
  const patched = model.events.some(event => event.event_type === 'patch_completed')
  return shell(`
    <div class="page-title reveal"><p class="section-kicker">修复中心</p><h1>你的错误，都能被修好</h1><p>错题不是改个答案就完事——系统会追踪你为什么错、提示了几次、最后是不是真的修好了。</p></div>
    <section class="bug-card ${errors.length?'has-bug':''} reveal">
      <div class="bug-code">${errors.length ? '指向关系错误' : '暂无错误'}</div>
      <div><small>当前诊断</small><h2>${errors.length ? 'which 指向关系错误' : '还没有错误记录'}</h2><p>${errors.length ? `系统给过 ${hints.length} 次提示；修复状态：${patched?'已修好 ✓':'修复中'}` : '做一道题之后，如果你答错了，这里会出现具体诊断。'}</p></div>
      <button class="secondary" data-action="learn">${errors.length?'回到修复现场':'去做一道题'}</button>
    </section>
    <div class="section-head reveal"><div><p class="section-kicker">错误类型</p><h2>系统能识别哪些错误</h2></div></div>
    <section class="error-model-grid reveal" data-d="1">
      ${[['POINTER_ERROR','指向关系错','当前支持'],['CONSTRAINT_OMISSION','漏掉约束条件','内容制作中'],['VARIABLE_SUBSTITUTION','指代替换错','内容制作中'],['CAUSAL_CHAIN_BREAK','因果链断裂','内容制作中'],['OVERLOAD','信息过载','内容制作中']].map(([code,name,note],index)=>`<article class="error-model ${index===0?'active':''}"><b>${name}</b><span>${note}</span></article>`).join('')}
    </section>
    <section class="regression-card reveal" data-d="2"><div><p class="section-kicker">错一题，练三题</p><h2>修好不算完，验证过才算会</h2><p>原题答对之后，系统会用三道「换个说法、考同一个点」的新题来确认你是真的掌握了。</p></div><div class="three-tests"><span class="${model.session?.variant_passes?.includes('pointer-v1')?'done':''}">${model.session?.variant_passes?.includes('pointer-v1')?'✓':'1'}</span><span class="${model.session?.variant_passes?.includes('pointer-v2')?'done':''}">${model.session?.variant_passes?.includes('pointer-v2')?'✓':'2'}</span><span class="${model.session?.variant_passes?.includes('pointer-v3')?'done':''}">${model.session?.variant_passes?.includes('pointer-v3')?'✓':'3'}</span></div></section>
  `)
}

/* ---------- 知识地图 ---------- */
function topologyPage() {
  const nodes = model.manifest?.topology || []
  const groups = [...new Set(nodes.map(node => node.group))]
  return shell(`
    <button class="back-button" data-nav="home">← 返回首页</button>
    <div class="page-title reveal"><p class="section-kicker">知识地图</p><h1>这个单元要学什么</h1><p>完整的课程结构都在这里；只有你真实做过的题，才会改变每个知识点的状态。</p></div>
    <section class="topology-summary reveal" data-d="1"><div><small>课程</small><strong>${esc(courseLine())}</strong></div><div><small>已开放知识点</small><strong>2 / ${nodes.length}</strong></div><div><small>状态来源</small><strong>你的真实作答</strong></div></section>
    <section class="topology-map reveal" data-d="2">
      ${groups.map(group => `<div class="topology-column"><h3>${esc(group)}</h3>${nodes.filter(node=>node.group===group).map(node => {
        const status = node.status === 'runtime' ? runtimeNodeStatus(node.id) : node.status
        return `<article class="node node-${esc(String(status).toLowerCase())}"><span class="node-dot"></span><div><b>${esc(node.name)}</b></div><small>${esc(stateLabel(status))}</small></article>`
      }).join('')}</div>`).join('')}
    </section>
    <div class="info-note reveal" data-d="3"><b>怎么看这张图？</b><span>绿色点是已掌握，黄色点正在修复，灰色点还没开始。知识点按学习顺序排列，前面修好才会解锁后面。</span></div>
  `)
}

/* ---------- 学习档案 ---------- */
function assetsPage() {
  const errorEvents = model.events.filter(event => event.event_type === 'error_diagnosed')
  const verified = [
    ['定语从句指向', runtimeNodeStatus('relative_clause.pointer')],
    ['词根 rupt', runtimeNodeStatus('word.root.rupt')],
  ].filter(([,status])=>status==='VERIFIED')
  const recent = [...model.events].slice(-12).reverse()
  return shell(`
    <button class="back-button" data-nav="home">← 返回首页</button>
    <div class="page-title reveal"><p class="section-kicker">学习档案</p><h1>你真实学过的痕迹</h1><p>只记录真实发生过的错误、修复和验证，没有虚假数据。</p></div>
    <section class="asset-grid reveal" data-d="1">
      ${(model.manifest?.assets || []).map(item => `<article class="asset-card"><div><h3>${esc(item.name)}</h3>${statusBadge(item.status)}</div><p>${esc(item.description)}</p></article>`).join('')}
    </section>
    <div class="section-head reveal"><div><p class="section-kicker">已掌握</p><h2>这些点你是真的会了</h2></div></div>
    <section class="component-strip reveal" data-d="1">${verified.length ? verified.map(([name])=>`<article><span>✓</span><div><b>${esc(name)}</b><small>已通过三题验证</small></div></article>`).join('') : `<div class="empty-state" style="padding:26px"><img src="assets/empty-synthesis.jpg" alt="" class="result-illustration"/><p class="empty" style="padding:0">还没有已掌握的知识点。<br>完成一轮「做题 → 修复 → 验证」后，这里会出现第一个。</p></div>`}</section>
    <div class="section-head reveal"><div><p class="section-kicker">错题档案</p><h2>你踩过的坑</h2></div></div>
    <section class="archive-card reveal" data-d="1">${errorEvents.length ? errorEvents.map(event => `<div class="archive-row"><span class="danger-dot"></span><div><b>指向关系错误</b><small>${esc(event.created_at || event.timestamp || '本次学习')}</small></div><span>${model.events.some(item=>item.event_type==='patch_completed')?'已修复 ✓':'待修复'}</span></div>`).join('') : '<p class="empty">目前还没有错题记录，这是好事。</p>'}</section>
    <div class="section-head reveal"><div><p class="section-kicker">学习流水</p><h2>每一步都有记录</h2></div><span>${model.events.length} 条</span></div>
    <section class="event-list reveal" data-d="1">${recent.length ? recent.map((event, i) => `<article style="animation-delay:${i*40}ms"><span class="event-dot"></span><div><b>${esc(EVENT_LABELS[event.event_type] || event.event_type)}</b><small>${esc(event.event_type)}</small></div></article>`).join('') : '<p class="empty">开始第一次学习后，这里会出现你的完整学习过程。</p>'}</section>
  `)
}

/* ---------- 我的 ---------- */
function profilePage() {
  return shell(`
    <div class="page-title reveal"><p class="section-kicker">我的</p><h1>我的学习</h1><p>当前是本地体验版，学习数据保存在这台设备上。</p></div>
    <section class="profile-card reveal"><div class="avatar">∴</div><div><small>当前课程</small><h2>${esc(courseLine())}</h2><p>文科实验室 · 体验版 V${esc(model.manifest?.version || '3.0')}</p></div></section>
    <section class="settings-list reveal" data-d="1">
      <article><span>学习阶段</span><b>${model.session ? stageLabel() : '待开始'}</b></article>
      <article><span>学习记录</span><b>${model.events.length} 条</b></article>
      <article><span>内容范围</span><b>Unit 4 核心语法</b></article>
    </section>
    <section class="about-card reveal" data-d="2">
      <h3>这个产品是什么？</h3>
      <p>一个帮你「根治」语法错误的教练。普通刷题告诉你对错，它会继续追问：你错在哪一步？然后给你刚好够用的提示，让你自己想明白，最后用三道变式题确认你是真的会了。</p>
    </section>
    <section class="settings-list reveal" data-d="2">
      <article style="cursor:pointer" data-nav="about"><span>了解它的工作原理</span><b>→</b></article>
      <article style="cursor:pointer" data-nav="topology"><span>查看知识地图</span><b>→</b></article>
      <article style="cursor:pointer" data-nav="assets"><span>查看学习档案</span><b>→</b></article>
    </section>
    ${model.session ? '<button class="danger-button" data-action="reset">清除本设备上的学习记录</button>' : ''}
  `)
}

/* ---------- 关于（工作原理） ---------- */
function aboutPage() {
  const steps = [
    ['① 观察', '你做题的每一次选择都会被记录，包括选错的。'],
    ['② 诊断', '答错时，系统不只说「错了」，而是定位你卡在哪一步——比如把 which 指向了错误的词。'],
    ['③ 修复', '系统给一条「刚好够用」的提示，不直接给答案，让你自己想明白。'],
    ['④ 验证', '原题答对后，还有三道「换汤不换药」的变式题。全部通过，才算真正掌握。'],
  ]
  return shell(`
    <button class="back-button" data-nav="profile">← 返回我的</button>
    <div class="page-title reveal"><p class="section-kicker">工作原理</p><h1>它怎么帮你学会</h1><p>四步一个闭环，每一步都基于你的真实作答，没有虚假分数。</p></div>
    <section class="cap-list">
      ${steps.map(([title, desc], i) => `<article class="capability-card reveal" data-d="${i+1}" style="cursor:default"><div class="cap-icon">${esc(title.slice(0,1))}</div><div class="cap-copy"><div class="cap-title"><h3>${esc(title)}</h3></div><p>${esc(desc)}</p></div></article>`).join('')}
    </section>
    <section class="about-card reveal" data-d="3" style="margin-top:18px">
      <h3>数据与安全</h3>
      <p>当前体验版的所有学习数据只保存在你这台设备的浏览器里，不上传服务器、不需要注册、不收集任何个人信息。清除浏览器数据即可删除全部记录。</p>
    </section>
  `)
}

/* ---------- 能力预览 ---------- */
function previewPage() {
  const item = model.selectedCapability || {}
  return shell(`
    <button class="back-button" data-nav="lab">← 返回学习实验室</button>
    <section class="preview-hero reveal"><div class="preview-icon">${esc(item.icon || '◇')}</div>${statusBadge(item.status || 'preview')}<p class="section-kicker">${esc(item.groupName || '产品能力')}</p><h1>${esc(item.name)}</h1><p>${esc(item.description)}</p></section>
    <section class="preview-content reveal" data-d="1"><h2>它能帮你解决什么</h2><p>${esc(item.description)}</p>${item.future_interactions?.length ? `<h3>上线后会有这些玩法</h3><div class="interaction-tags">${item.future_interactions.map(value=>`<span>${esc(value)}</span>`).join('')}</div>`:''}<div class="info-note"><b>为什么现在用不了？</b><span>这个功能的内容还在制作中。我们不做假题目、假分数——内容准备好之前，宁可先锁着。</span></div></section>
  `)
}

/* ---------- 学习页 ---------- */
function taskCard() {
  const task = model.task || {}
  const choices = (task.choices || []).map(choice => `<button class="choice" data-choice="${esc(choice)}" ${model.loading?'disabled':''}>${esc(choice)}</button>`).join('')
  const encourage = model.errorType ? '<p class="message encourage">没关系，错一次才知道坑在哪。看看提示，再试一次。</p>' : ''
  return `<section class="learning-stage">
    <div class="learning-head"><button class="back-button" data-nav="today">← 今日学习</button><div class="learning-state"><span>${esc(stageLabel())}</span><b>${progress()}%</b></div></div>
    <div class="track"><div class="bar" style="width:${progress()}%"></div></div>
    <section class="task-card">
      <div class="task-meta"><span>${esc(task.id)}</span>${model.errorType?`<span class="error-tag">已定位错因</span>`:''}</div>
      ${task.sentence?`<p class="sentence">${esc(task.sentence)}</p>`:''}
      ${task.word?`<div class="word">${esc(task.word)}</div>`:''}
      <h2>${esc(task.prompt)}</h2>
      <p class="message">${esc(model.message)}</p>
      ${encourage}
      ${model.hint?`<div class="hint"><b>提示</b><span>${esc(model.hint)}</span></div>`:''}
      <div class="choices">${choices}</div>
      ${model.session?.state==='TASK'?'<p class="demo-tip">选错也不用担心——系统会告诉你错在哪，并带你修好它。</p>':''}
    </section>
  </section>`
}

function learnPage() {
  if (!model.session) return shell(`<section class="empty-state"><img src="assets/empty-synthesis.jpg" alt=""/><h1>还没有开始学习</h1><p>从今天的第一个语法任务开始，体验「错了也能修好」的完整过程。</p><button class="primary" data-action="start">开始学习</button></section>`)
  if (model.session.state !== 'DONE') return shell(taskCard())
  return shell(`<section class="result-page"><div class="success-mark">✓</div><p class="eyebrow">本轮完成</p><h1>这个语法点，你修好了</h1><p>${esc(model.message || '原题修正 + 三道变式题全部通过，是真正的掌握。')}</p><div class="result-grid"><div><small>定语从句指向</small><strong>${esc(model.session.node_status)}</strong></div><div><small>词根 rupt</small><strong>${esc(model.session.word_status)}</strong></div><div><small>学习记录</small><strong>${model.events.length} 条</strong></div></div><div class="result-actions"><button class="secondary" data-nav="assets">查看学习档案</button><button class="secondary" data-nav="topology">查看知识地图</button><button class="primary compact" data-nav="home">返回首页</button></div><p class="evidence">观察 → 诊断 → 修复 → 验证 · 四步闭环</p></section>`)
}

/* ---------- 渲染 ---------- */
let revealObserver = null

function bindMotion() {
  const topbar = app.querySelector('.topbar')
  if (topbar) {
    const sync = () => topbar.classList.toggle('scrolled', window.scrollY > 8)
    sync()
    window.addEventListener('scroll', sync, {passive: true})
  }
  const targets = app.querySelectorAll('.reveal')
  if (!('IntersectionObserver' in window)) {
    targets.forEach(el => el.classList.add('in'))
    return
  }
  if (!revealObserver) {
    revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in')
          revealObserver.unobserve(entry.target)
        }
      })
    }, {threshold: .08, rootMargin: '0px 0px -8% 0px'})
  }
  targets.forEach(el => revealObserver.observe(el))
}

function render() {
  if (!model.manifest) {
    app.innerHTML = '<main class="boot"><div class="brand-mark">∴</div><div class="boot-ring"></div><p>正在打开文科实验室…</p></main>'
    return
  }
  const pages = {
    home:homePage, today:todayPage, lab:labPage, repair:repairPage,
    topology:topologyPage, assets:assetsPage, profile:profilePage,
    about:aboutPage, preview:previewPage, learn:learnPage,
  }
  app.innerHTML = (pages[model.view] || homePage)()
  window.scrollTo({top: 0})

  app.querySelectorAll('[data-nav]').forEach(button => button.addEventListener('click', () => {
    model.view = button.dataset.nav
    render()
  }))
  app.querySelectorAll('[data-capability]').forEach(button => button.addEventListener('click', () => openCapability(button.dataset.capability)))
  app.querySelectorAll('[data-choice]').forEach(button => button.addEventListener('click', () => answer(button.dataset.choice)))
  app.querySelectorAll('[data-action="learn"]').forEach(button => button.addEventListener('click', ensureLearning))
  app.querySelectorAll('[data-action="start"]').forEach(button => button.addEventListener('click', startLearning))
  app.querySelectorAll('[data-action="reset"]').forEach(button => button.addEventListener('click', resetLearning))
  app.querySelectorAll('[data-action="dismiss-onboard"]').forEach(button => button.addEventListener('click', dismissOnboard))

  bindMotion()
}

async function boot() {
  model.onboarded = readOnboarded()
  render()
  await loadManifest()
  await restore()
  render()
}

boot()
