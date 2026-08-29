import { http } from './http'

export function listRuns() {
  return http.get('/runs')
}

export function createRun(payload) {
  return http.post('/runs', payload)
}

export function getRun(runId) {
  return http.get(`/runs/${runId}`)
}

export function deleteRun(runId) {
  return http.delete(`/runs/${runId}`)
}

export function getResults(runId, poolType) {
  return http.get(`/runs/${runId}/results`, {
    params: { pool_type: poolType },
  })
}

export function submitFeedback(runId, payload) {
  return http.post(`/runs/${runId}/feedback`, payload)
}

export function getArtifacts(runId) {
  return http.get(`/runs/${runId}/artifacts`)
}

export function getReport(runId) {
  return http.get(`/runs/${runId}/report`)
}

export function getToolCalls(runId) {
  return http.get(`/runs/${runId}/tool_calls`)
}

export function sendChat(payload) {
  return http.post('/chat', payload)
}
