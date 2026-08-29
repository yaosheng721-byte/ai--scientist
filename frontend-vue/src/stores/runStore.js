import { defineStore } from 'pinia'
import { createRun, deleteRun, getRun, listRuns } from '../api/runs'

export const useRunStore = defineStore('run', {
  state: () => ({
    runs: [],
    selectedRunId: localStorage.getItem('selectedRunId') || '',
    selectedRun: null,
    loadingRuns: false,
    loadingRun: false,
    lastError: '',
  }),
  getters: {
    hasSelectedRun: (state) => Boolean(state.selectedRunId),
  },
  actions: {
    setSelectedRunId(runId) {
      this.selectedRunId = runId || ''
      if (runId) {
        localStorage.setItem('selectedRunId', runId)
      } else {
        localStorage.removeItem('selectedRunId')
      }
    },
    async fetchRuns() {
      this.loadingRuns = true
      this.lastError = ''
      try {
        const data = await listRuns()
        this.runs = data.runs || []
      } catch (error) {
        this.lastError = error.message
        this.runs = []
      } finally {
        this.loadingRuns = false
      }
    },
    async selectRun(runId) {
      this.setSelectedRunId(runId)
      return this.fetchRun(runId)
    },
    async fetchRun(runId = this.selectedRunId) {
      if (!runId) return null
      this.loadingRun = true
      this.lastError = ''
      try {
        const data = await getRun(runId)
        this.selectedRun = data

        const runIndex = this.runs.findIndex((item) => item.run_id === runId)
        if (runIndex !== -1 && data.status !== 'not_found') {
          this.runs[runIndex] = {
            ...this.runs[runIndex],
            status: data.status,
            current_node: data.current_node,
            query: data.query || this.runs[runIndex].query,
            task_type: data.task_type || this.runs[runIndex].task_type,
            dataset_path: data.dataset_path || this.runs[runIndex].dataset_path,
          }
        }

        return data
      } catch (error) {
        this.lastError = error.message
        this.selectedRun = null
        return null
      } finally {
        this.loadingRun = false
      }
    },
    async create(payload) {
      const data = await createRun(payload)
      this.setSelectedRunId(data.run_id)
      await this.fetchRuns()
      await this.fetchRun(data.run_id)
      return data
    },
    async remove(runId) {
      await deleteRun(runId)
      if (this.selectedRunId === runId) {
        this.setSelectedRunId('')
        this.selectedRun = null
      }
      await this.fetchRuns()
    },
  },
})
