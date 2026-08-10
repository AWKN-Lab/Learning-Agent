const app = document.querySelector('#app')

const model = {
  session: null,
  task: null,
  message: '',
  hint: null,
  errorType: null,
  eventsCount: 0,
  loading: false,
}

const esc = (value = '') => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]))

function saveSessionId(id) {
  try { localStorage.setItem('learning-agent-session', id) } catch {}
}

function readSessionId() {
  try { return localStorage.getItem('learning-agent-session') } catch { return null }
}

function clearSessionId() {
  try { localStorage.removeItem('learning-agent-session') } catch {}
}

function newRequestId() {
  const token = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
  return `${model.session.session_id}:${token}`
}

function stageLabel() {
  if (!model.session) return '未开始'
  return ({TASK:'主任务', RETRY:'逻辑修复', VERIFY:'迁移验证', WORD_TASK:'能力迁移', DONE:'闭环完成'})[model.session.state] || model.session.state
}

function progress() {
  const state = model.session?.state
  if (state === 'TASK' || state === 'RETRY') return 20
  if (state === 'VERIFY') return 35 + (model.session.variant_index || 0) * 15
  if (state === 'WORD_TASK') return 85
  if (state === 'DONE') return 100
  return 0
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {'Content-Type':'application/json', ...(options.headers || {})},
    ...options,
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}

function applyResult(data) {
  model.session = data.session
  model.task = data.current_task || null
  model.message = data.message || ''
  model.hint = data.hint || null
  model.errorType = data.error_type || null
  saveSessionId(data.session.session_id)
}

async function refreshEventCount() {
  if (!model.session) return
  const snapshot = await api(`/api/v1/session/${model.session.session_id}`)
  model.eventsCount = snapshot.events.length
}

async function start() {
  model.loading = true
  render()
  try {
    applyResult(await api('/api/v1/session/start', {method:'POST'}))
    model.eventsCount = 2
  } catch (error) {
    model.message = `启动失败：${error.message}`
  } finally {
    model.loading = false
    render()
  }
}

async function restore() {
  const sid = readSessionId()
  if (!sid) return render()
  try {
    const data = await api(`/api/v1/session/${sid}`)
    model.session = data.session
    model.task = data.current_task
    model.eventsCount = data.events.length
    model.message = data.session.state === 'DONE' ? '上次学习闭环已完成。' : '已恢复上次学习现场。'
  } catch {
    clearSessionId()
  }
  render()
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
    const data = await api('/api/v1/learning/step', {
      method:'POST',
      body:JSON.stringify({
        session_id:model.session.session_id,
        event,
        event_id:newRequestId(),
        payload,
      }),
    })
    applyResult(data)
    await refreshEventCount()
  } catch (error) {
    model.message = `请求失败：${error.message}`
  } finally {
    model.loading = false
    render()
  }
}

function reset() {
  clearSessionId()
  Object.assign(model, {session:null, task:null, message:'', hint:null, errorType:null, eventsCount:0, loading:false})
  render()
}

function taskCard() {
  const task = model.task || {}
  const choices = (task.choices || []).map(choice => `<button class="choice" data-choice="${esc(choice)}" ${model.loading?'disabled':''}>${esc(choice)}</button>`).join('')
  return `<section class="lab-card">
    <div class="task-meta"><span>${esc(task.id)}</span>${model.errorType?`<span class="error-tag">${esc(model.errorType)}</span>`:''}</div>
    ${task.sentence?`<p class="sentence">${esc(task.sentence)}</p>`:''}
    ${task.word?`<div class="word">${esc(task.word)}</div>`:''}
    <h2>${esc(task.prompt)}</h2>
    <p class="message">${esc(model.message)}</p>
    ${model.hint?`<div class="hint"><b>最小提示</b><span>${esc(model.hint)}</span></div>`:''}
    <div class="choices">${choices}</div>
    ${model.session?.state==='TASK'?'<p class="demo-tip">演示错误路径可先选择 <b>trapped</b>。</p>':''}
  </section>`
}

function render() {
  app.innerHTML = `<main class="shell">
    <header class="hero">
      <div><p class="eyebrow">LEARNING AGENT · GOLD LOOP</p><h1>文科实验室</h1><p class="subtitle">把错误当成 Logic Bug：定位 → 最小干预 → 迁移验证 → 更新状态</p></div>
      <div class="status-pill">${esc(stageLabel())}</div>
    </header>
    <section class="progress-card">
      <div class="progress-copy"><span>闭环进度</span><strong>${progress()}%</strong></div>
      <div class="track"><div class="bar" style="width:${progress()}%"></div></div>
      ${model.session?`<div class="facts"><span>pointer: ${esc(model.session.node_status)}</span><span>rupt: ${esc(model.session.word_status)}</span><span>events: ${model.eventsCount}</span></div>`:''}
    </section>
    ${!model.session?`<section class="lab-card intro"><div class="icon">∴</div><h2>先证明学习真的发生</h2><p>首个 Gold Node：<code>relative_clause.pointer</code>。AI OFF 也能完整运行。</p><button id="start" class="primary" ${model.loading?'disabled':''}>开始 Gold Demo</button></section>`:
      model.session.state==='DONE'?`<section class="lab-card result"><div class="success-mark">✓</div><p class="eyebrow">CLOSED LOOP</p><h2>DEMO 闭环完成</h2><p>${esc(model.message)}</p><div class="result-grid"><div><small>relative_clause.pointer</small><strong>${esc(model.session.node_status)}</strong></div><div><small>word.root.rupt</small><strong>${esc(model.session.word_status)}</strong></div></div><p class="evidence">Learning Events 已记录：错误归因、提示、迁移验证、状态更新与完成事件。</p><button id="reset" class="secondary">重新演示</button></section>`:taskCard()}
    <footer>Observe → Diagnose → Intervene → Verify → Update</footer>
  </main>`

  document.querySelector('#start')?.addEventListener('click', start)
  document.querySelector('#reset')?.addEventListener('click', reset)
  document.querySelectorAll('[data-choice]').forEach(button => button.addEventListener('click', () => answer(button.dataset.choice)))
}

restore()
