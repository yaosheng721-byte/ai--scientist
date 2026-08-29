<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import JsonBlock from '../components/JsonBlock.vue'
import MetricTile from '../components/MetricTile.vue'
import PageHeader from '../components/PageHeader.vue'
import { useRunStore } from '../stores/runStore'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()
const runId = computed(() => String(route.params.runId || ''))
const autoRefresh = ref(false)
const expandedSections = ref([])
let timer = null

const run = computed(() => runStore.selectedRun || {})
const result = computed(() => run.value.result || {})
const splits = computed(() => result.value.splits || {})
const observations = computed(() => result.value.observations || [])
const artifactCounts = computed(() => ({
  charts: result.value.artifacts?.interactive_charts?.length || 0,
  samples: result.value.artifacts?.sample_images?.length || 0,
}))

const nodeLabels = {
  initializing: '初始化任务',
  dataset_scan: '扫描数据集',
  annotation_parsing: '解析标注',
  image_quality: '图像质量分析',
  image_analysis: '图像特征分析',
  plot_generation: '生成画像图表',
  observation_generation: '生成观察结论',
  completed: '任务完成',
  dataset_profiling: '数据集画像',
}

const progress = computed(() => {
  const value = Number(runStore.selectedRun?.progress || 0)
  return Math.max(0, Math.min(100, Math.round(value)))
})

const currentStage = computed(() => {
  const node = runStore.selectedRun?.current_node
  return nodeLabels[node] || node || '-'
})

const progressStatus = computed(() => {
  if (runStore.selectedRun?.status === 'completed') return 'success'
  if (runStore.selectedRun?.status === 'failed') return 'exception'
  return ''
})

async function refresh() {
  await runStore.fetchRun(runId.value)
  if (runStore.lastError) ElMessage.warning(runStore.lastError)

  if (['completed', 'failed'].includes(runStore.selectedRun?.status)) {
    autoRefresh.value = false
    clearInterval(timer)
    timer = null
  }
}

function toggleAutoRefresh(value) {
  clearInterval(timer)
  timer = null
  if (value) timer = setInterval(refresh, 2000)
}

function openDatasetProfile() {
  router.push({ name: 'dataset-profile', params: { runId: runId.value } })
}

