<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import ScoreBadge from '../components/ScoreBadge.vue'
import { getResults } from '../api/runs'
import { averageScore } from '../utils/format'

const route = useRoute()
const runId = computed(() => String(route.params.runId || ''))
const loading = ref(false)
const items = ref([])

const scoreLabels = {
  novelty: '创新性',
  feasibility: '可行性',
  evidence: '证据强度',
  reproducibility: '可复现性',
}

const rankedItems = computed(() =>
  [...items.value]
    .map((item) => ({ ...item, average: averageScore(item.scores) }))
    .sort((a, b) => b.average - a.average),
)
const totalAverage = computed(() => {
  if (!rankedItems.value.length) return 0
  return Math.round(rankedItems.value.reduce((sum, item) => sum + item.average, 0) / rankedItems.value.length)
})
const topItem = computed(() => rankedItems.value[0] || {})

async function fetchHypotheses() {
  loading.value = true
  try {
    const data = await getResults(runId.value, 'hypothesis')
    items.value = data.items || []
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

onMounted(fetchHypotheses)
</script>

<template>
  <div class="page-stack">
    <PageHeader title="候选假设评分" description="比较候选假设的综合表现和各评分维度，快速识别优先验证方向。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
    </PageHeader>

    <section class="score-summary">
      <div><span>候选数量</span><strong>{{ rankedItems.length }}</strong></div>
      <div><span>平均得分</span><strong>{{ totalAverage }}</strong></div>
      <div class="top-summary"><span>当前最高分</span><strong>{{ topItem.hypothesis_id || '-' }} · {{ topItem.average || 0 }}</strong></div>
    </section>

    <div v-loading="loading" class="score-list">
      <article v-for="(item, index) in rankedItems" :key="item.hypothesis_id" class="score-card">
        <div class="rank">{{ String(index + 1).padStart(2, '0') }}</div>
        <div class="score-head">
          <div>
            <div class="score-id">{{ item.hypothesis_id }} · {{ item.source_agent }}</div>
            <h2>{{ item.hypothesis }}</h2>
          </div>
          <div class="overall-score">
            <span>综合得分</span>
            <ScoreBadge :score="item.average" />
          </div>
        </div>

        <p class="mechanism">{{ item.mechanism }}</p>

        <div class="score-grid">
          <div v-for="(score, key) in item.scores" :key="key" class="score-item">
            <div><span>{{ scoreLabels[key] || key }}</span><strong>{{ score }}</strong></div>
            <div class="score-track"><i :style="{ width: `${Math.max(0, Math.min(100, Number(score) || 0))}%` }" /></div>
          </div>
        </div>

        <el-collapse class="detail-collapse">
          <el-collapse-item title="查看验证条件与风险" name="details">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="预期效果">{{ item.expected_effect || '-' }}</el-descriptions-item>
              <el-descriptions-item label="测试方法">{{ item.test_method || '-' }}</el-descriptions-item>
              <el-descriptions-item label="所需数据">{{ (item.required_data || []).join('、') || '-' }}</el-descriptions-item>
              <el-descriptions-item label="风险">{{ (item.risks || []).join('；') || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-collapse-item>
        </el-collapse>
      </article>

      <el-empty v-if="!loading && !rankedItems.length" description="当前任务还没有候选假设" />
    </div>
  </div>
</template>

<style scoped>
.score-summary {
  display: grid;
  grid-template-columns: 160px 160px minmax(0, 1fr);
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.score-summary > div {
  display: grid;
  gap: 5px;
  padding: 16px 18px;
  border-right: 1px solid var(--line);
}

.score-summary > div:last-child { border-right: 0; }
.score-summary span { color: var(--text-muted); font-size: 12px; }
.score-summary strong { color: var(--text); font-size: 20px; }
.score-summary .top-summary strong { color: var(--accent); font-size: 15px; }
.score-list { display: grid; gap: 12px; }

.score-card {
  position: relative;
  overflow: hidden;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  transition: border-color .16s ease, box-shadow .16s ease;
}

.score-card:hover { border-color: var(--line-strong); box-shadow: var(--shadow-sm); }
.rank { position: absolute; top: 13px; right: 16px; color: #b5c0c5; font-family: Consolas, monospace; font-size: 11px; }
.score-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; padding-right: 28px; }
.score-id { color: var(--accent); font-family: Consolas, monospace; font-size: 11px; font-weight: 700; }
.score-head h2 { max-width: 900px; margin: 7px 0 0; color: var(--text); font-size: 17px; line-height: 1.55; }
.overall-score { display: grid; flex: 0 0 auto; justify-items: end; gap: 6px; }
.overall-score > span { color: var(--text-muted); font-size: 11px; }
.mechanism { margin: 13px 0 16px; color: var(--text-secondary); font-size: 13px; line-height: 1.7; }
.score-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 9px; }
.score-item { padding: 11px 12px; border: 1px solid var(--line); border-radius: 7px; background: var(--surface-soft); }
.score-item > div:first-child { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.score-item span { color: var(--text-secondary); font-size: 12px; }
.score-item strong { color: var(--text); font-size: 14px; }
.score-track { height: 4px; margin-top: 9px; overflow: hidden; border-radius: 2px; background: #dfe7e8; }
.score-track i { display: block; height: 100%; border-radius: inherit; background: var(--accent); transition: width .45s ease; }
.detail-collapse { margin-top: 14px; border-bottom: 0; }
.detail-collapse :deep(.el-collapse-item__header) { min-height: 44px; border-top: 1px solid var(--line); color: var(--text-secondary); font-size: 12px; }
.detail-collapse :deep(.el-collapse-item__wrap) { border-bottom: 0; }

@media (max-width: 900px) {
  .score-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 720px) {
  .score-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .score-summary .top-summary { grid-column: 1 / -1; border-top: 1px solid var(--line); }
  .score-head { flex-direction: column; padding-right: 0; }
  .overall-score { justify-items: start; }
  .score-grid { grid-template-columns: 1fr; }
  .score-card { padding: 17px; }
}
</style>
