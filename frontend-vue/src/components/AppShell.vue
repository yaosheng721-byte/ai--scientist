<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, Delete, Menu, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRunStore } from '../stores/runStore'
import { compactText, formatTime, getDatasetName, shortRunId, statusType } from '../utils/format'
import ChatAssistant from './ChatAssistant.vue'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()
const sidebarOpen = ref(false)

const selectedRunId = computed(() => String(route.params.runId || runStore.selectedRunId || ''))
const chatRunId = computed(() => String(route.params.runId || ''))

watch(
  () => route.fullPath,
  () => {
    sidebarOpen.value = false
  },
)

onMounted(async () => {
  await runStore.fetchRuns()
  if (selectedRunId.value && !runStore.selectedRun) {
    await runStore.fetchRun(selectedRunId.value)
  }
})

async function refreshRuns() {
  await runStore.fetchRuns()
  if (runStore.lastError) {
    ElMessage.warning(runStore.lastError)
  }
}

async function openRun(runId) {
  await runStore.selectRun(runId)
  router.push({ name: 'workspace', params: { runId } })
}

async function removeRun(runId) {
  try {
    await ElMessageBox.confirm(`确认删除任务 ${runId}？`, '删除任务', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await runStore.remove(runId)
    ElMessage.success('任务已删除')
    if (String(route.params.runId || '') === runId) {
      router.push({ name: 'create-run' })
    }
  } catch {
    // 用户取消时保持当前状态
  }
}
</script>

<template>
  <div class="app-shell">
    <header class="mobile-bar">
      <el-button :icon="Menu" text circle aria-label="打开任务导航" @click="sidebarOpen = true" />
      <div class="mobile-brand"><span>CV</span><strong>CV Scientist</strong></div>
    </header>

    <button
      v-if="sidebarOpen"
      class="sidebar-scrim"
      type="button"
      aria-label="关闭任务导航"
      @click="sidebarOpen = false"
    />

    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-top">
        <div class="brand">
          <div class="brand-mark">CV</div>
          <div>
            <div class="brand-title">CV Scientist</div>
            <div class="brand-subtitle">Research workspace</div>
          </div>
        </div>
        <el-button class="sidebar-close" :icon="Close" text circle aria-label="关闭任务导航" @click="sidebarOpen = false" />
      </div>

      <el-button
        class="new-task"
        type="primary"
        :icon="Plus"
        @click="router.push({ name: 'create-run' })"
      >
        新建任务
      </el-button>

      <div class="history-head">
        <span>任务历史</span>
        <el-button :icon="Refresh" text circle :loading="runStore.loadingRuns" @click="refreshRuns" />
      </div>

      <div v-if="runStore.runs.length" class="history-list">
        <button
          v-for="item in runStore.runs"
          :key="item.run_id"
          class="history-item"
          :class="{ active: item.run_id === selectedRunId }"
          @click="openRun(item.run_id)"
        >
          <span class="history-status-line" :data-status="item.status" />
          <div class="history-main">
            <span class="history-title">{{ compactText(item.query, 34) }}</span>
            <el-button
              :icon="Delete"
              text
              circle
              class="history-delete"
              :aria-label="`删除任务 ${shortRunId(item.run_id)}`"
              @click.stop="removeRun(item.run_id)"
            />
          </div>
          <div class="history-meta">
            <el-tag size="small" :type="statusType(item.status)" effect="plain">{{ item.status }}</el-tag>
            <span>{{ formatTime(item.created_at) }}</span>
          </div>
          <div class="history-extra">
            <span>{{ shortRunId(item.run_id) }}</span>
            <span>{{ item.task_type || 'research' }}</span>
            <span>{{ getDatasetName(item.dataset_path) }}</span>
          </div>
        </button>
      </div>

      <div v-else class="history-empty">
        <el-icon><Search /></el-icon>
        <span>暂无任务历史</span>
      </div>
    </aside>

    <main class="main-panel">
      <div class="content-frame">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <ChatAssistant :run-id="chatRunId" />
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 296px minmax(0, 1fr);
  min-height: 100vh;
  background: var(--app-bg);
}

