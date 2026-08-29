<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Document, Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getArtifacts, getReport } from '../api/runs'

const route = useRoute()
const runId = computed(() => String(route.params.runId || ''))
const loading = ref(false)
const artifacts = ref([])
const report = ref({})

const results = computed(() => report.value?.results || {})
const metricLabels = {
  image_auroc: 'Image AUROC',
  pixel_auroc: 'Pixel AUROC',
  pro: 'PRO',
  small_defect_pixel_auroc: 'Small Defect Pixel AUROC',
}
const resultRows = computed(() =>
  Object.entries(results.value).map(([key, value]) => ({
    key,
    label: metricLabels[key] || key,
    baseline: Number(value?.baseline || 0),
    ours: Number(value?.ours || 0),
    delta: Number(value?.ours || 0) - Number(value?.baseline || 0),
  })),
)

function formatScore(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(1) : '-'
}

async function fetchData() {
  loading.value = true
  try {
    const [artifactData, reportData] = await Promise.all([getArtifacts(runId.value), getReport(runId.value)])
    artifacts.value = artifactData.artifacts || []
    report.value = reportData.report || {}
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="page-stack" v-loading="loading">
    <PageHeader title="实验结果" description="对比当前方法与基线的关键指标，查看实验设置、消融项和输出产物。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
    </PageHeader>

    <section v-if="resultRows.length" class="comparison-grid">
      <article v-for="item in resultRows" :key="item.key" class="metric-comparison">
        <div class="metric-head">
          <span>{{ item.label }}</span>
          <strong :class="{ positive: item.delta > 0 }">{{ item.delta >= 0 ? '+' : '' }}{{ formatScore(item.delta) }}</strong>
        </div>
        <div class="metric-values">
          <div><span>当前方法</span><strong>{{ formatScore(item.ours) }}</strong></div>
          <div><span>Baseline</span><strong>{{ formatScore(item.baseline) }}</strong></div>
        </div>
        <div class="comparison-track">
          <i class="baseline" :style="{ width: `${Math.min(100, item.baseline)}%` }" />
          <i class="ours" :style="{ width: `${Math.min(100, item.ours)}%` }" />
        </div>
      </article>
    </section>
    <el-empty v-else-if="!loading" description="当前任务还没有实验指标" />

    <section class="experiment-layout">
      <div class="experiment-settings">
        <div class="section-heading"><div><h2>实验设置</h2><p>用于复现实验的基线、指标和消融配置</p></div></div>
        <dl class="setting-list">
          <div><dt>Baseline</dt><dd>{{ report.experiments?.baseline || '-' }}</dd></div>
          <div><dt>Metrics</dt><dd>{{ (report.experiments?.metrics || []).join(' · ') || '-' }}</dd></div>
        </dl>
        <div class="ablation-block">
          <span>消融实验</span>
          <div class="ablation-list">
            <el-tag v-for="item in report.experiments?.ablation || []" :key="item" effect="plain">{{ item }}</el-tag>
            <small v-if="!report.experiments?.ablation?.length">暂无消融配置</small>
          </div>
        </div>
      </div>

      <div class="artifact-panel">
        <div class="section-heading"><div><h2>输出产物</h2><p>本次任务生成的图表和报告文件</p></div><span>{{ artifacts.length }} 项</span></div>
        <div class="artifact-list">
          <div v-for="item in artifacts" :key="item.path" class="artifact-item">
            <span class="artifact-icon"><el-icon><component :is="item.type === 'final_report' ? Document : Picture" /></el-icon></span>
            <span class="artifact-copy"><strong>{{ item.description || item.type }}</strong><small>{{ item.path }}</small></span>
            <el-tag effect="plain">{{ item.type }}</el-tag>
          </div>
          <el-empty v-if="!artifacts.length && !loading" description="暂无输出产物" :image-size="72" />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.comparison-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.metric-comparison { padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.metric-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.metric-head > span { color: var(--text-secondary); font-size: 12px; font-weight: 700; }
.metric-head > strong { color: var(--text-secondary); font-size: 13px; }
.metric-head > strong.positive { color: var(--success); }
.metric-values { display: flex; align-items: flex-end; gap: 22px; margin: 17px 0 13px; }
.metric-values div { display: grid; gap: 3px; }
.metric-values span { color: var(--text-muted); font-size: 10px; }
.metric-values strong { color: var(--text); font-size: 23px; font-variant-numeric: tabular-nums; }
.metric-values div:last-child strong { color: var(--text-secondary); font-size: 15px; }
.comparison-track { position: relative; height: 9px; }
.comparison-track i { position: absolute; left: 0; display: block; border-radius: 2px; }
.comparison-track .baseline { top: 0; height: 3px; background: #a9b5b8; }
.comparison-track .ours { bottom: 0; height: 4px; background: var(--accent); }
.experiment-layout { display: grid; grid-template-columns: minmax(300px, .75fr) minmax(0, 1.25fr); gap: 14px; }
.experiment-settings, .artifact-panel { padding: 18px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.section-heading h2 { margin: 0; color: var(--text); font-size: 15px; }
.section-heading p, .section-heading > span { margin: 4px 0 0; color: var(--text-muted); font-size: 12px; }
.setting-list { margin: 0; border-top: 1px solid var(--line); }
.setting-list > div { display: grid; grid-template-columns: 88px minmax(0, 1fr); gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line); }
.setting-list dt { color: var(--text-muted); font-size: 11px; }
.setting-list dd { margin: 0; color: var(--text-secondary); font-size: 13px; }
.ablation-block { margin-top: 16px; }
.ablation-block > span { color: var(--text-muted); font-size: 11px; }
.ablation-list { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 9px; }
.ablation-list small { color: var(--text-muted); }
.artifact-list { display: grid; }
.artifact-item { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; padding: 12px 0; border-top: 1px solid var(--line); }
.artifact-icon { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 7px; background: var(--accent-soft); color: var(--accent); }
.artifact-copy { display: grid; gap: 3px; min-width: 0; }
.artifact-copy strong { color: var(--text); font-size: 12px; }
.artifact-copy small { overflow: hidden; color: var(--text-muted); font-family: Consolas, monospace; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 1100px) {
  .comparison-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 820px) {
  .experiment-layout { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .comparison-grid { grid-template-columns: 1fr; }
  .artifact-item { grid-template-columns: auto minmax(0, 1fr); }
  .artifact-item > .el-tag { grid-column: 2; justify-self: start; }
}
</style>
