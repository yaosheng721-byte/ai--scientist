<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Search, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import JsonBlock from '../components/JsonBlock.vue'
import PageHeader from '../components/PageHeader.vue'
import { getResults } from '../api/runs'
import { poolTabs } from '../constants/modules'

const route = useRoute()
const runId = computed(() => String(route.params.runId || ''))
const activePool = ref('paper')
const loading = ref(false)
const keyword = ref('')
const data = ref({ items: [], count: 0 })
const detailVisible = ref(false)
const selectedItem = ref(null)

const poolMeta = {
  paper: { title: '论文资料', description: '检索与研究问题相关的论文、发表信息和相关度。' },
  fact: { title: '事实证据', description: '查看从论文中提取的事实、来源和置信度。' },
  gap: { title: '研究空白', description: '归纳现有方法尚未解决的问题与空白类型。' },
  hypothesis: { title: '候选假设', description: '汇总不同 Agent 生成的可检验研究假设。' },
  review: { title: '评审记录', description: '查看候选假设的评审来源和评分结果。' },
}

const currentMeta = computed(() => poolMeta[activePool.value])
const filteredItems = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return data.value.items || []
  return (data.value.items || []).filter((item) => JSON.stringify(item).toLowerCase().includes(query))
})

async function fetchPool() {
  loading.value = true
  keyword.value = ''
  try {
    data.value = await getResults(runId.value, activePool.value)
  } catch (error) {
    ElMessage.error(error.message)
    data.value = { items: [], count: 0 }
  } finally {
    loading.value = false
  }
}

function openDetail(item) {
  selectedItem.value = item
  detailVisible.value = true
}

watch(activePool, fetchPool)
onMounted(fetchPool)
</script>

<template>
  <div class="page-stack">
    <PageHeader title="研究结果池" description="集中浏览研究链路产生的论文、证据、空白、假设和评审记录。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
    </PageHeader>

    <section class="pool-surface">
      <el-tabs v-model="activePool" class="pool-tabs">
        <el-tab-pane v-for="tab in poolTabs" :key="tab.value" :label="tab.label" :name="tab.value" />
      </el-tabs>

      <div class="pool-heading">
        <div>
          <h2>{{ currentMeta.title }}</h2>
          <p>{{ currentMeta.description }}</p>
        </div>
        <el-tag effect="plain">{{ filteredItems.length }} / {{ data.count || 0 }} 条</el-tag>
      </div>

      <div class="pool-tools">
        <el-input v-model="keyword" :prefix-icon="Search" clearable placeholder="搜索当前结果池" />
      </div>

      <el-table v-if="filteredItems.length || loading" v-loading="loading" :data="filteredItems" class="pool-table">
        <el-table-column type="index" label="#" width="58" />
        <el-table-column v-if="activePool === 'paper'" prop="title" label="论文标题" min-width="340" show-overflow-tooltip />
        <el-table-column v-if="activePool === 'paper'" prop="venue" label="发表场所" width="130" />
        <el-table-column v-if="activePool === 'paper'" prop="year" label="年份" width="88" />
        <el-table-column v-if="activePool === 'paper'" label="相关度" width="110">
          <template #default="{ row }"><strong class="numeric">{{ Math.round(Number(row.relevance_score || 0) * 100) }}%</strong></template>
        </el-table-column>

        <el-table-column v-if="activePool === 'fact'" prop="claim" label="事实内容" min-width="360" show-overflow-tooltip />
        <el-table-column v-if="activePool === 'fact'" prop="source_paper_id" label="来源论文" width="120" />
        <el-table-column v-if="activePool === 'fact'" prop="confidence" label="置信度" width="110" />

        <el-table-column v-if="activePool === 'gap'" prop="description" label="研究空白" min-width="360" show-overflow-tooltip />
        <el-table-column v-if="activePool === 'gap'" prop="gap_type" label="空白类型" width="150" />

        <el-table-column v-if="activePool === 'hypothesis'" prop="hypothesis" label="候选假设" min-width="420" show-overflow-tooltip />
        <el-table-column v-if="activePool === 'hypothesis'" prop="source_agent" label="生成来源" width="150" />

        <el-table-column v-if="activePool === 'review'" prop="hypothesis_id" label="假设编号" width="130" />
        <el-table-column v-if="activePool === 'review'" prop="reviewer_type" label="评审来源" width="150" />
        <el-table-column v-if="activePool === 'review'" prop="score" label="评分" width="90" />

        <el-table-column label="详情" width="82" fixed="right">
          <template #default="{ row }">
            <el-button text :icon="View" aria-label="查看完整记录" @click="openDetail(row)" />
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="当前结果池没有匹配内容">
        <el-button v-if="keyword" @click="keyword = ''">清除搜索</el-button>
      </el-empty>
    </section>

    <el-drawer v-model="detailVisible" title="完整记录" size="min(520px, 92vw)">
      <JsonBlock :value="selectedItem || {}" />
    </el-drawer>
  </div>
</template>

<style scoped>
.pool-surface {
  min-width: 0;
  overflow: hidden;
  padding: 0 20px 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.pool-tabs { min-width: 0; }
.pool-tabs :deep(.el-tabs__header) { margin-bottom: 0; }

.pool-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 0 16px;
}

.pool-heading h2 { margin: 0; color: var(--text); font-size: 17px; }
.pool-heading p { margin: 5px 0 0; color: var(--text-muted); font-size: 12px; }
.pool-tools { width: min(360px, 100%); margin-bottom: 14px; }
.pool-table { border: 1px solid var(--line); border-radius: 8px; }
.numeric { color: var(--accent); font-variant-numeric: tabular-nums; }

@media (max-width: 720px) {
  .pool-surface { padding: 0 14px 14px; }
  .pool-heading { align-items: flex-start; flex-direction: column; }
  .pool-tabs :deep(.el-tabs__nav-scroll) { overflow-x: auto; scrollbar-width: none; }
  .pool-tabs :deep(.el-tabs__nav-next), .pool-tabs :deep(.el-tabs__nav-prev) { display: none; }
}
</style>
