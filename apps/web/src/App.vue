<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type Task = {
  id: string
  sentence?: string
  word?: string
  prompt: string
  choices: string[]
}

type Session = {
  session_id: string
  state: string
  attempt: number
  hint_level: number
  variant_index: number
  node_status: string
  word_status: string
}

type ApiResult = {
  session: Session
  ui_action: string
  message: string
  error_type?: string | null
  hint?: string | null
  current_task?: Task | null
  topology_delta?: unknown
}

const apiBase = import.meta.env.VITE_API_BASE || ''
const session = ref<Session | null>(null)
const task = ref<Task | null>(null)
const message = ref('')
const hint = ref<string | null>(null)
const errorType = ref<string | null>(null)
const loading = ref(false)
const eventsCount = ref(0)

const stageLabel = computed(() => {
  const state = session.value?.state
  if (!state) return '未开始'
  return ({ TASK: '主任务', RETRY: '逻辑修复', VERIFY: '迁移验证', WORD_TASK: '能力迁移', DONE: '闭环完成' } as Record<string, string>)[state] || state
})

const progress = computed(() => {
  const state = session.value?.state
  if (state === 'TASK' || state === 'RETRY') return 20
  if (state === 'VERIFY') return 35 + (session.value?.variant_index || 0) * 15
  if (state === 'WORD_TASK') return 85
  if (state === 'DONE') return 100
  return 0
})

async function request(path: string, options?: RequestInit) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}

function applyResult(data: ApiResult) {
  session.value = data.session
  task.value = data.current_task || null
  message.value = data.message
  hint.value = data.hint || null
  errorType.value = data.error_type || null
  localStorage.setItem('learning-agent-session', data.session.session_id)
}

async function start() {
  loading.value = true
  try {
    const data = await request('/api/v1/session/start', { method: 'POST' })
    applyResult(data)
    eventsCount.value = 2
  } finally {
    loading.value = false
  }
}

async function restore() {
  const sid = localStorage.getItem('learning-agent-session')
  if (!sid) return
  try {
    const data = await request(`/api/v1/session/${sid}`)
    session.value = data.session
    task.value = data.current_task
    eventsCount.value = data.events.length
    message.value = data.session.state === 'DONE' ? '上次学习闭环已完成。' : '已恢复上次学习现场。'
  } catch {
    localStorage.removeItem('learning-agent-session')
  }
}

async function answer(choice: string) {
  if (!session.value || !task.value || loading.value) return
  loading.value = true
  try {
    let event = 'ANSWER_SUBMITTED'
    const payload: Record<string, string> = { answer: choice }
    if (session.value.state === 'VERIFY') {
      event = 'VERIFY_ANSWER'
      payload.variant_id = task.value.id
    } else if (session.value.state === 'WORD_TASK') {
      event = 'WORD_ANSWER'
    }
    const data = await request('/api/v1/learning/step', {
      method: 'POST',
      body: JSON.stringify({
        session_id: session.value.session_id,
        event,
        event_id: crypto.randomUUID(),
        payload,
      }),
    })
    applyResult(data)
    const snapshot = await request(`/api/v1/session/${session.value.session_id}`)
    eventsCount.value = snapshot.events.length
  } finally {
    loading.value = false
  }
}

function reset() {
  localStorage.removeItem('learning-agent-session')
  session.value = null
  task.value = null
  message.value = ''
  hint.value = null
  errorType.value = null
  eventsCount.value = 0
}

onMounted(restore)
</script>

<template>
  <main class="shell">
    <header class="hero">
      <div>
        <p class="eyebrow">LEARNING AGENT · GOLD LOOP</p>
        <h1>文科实验室</h1>
        <p class="subtitle">把错误当成 Logic Bug：定位 → 最小干预 → 迁移验证 → 更新状态</p>
      </div>
      <div class="status-pill">{{ stageLabel }}</div>
    </header>

    <section class="progress-card">
      <div class="progress-copy"><span>闭环进度</span><strong>{{ progress }}%</strong></div>
      <div class="track"><div class="bar" :style="{ width: `${progress}%` }"></div></div>
      <div class="facts" v-if="session">
        <span>pointer: {{ session.node_status }}</span>
        <span>rupt: {{ session.word_status }}</span>
        <span>events: {{ eventsCount }}</span>
      </div>
    </section>

    <section v-if="!session" class="lab-card intro">
      <div class="icon">∴</div>
      <h2>先证明学习真的发生</h2>
      <p>首个 Gold Node：<code>relative_clause.pointer</code>。AI OFF 也能完整运行。</p>
      <button class="primary" :disabled="loading" @click="start">开始 Gold Demo</button>
    </section>

    <section v-else-if="session.state !== 'DONE'" class="lab-card">
      <div class="task-meta">
        <span>{{ task?.id }}</span>
        <span v-if="errorType" class="error-tag">{{ errorType }}</span>
      </div>
      <p v-if="task?.sentence" class="sentence">{{ task.sentence }}</p>
      <div v-if="task?.word" class="word">{{ task.word }}</div>
      <h2>{{ task?.prompt }}</h2>
      <p class="message">{{ message }}</p>
      <div v-if="hint" class="hint"><b>最小提示</b>{{ hint }}</div>
      <div class="choices">
        <button v-for="choice in task?.choices" :key="choice" :disabled="loading" @click="answer(choice)">{{ choice }}</button>
      </div>
      <p v-if="session.state === 'TASK'" class="demo-tip">演示错误路径可先选择 <b>trapped</b>。</p>
    </section>

    <section v-else class="lab-card result">
      <div class="success-mark">✓</div>
      <p class="eyebrow">CLOSED LOOP</p>
      <h2>DEMO 闭环完成</h2>
      <p>{{ message }}</p>
      <div class="result-grid">
        <div><small>relative_clause.pointer</small><strong>{{ session.node_status }}</strong></div>
        <div><small>word.root.rupt</small><strong>{{ session.word_status }}</strong></div>
      </div>
      <p class="evidence">Learning Events 已记录：错误归因、提示、迁移验证、状态更新与完成事件。</p>
      <button class="secondary" @click="reset">重新演示</button>
    </section>

    <footer>Observe → Diagnose → Intervene → Verify → Update</footer>
  </main>
</template>