.mobile-bar,
.sidebar-scrim,
.sidebar-close {
  display: none;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 16px;
  border-right: 1px solid var(--line);
  background: var(--surface);
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 2px 8px;
}

.brand-mark {
  position: relative;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: var(--brand);
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
}

.brand-mark::after {
  position: absolute;
  right: 5px;
  bottom: 5px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #39b8a9;
  content: "";
}

.brand-title {
  font-size: 16px;
  font-weight: 850;
  color: var(--text);
}

.brand-subtitle {
  margin-top: 2px;
  color: var(--text-muted);
  font-size: 12px;
}

.new-task {
  width: 100%;
  justify-content: center;
}

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 800;
}

.history-list {
  display: grid;
  gap: 10px;
  overflow: auto;
  padding: 1px 4px 12px 1px;
}

.history-item {
  position: relative;
  width: 100%;
  padding: 12px 12px 12px 15px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
}

.history-item:hover {
  border-color: var(--line-strong);
  background: var(--surface-raised);
}

.history-item.active {
  border-color: #91bdb8;
  background: #f3faf8;
  box-shadow: 0 8px 24px rgba(15, 118, 110, 0.08);
}

.history-status-line {
  position: absolute;
  top: 13px;
  bottom: 13px;
  left: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #b8c2c4;
}

.history-status-line[data-status="completed"] {
  background: var(--success);
}

.history-status-line[data-status="running"] {
  background: var(--warning);
}

.history-status-line[data-status="failed"] {
  background: var(--danger);
}

.history-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.history-title {
  min-width: 0;
  color: var(--text);
  font-size: 13px;
  font-weight: 750;
  line-height: 1.5;
}

.history-delete {
  flex: 0 0 auto;
  margin-top: -6px;
  color: var(--text-muted);
}

.history-meta,
.history-extra {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.history-extra span {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-empty {
  display: grid;
  place-items: center;
  gap: 8px;
  min-height: 180px;
  border: 1px dashed var(--line-strong);
  border-radius: 8px;
  color: var(--text-muted);
  background: var(--surface-soft);
  font-size: 13px;
}

.main-panel {
  min-width: 0;
  padding: 28px clamp(24px, 3vw, 46px) 48px;
}

.content-frame {
  width: min(100%, 1440px);
  margin: 0 auto;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.page-fade-leave-to {
  opacity: 0;
}

@media (max-width: 920px) {
  .app-shell {
    grid-template-columns: 1fr;
    padding-top: 56px;
  }

  .mobile-bar {
    position: fixed;
    z-index: 80;
    top: 0;
    right: 0;
    left: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    height: 56px;
    padding: 0 14px;
    border-bottom: 1px solid var(--line);
    background: rgba(255, 255, 255, 0.96);
  }

  .mobile-brand {
    display: flex;
    align-items: center;
    gap: 9px;
  }

  .mobile-brand span {
    display: grid;
    place-items: center;
    width: 26px;
    height: 26px;
    border-radius: 6px;
    background: var(--brand);
    color: #ffffff;
    font-size: 10px;
    font-weight: 800;
  }

  .mobile-brand strong {
    color: var(--text);
    font-size: 14px;
  }

  .sidebar-scrim {
    position: fixed;
    z-index: 89;
    inset: 0;
    display: block;
    border: 0;
    background: rgba(12, 23, 25, 0.38);
  }

  .sidebar {
    position: fixed;
    z-index: 90;
    top: 0;
    bottom: 0;
    left: 0;
    width: min(88vw, 320px);
    height: 100vh;
    transform: translateX(-102%);
    transition: transform 0.2s ease;
  }

  .sidebar.open {
    transform: translateX(0);
    box-shadow: 20px 0 50px rgba(12, 23, 25, 0.18);
  }

  .sidebar-close {
    display: inline-flex;
  }

  .main-panel {
    padding: 22px 18px 36px;
  }
}

@media (max-width: 520px) {
  .main-panel {
    padding-right: 12px;
    padding-left: 12px;
  }
}
</style>
