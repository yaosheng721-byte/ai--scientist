<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import JsonBlock from '../components/JsonBlock.vue'
import PageHeader from '../components/PageHeader.vue'
import { getReport } from '../api/runs'
import { downloadText } from '../utils/format'

const route = useRoute()
const runId = computed(() => String(route.params.runId || ''))
const loading = ref(false)
const report = ref({})
const selectedHypothesis = ref({})
const technicalOpen = ref([])

const metricLabels = {
  image_auroc: 'Image AUROC',
  pixel_auroc: 'Pixel AUROC',
  pro: 'PRO',
  small_defect_pixel_auroc: 'Small Defect Pixel AUROC',
}
const resultRows = computed(() =>
  Object.entries(report.value.results || {}).map(([key, value]) => ({
    label: metricLabels[key] || key,
    baseline: value?.baseline,
    ours: value?.ours,
    delta: Number(value?.ours || 0) - Number(value?.baseline || 0),
  })),
)

const markdown = computed(() => {
  const value = report.value || {}
  return [
    `# ${value.paper_title || 'Final Report'}`,
    '',
    '## Problem Statement',
    value.problem_statement || '',
    '',
    '## Rationale',
    value.rationale || '',
    '',
    '## Technical Details',
    value.technical_details || '',
    '',
    '## Abstract',
    value.paper_abstract || '',
    '',
    '## Methods',
    value.methods || '',
    '',
    '## Results',
    '```json',
    JSON.stringify(value.results || {}, null, 2),
    '```',
    '',
    '## References',
    ...(value.references || []).map((item) => `- ${item.paper_id}: ${item.title}`),
    '',
  ].join('\n')
})

