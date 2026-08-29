<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { taskModules } from '../constants/modules'
import { useRunStore } from '../stores/runStore'
import { compactText, formatTime, getDatasetName, shortRunId, statusType } from '../utils/format'
import MetricTile from '../components/MetricTile.vue'
import PageHeader from '../components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()

const runId = computed(() => String(route.params.runId || runStore.selectedRunId || ''))
const run = computed(() => runStore.selectedRun || {})
const coreModules = computed(() => taskModules.filter((module) => module.group === 'core'))
const extendedModules = computed(() => taskModules.filter((module) => module.group === 'extended'))

async function refresh() {
  if (!runId.value) return
  await runStore.fetchRun(runId.value)
  if (runStore.lastError) ElMessage.warning(runStore.lastError)
}

function openModule(module) {
  router.push({ name: module.routeName, params: { runId: runId.value } })
}

onMounted(async () => {
  if (!runId.value) {
    router.replace({ name: 'create-run' })
    return
  }
  runStore.setSelectedRunId(runId.value)
  await refresh()
})
</script>

<template>
  <div class="page-stack">
    <PageHeader
      title="任务工作台"
      description="左侧任务历史只负责选择任务，具体模块统一从这里进入。"
    >
      <template #kicker>{{ shortRunId(runId) }}</template>
      <template #actions>
        <el-button :icon="Refresh" :loading="runStore.loadingRun" @click="refresh">刷新</el-button>
      </template>
    </PageHeader>

    <div class="metric-grid">
      <MetricTile label="状态" :value="run.status || '-'" :hint="run.current_node || '-'" />
      <MetricTile label="任务类型" :value="run.task_type || '-'" :hint="run.domain || 'default domain'" />
      <MetricTile label="数据集" :value="getDatasetName(run.dataset_path)" :hint="run.dataset_path || '-'" />
      <MetricTile label="创建时间" :value="formatTime(run.created_at)" :hint="runId" />
    </div>

    <section class="task-summary">
      <div class="summary-status" aria-hidden="true" />
      <div class="summary-copy">
        <div class="summary-label">当前研究任务</div>
        <div class="summary-title">{{ compactText(run.query || runId, 120) }}</div>
        <div class="summary-meta">
          <span>{{ getDatasetName(run.dataset_path) }}</span>
          <span>{{ run.task_type || '未指定类型' }}</span>
        </div>
      </div>
      <el-tag :type="statusType(run.status)" effect="plain">{{ run.status || 'unknown' }}</el-tag>
    </section>

    <section class="module-section">
      <div class="section-head">
        <div><h2>分析流程</h2><p>当前任务可直接使用的状态跟踪与数据画像能力</p></div>
        <span>3 个入口</span>
      </div>
      <div class="module-grid core-grid">
        <button
          v-for="(module, index) in coreModules"
          :key="module.key"
          type="button"
          class="module-card core-module"
          @click="openModule(module)"
        >
          <span class="module-index">0{{ index + 1 }}</span>
          <span class="module-icon"><el-icon><component :is="module.icon" /></el-icon></span>
          <span class="module-copy">
            <strong>{{ module.title }}</strong>
            <small>{{ module.description }}</small>
          </span>
          <el-icon class="module-arrow"><ArrowRight /></el-icon>
        </button>
      </div>
    </section>

    <section class="module-section extended-section">
      <div class="section-head">
        <div><h2>扩展研究模块</h2><p>由完整研究链路产生内容后，可从这里继续查看</p></div>
        <span>{{ extendedModules.length }} 个模块</span>
      </div>
      <div class="module-grid extended-grid">
        <button
          v-for="module in extendedModules"
          :key="module.key"
          type="button"
          class="module-card extended-module"
          @click="openModule(module)"
        >
          <span class="module-icon"><el-icon><component :is="module.icon" /></el-icon></span>
          <span class="module-copy">
            <strong>{{ module.title }}</strong>
            <small>{{ module.description }}</small>
          </span>
          <el-icon class="module-arrow"><ArrowRight /></el-icon>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.task-summary {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  overflow: hidden;
  padding: 20px 22px 20px 27px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.summary-status {
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--accent);
}

.summary-copy {
  min-width: 0;
}

.summary-label {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 800;
}

.summary-title {
  margin-top: 6px;
  color: var(--text);
  font-size: 17px;
  font-weight: 760;
  line-height: 1.5;
}

.summary-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 9px;
  color: var(--text-muted);
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 11px;
}

.module-section {
  display: grid;
  gap: 12px;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 0 2px;
}

.section-head h2 {
  margin: 0;
  color: var(--text);
  font-size: 15px;
}

.section-head p,
.section-head > span {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.module-grid {
  display: grid;
  gap: 10px;
}

.core-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.extended-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.module-card {
  position: relative;
  display: grid;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease, background 0.16s ease;
}

.module-card:hover {
  border-color: #94a3b8;
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.core-module {
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 13px;
  min-height: 118px;
  padding: 22px 18px;
}

.extended-module {
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: start;
  gap: 11px;
  min-height: 118px;
  padding: 16px;
  background: color-mix(in srgb, var(--surface) 76%, var(--surface-soft));
}

.module-index {
  position: absolute;
  top: 11px;
  right: 13px;
  color: #b5c0c5;
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 10px;
  font-weight: 700;
}

.module-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #f3f4f6;
  color: var(--accent);
  font-size: 18px;
}

.module-copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.module-copy strong {
  color: var(--text);
  font-size: 14px;
  font-weight: 760;
}

.module-copy small {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.module-arrow {
  align-self: center;
  color: var(--text-muted);
  transition: color 0.16s ease, transform 0.16s ease;
}

.module-card:hover .module-arrow {
  color: var(--accent);
  transform: translateX(2px);
}

@media (max-width: 1280px) {
  .extended-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .core-grid,
  .extended-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .core-grid,
  .extended-grid {
    grid-template-columns: 1fr;
  }

  .task-summary,
  .section-head {
    align-items: flex-start;
  }

  .task-summary {
    flex-direction: column;
  }
}
</style>