onMounted(async () => {
  await refresh()
  const shouldRefresh = ['created', 'running'].includes(runStore.selectedRun?.status)
  autoRefresh.value = shouldRefresh
  toggleAutoRefresh(shouldRefresh)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="page-stack">
    <PageHeader title="工作流状态" description="查看任务状态、当前节点和最终结果。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
      <template #actions>
        <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleAutoRefresh" />
        <el-button :icon="Refresh" :loading="runStore.loadingRun" @click="refresh">刷新</el-button>
      </template>
    </PageHeader>

    <div class="metric-grid">
      <MetricTile label="状态" :value="runStore.selectedRun?.status || '-'" />
      <MetricTile label="当前阶段" :value="currentStage" />
      <div class="progress-tile">
        <div class="progress-head">
          <span>进度</span>
          <strong>{{ progress }}%</strong>
        </div>
        <el-progress
          :percentage="progress"
          :status="progressStatus"
          :stroke-width="9"
          :show-text="false"
        />
        <div class="progress-message">
          {{ runStore.selectedRun?.progress_message || '等待任务进度更新' }}
        </div>
      </div>
      <MetricTile label="任务类型" :value="runStore.selectedRun?.task_type || '-'" />
    </div>

    <el-alert
      v-if="runStore.selectedRun?.error"
      type="error"
      :title="runStore.selectedRun.error"
      :closable="false"
      show-icon
    />

    <el-card shadow="never" class="result-card">
      <template #header>
        <div class="result-card-head">
          <div>
            <strong>任务结果</strong>
            <span>结构化展示本次工作流产生的数据</span>
          </div>
          <el-button
            v-if="run.task_type === 'dataset_profiling' && run.status === 'completed'"
            type="primary"
            :icon="DataAnalysis"
            @click="openDatasetProfile"
          >
            查看完整数据画像
          </el-button>
        </div>
      </template>

      <div v-if="run.status === 'completed' && Object.keys(result).length" class="result-layout">
        <section class="dataset-result-summary">
          <div class="result-identity">
            <span>DATASET RESULT</span>
            <h2>{{ result.dataset_name || '数据集画像结果' }}</h2>
            <p>{{ result.dataset_path || run.dataset_path || '-' }}</p>
          </div>
          <div class="result-facts">
            <div><span>图像总数</span><strong>{{ result.image_count ?? '-' }}</strong></div>
            <div><span>数据划分</span><strong>{{ Object.keys(splits).length }}</strong></div>
            <div><span>交互图表</span><strong>{{ artifactCounts.charts }}</strong></div>
            <div><span>样本图片</span><strong>{{ artifactCounts.samples }}</strong></div>
          </div>
        </section>

        <section class="split-summary">
          <article v-for="(count, name) in splits" :key="name">
            <span>{{ name }}</span>
            <strong>{{ count }}</strong>
          </article>
        </section>

        <section v-if="observations.length" class="observation-summary">
          <div class="section-heading">
            <div><h3>数据观察</h3><p>Agent 生成的主要结论</p></div>
            <span>{{ observations.length }} 条</span>
          </div>
          <div class="observation-list">
            <div v-for="(item, index) in observations.slice(0, 4)" :key="index">
              <span>{{ index + 1 }}</span>
              <p>{{ item }}</p>
            </div>
          </div>
          <button v-if="observations.length > 4" class="more-result" type="button" @click="openDatasetProfile">
            在数据画像中查看其余 {{ observations.length - 4 }} 条结论
          </button>
        </section>
      </div>

      <div v-else-if="run.status === 'running'" class="result-placeholder">
        <strong>任务仍在执行</strong>
        <span>{{ run.progress_message || '结果生成后将在这里展示' }}</span>
      </div>

      <div v-else class="result-placeholder">
        <strong>暂无可展示结果</strong>
        <span>任务完成后会自动生成结构化摘要。</span>
      </div>

      <el-collapse v-model="expandedSections" class="raw-collapse">
        <el-collapse-item name="raw">
          <template #title>
            <div class="raw-title"><strong>原始 JSON</strong><span>用于核对完整任务状态与返回字段</span></div>
          </template>
          <JsonBlock v-if="expandedSections.includes('raw')" :value="run" />
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<style scoped>
.progress-tile {
  min-height: 108px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.progress-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 15px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
}

.progress-head strong {
  color: var(--text);
  font-size: 22px;
  line-height: 1;
}

.progress-tile :deep(.el-progress-bar__outer) {
  background: #e5e7eb;
}

.progress-tile :deep(.el-progress-bar__inner) {
  background: var(--brand);
  transition: width 0.45s ease;
}

.progress-message {
  margin-top: 11px;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-card :deep(.el-card__body) {
  padding: 0;
}

.result-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.result-card-head > div {
  display: grid;
  gap: 4px;
}

.result-card-head strong {
  color: var(--text);
  font-size: 15px;
}

.result-card-head span,
.raw-title span {
  color: var(--text-muted);
  font-size: 12px;
}

.result-layout {
  display: grid;
  gap: 18px;
  padding: 20px;
}

.dataset-result-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(360px, 1fr);
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.result-identity {
  min-width: 0;
  padding: 22px;
}

.result-identity > span {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 800;
}

.result-identity h2 {
  margin: 8px 0 5px;
  color: var(--text);
  font-size: 21px;
}

.result-identity p {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.result-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border-left: 1px solid var(--line);
  background: var(--surface-soft);
}

.result-facts div {
  display: grid;
  align-content: center;
  gap: 5px;
  min-height: 78px;
  padding: 14px 18px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.result-facts span,
.split-summary span {
  color: var(--text-muted);
  font-size: 12px;
}

.result-facts strong {
  color: var(--text);
  font-size: 18px;
}

.split-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.split-summary article {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 62px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
  transition: border-color 0.18s ease, transform 0.18s ease;
}

.split-summary article:hover {
  border-color: #b6bec9;
  transform: translateY(-1px);
}

.split-summary strong {
  color: var(--text);
  font-size: 19px;
}

.observation-summary {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.section-heading h3 {
  margin: 0;
  color: var(--text);
  font-size: 14px;
}

.section-heading p,
.section-heading > span {
  margin: 3px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.observation-list {
  display: grid;
  gap: 8px;
}

.observation-list > div {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.observation-list > div > span {
  display: grid;
  place-items: center;
  flex: 0 0 22px;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: var(--brand);
  color: #ffffff;
  font-size: 11px;
  font-weight: 800;
}

.observation-list p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.more-result {
  margin-top: 10px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.more-result:hover {
  color: var(--text);
}

.result-placeholder {
  display: grid;
  place-items: center;
  gap: 6px;
  min-height: 180px;
  padding: 20px;
  color: var(--text-muted);
  font-size: 12px;
}

.result-placeholder strong {
  color: var(--text-secondary);
  font-size: 14px;
}

.raw-collapse {
  border-top: 1px solid var(--line);
  border-bottom: 0;
}

.raw-collapse :deep(.el-collapse-item__header) {
  height: auto;
  min-height: 58px;
  padding: 0 20px;
  border-bottom: 0;
}

.raw-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: 0;
}

.raw-collapse :deep(.el-collapse-item__content) {
  padding: 0 20px 20px;
}

.raw-title {
  display: grid;
  gap: 2px;
  text-align: left;
}

@media (max-width: 980px) {
  .dataset-result-summary {
    grid-template-columns: 1fr;
  }

  .result-facts {
    border-top: 1px solid var(--line);
    border-left: 0;
  }
}

@media (max-width: 720px) {
  .result-card-head {
    align-items: stretch;
    flex-direction: column;
  }

  .split-summary,
  .result-facts {
    grid-template-columns: 1fr;
  }
}
</style>