async function fetchReport() {
  loading.value = true
  try {
    const data = await getReport(runId.value)
    report.value = data.report || {}
    selectedHypothesis.value = data.selected_hypothesis || {}
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function downloadMarkdown() {
  downloadText(`${runId.value || 'report'}.md`, markdown.value, 'text/markdown;charset=utf-8')
}

function downloadHtml() {
  const title = report.value.paper_title || 'Report'
  const escaped = markdown.value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title><style>body{max-width:900px;margin:48px auto;padding:0 24px;font:16px/1.75 system-ui;color:#142124}pre{white-space:pre-wrap}</style></head><body><pre>${escaped}</pre></body></html>`
  downloadText(`${runId.value || 'report'}.html`, html, 'text/html;charset=utf-8')
}

onMounted(fetchReport)
</script>

<template>
  <div class="page-stack">
    <PageHeader title="报告预览" description="阅读研究结论、方法和实验结果，并导出可继续编辑的报告文件。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
      <template #actions>
        <el-button :icon="Download" @click="downloadMarkdown">导出 Markdown</el-button>
        <el-button type="primary" :icon="Download" @click="downloadHtml">导出 HTML</el-button>
      </template>
    </PageHeader>

    <article v-loading="loading" class="report-paper">
      <header class="report-cover">
        <span>RESEARCH REPORT</span>
        <h1>{{ report.paper_title || '研究报告尚未生成' }}</h1>
        <div class="report-meta">
          <span>{{ report.datasets?.name || '未指定数据集' }}</span>
          <span>{{ report.experiments?.baseline || '未指定基线' }}</span>
          <span>{{ (report.references || []).length }} 篇参考文献</span>
        </div>
      </header>

      <section class="abstract-section">
        <div class="section-marker">摘要</div>
        <p>{{ report.paper_abstract || '暂无摘要内容。' }}</p>
      </section>

      <div class="report-columns">
        <main class="report-body">
          <section>
            <h2>问题定义</h2>
            <p>{{ report.problem_statement || '暂无内容。' }}</p>
          </section>
          <section>
            <h2>研究依据</h2>
            <p>{{ report.rationale || '暂无内容。' }}</p>
          </section>
          <section>
            <h2>技术方案</h2>
            <p>{{ report.technical_details || '暂无内容。' }}</p>
          </section>
          <section>
            <h2>实验方法</h2>
            <p>{{ report.methods || '暂无内容。' }}</p>
          </section>
        </main>

        <aside class="report-aside">
          <div class="aside-block">
            <span>数据集</span>
            <strong>{{ report.datasets?.name || '-' }}</strong>
            <small>{{ (report.datasets?.categories || []).join('、') || '暂无类别信息' }}</small>
          </div>
          <div class="aside-block">
            <span>评估指标</span>
            <strong>{{ (report.experiments?.metrics || []).length }}</strong>
            <small>{{ (report.experiments?.metrics || []).join(' · ') || '暂无指标' }}</small>
          </div>
          <div v-if="report.source?.url" class="aside-block">
            <span>数据来源</span>
            <strong>{{ report.source.version || 'Source' }}</strong>
            <a :href="report.source.url" target="_blank" rel="noreferrer">查看来源</a>
          </div>
        </aside>
      </div>

      <section v-if="resultRows.length" class="results-section">
        <div class="report-section-head"><div><h2>实验结果</h2><p>当前方法与基线结果对比</p></div></div>
        <div class="result-table">
          <div class="result-row result-header"><span>指标</span><span>Baseline</span><span>当前方法</span><span>提升</span></div>
          <div v-for="item in resultRows" :key="item.label" class="result-row">
            <strong>{{ item.label }}</strong>
            <span>{{ item.baseline ?? '-' }}</span>
            <span>{{ item.ours ?? '-' }}</span>
            <b>{{ item.delta >= 0 ? '+' : '' }}{{ item.delta.toFixed(1) }}</b>
          </div>
        </div>
      </section>

      <section v-if="report.references?.length" class="references-section">
        <div class="report-section-head"><div><h2>参考文献</h2><p>报告中引用的主要研究工作</p></div></div>
        <ol>
          <li v-for="item in report.references" :key="item.paper_id"><span>{{ item.paper_id }}</span>{{ item.title }}</li>
        </ol>
      </section>
    </article>

    <el-collapse v-model="technicalOpen" class="technical-collapse">
      <el-collapse-item v-if="Object.keys(selectedHypothesis).length" title="查看入选假设原始数据" name="hypothesis">
        <JsonBlock :value="selectedHypothesis" />
      </el-collapse-item>
      <el-collapse-item title="查看 Markdown 源文档" name="markdown">
        <JsonBlock :value="markdown" />
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<style scoped>
.report-paper { overflow: hidden; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.report-cover { padding: 34px 38px 28px; border-bottom: 1px solid var(--line); }
.report-cover > span { color: var(--accent); font-size: 11px; font-weight: 800; }
.report-cover h1 { max-width: 1000px; margin: 10px 0 16px; color: var(--text); font-size: 28px; line-height: 1.35; }
.report-meta { display: flex; flex-wrap: wrap; gap: 8px 22px; color: var(--text-muted); font-size: 12px; }
.report-meta span { display: inline-flex; align-items: center; }
.report-meta span:not(:last-child)::after {
  width: 3px;
  height: 3px;
  margin-left: 22px;
  border-radius: 50%;
  background: var(--line-strong);
  content: '';
}
.abstract-section { display: grid; grid-template-columns: 90px minmax(0, 1fr); gap: 24px; padding: 26px 38px; border-bottom: 1px solid var(--line); background: var(--surface-soft); }
.section-marker { color: var(--accent); font-size: 13px; font-weight: 800; }
.abstract-section p { max-width: 950px; margin: 0; color: var(--text-secondary); font-size: 14px; line-height: 1.85; }
.report-columns { display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 46px; padding: 32px 38px; }
.report-body { display: grid; gap: 28px; }
.report-body h2, .report-section-head h2 { margin: 0 0 9px; color: var(--text); font-size: 17px; }
.report-body p { margin: 0; color: var(--text-secondary); font-size: 14px; line-height: 1.9; white-space: pre-line; }
.report-aside { border-left: 1px solid var(--line); }
.aside-block { display: grid; gap: 5px; padding: 0 0 18px 20px; margin-bottom: 18px; border-bottom: 1px solid var(--line); }
.aside-block > span { color: var(--text-muted); font-size: 11px; }
.aside-block strong { color: var(--text); font-size: 15px; }
.aside-block small { color: var(--text-secondary); font-size: 11px; line-height: 1.5; }
.aside-block a { color: var(--accent); font-size: 12px; text-decoration: none; }
.results-section, .references-section { padding: 0 38px 32px; }
.report-section-head p { margin: -4px 0 14px; color: var(--text-muted); font-size: 12px; }
.result-table { border: 1px solid var(--line); border-radius: 8px; }
.result-row { display: grid; grid-template-columns: minmax(180px, 1fr) repeat(3, 120px); align-items: center; min-height: 48px; border-top: 1px solid var(--line); }
.result-row:first-child { border-top: 0; }
.result-row > * { padding: 0 14px; color: var(--text-secondary); font-size: 13px; font-variant-numeric: tabular-nums; }
.result-row > strong { color: var(--text); }
.result-row > b { color: var(--success); }
.result-header { min-height: 40px; background: var(--surface-soft); }
.result-header span { color: var(--text-muted); font-size: 11px; font-weight: 700; }
.references-section ol { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; border-top: 1px solid var(--line); }
.references-section li { display: grid; grid-template-columns: 58px minmax(0, 1fr); gap: 10px; padding: 11px 0; border-bottom: 1px solid var(--line); color: var(--text-secondary); font-size: 13px; line-height: 1.5; }
.references-section li span { color: var(--accent); font-family: Consolas, monospace; font-size: 11px; }
.technical-collapse { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.technical-collapse :deep(.el-collapse-item__header) { padding: 0 16px; }
.technical-collapse :deep(.el-collapse-item__content) { padding: 0 16px 16px; }

@media (max-width: 860px) {
  .report-columns { grid-template-columns: 1fr; gap: 28px; }
  .report-aside { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-left: 0; border-top: 1px solid var(--line); padding-top: 20px; }
  .aside-block { padding-left: 0; padding-right: 16px; border-bottom: 0; border-right: 1px solid var(--line); }
}

@media (max-width: 720px) {
  .report-cover, .report-columns { padding: 24px 20px; }
  .report-cover h1 { font-size: 20px; line-height: 1.42; }
  .report-meta { display: grid; gap: 0; }
  .report-meta span { padding: 5px 0; border-bottom: 1px solid var(--line); }
  .report-meta span:last-child { border-bottom: 0; }
  .report-meta span::after { display: none; }
  .abstract-section { grid-template-columns: 1fr; gap: 8px; padding: 20px; }
  .report-aside { grid-template-columns: 1fr; }
  .aside-block { border-right: 0; border-bottom: 1px solid var(--line); }
  .results-section, .references-section { padding: 0 20px 24px; }
  .result-table { overflow-x: auto; }
  .result-row { min-width: 590px; }
}
</style>
