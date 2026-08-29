export function shortRunId(runId = '') {
  if (!runId) return '-'
  return runId.length > 14 ? `${runId.slice(0, 10)}...${runId.slice(-4)}` : runId
}

export function formatTime(timestamp) {
  if (!timestamp) return '未记录时间'
  const date = new Date(Number(timestamp) * 1000)
  if (Number.isNaN(date.getTime())) return '未记录时间'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function getDatasetName(path = '') {
  if (!path) return '-'
  const normalized = String(path).replaceAll('\\', '/')
  return normalized.split('/').filter(Boolean).at(-1) || path
}

export function compactText(text = '', max = 44) {
  const value = String(text || '').trim()
  if (!value) return '未命名任务'
  return value.length > max ? `${value.slice(0, max)}...` : value
}

export function statusType(status = '') {
  const map = {
    completed: 'success',
    running: 'warning',
    failed: 'danger',
    created: 'info',
    not_found: 'danger',
  }
  return map[status] || 'info'
}

export function scoreLevel(score) {
  const value = Number(score) || 0
  if (value >= 80) return 'strong'
  if (value >= 70) return 'good'
  if (value >= 60) return 'normal'
  return 'weak'
}

export function averageScore(scores = {}) {
  const values = Object.values(scores).map(Number).filter((item) => !Number.isNaN(item))
  if (!values.length) return 0
  return Math.round(values.reduce((sum, item) => sum + item, 0) / values.length)
}

export function downloadText(filename, text, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
