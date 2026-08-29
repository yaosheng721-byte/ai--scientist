<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import ScoreBadge from '../components/ScoreBadge.vue'
import JsonBlock from '../components/JsonBlock.vue'
import { getResults, submitFeedback } from '../api/runs'
import { averageScore } from '../utils/format'

const route = useRoute()
const runId = computed(() => String(route.params.runId || ''))
const loading = ref(false)
const submitting = ref(false)
const items = ref([])
const comments = ref('')
const selectedId = ref('')
const lastResponse = ref(null)
const responseOpen = ref([])

const selectedItem = computed(() => items.value.find((item) => item.hypothesis_id === selectedId.value))

async function fetchHypotheses() {
  loading.value = true
  try {
    const data = await getResults(runId.value, 'hypothesis')
    items.value = data.items || []
    selectedId.value = items.value[0]?.hypothesis_id || ''
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function review(decision) {
  if (decision === 'approve' && !selectedId.value) {
    ElMessage.warning('请先选择一个候选假设')
    return
  }
  submitting.value = true
  try {
    lastResponse.value = await submitFeedback(runId.value, {
      decision,
      selected_hypothesis_id: decision === 'approve' ? selectedId.value : null,
      comments: comments.value,
    })
    ElMessage.success(decision === 'approve' ? '已提交所选假设' : '已提交重新生成请求')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

onMounted(fetchHypotheses)
</script>

<template>
  <div class="page-stack">
    <PageHeader title="人工选择" description="比较候选假设，选择一个进入后续验证，或驳回本轮结果并要求重新生成。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
    </PageHeader>

    <div v-loading="loading" class="review-layout">
      <section class="candidate-panel">
        <div class="panel-heading">
          <div><h2>候选假设</h2><p>选择后可在右侧确认并填写审核依据</p></div>
          <el-tag effect="plain">{{ items.length }} 项</el-tag>
        </div>

        <button
          v-for="item in items"
          :key="item.hypothesis_id"
          type="button"
          class="candidate-item"
          :class="{ selected: selectedId === item.hypothesis_id }"
          @click="selectedId = item.hypothesis_id"
        >
          <span class="select-indicator" aria-hidden="true"><i /></span>
          <span class="candidate-copy">
            <small>{{ item.hypothesis_id }} · {{ item.source_agent }}</small>
            <strong>{{ item.hypothesis }}</strong>
            <span>{{ item.expected_effect }}</span>
          </span>
          <ScoreBadge :score="averageScore(item.scores)" />
        </button>

        <el-empty v-if="!loading && !items.length" description="当前任务还没有可审核的假设" />
      </section>

      <aside class="decision-panel">
        <div class="panel-heading">
          <div><h2>审核决定</h2><p>本次提交会记录到任务反馈中</p></div>
        </div>

        <div v-if="selectedItem" class="selected-summary">
          <span>已选择</span>
          <strong>{{ selectedItem.hypothesis_id }}</strong>
          <p>{{ selectedItem.hypothesis }}</p>
        </div>
        <div v-else class="selected-summary empty">尚未选择候选假设</div>

        <label class="comment-label" for="review-comments">审核备注</label>
        <el-input id="review-comments" v-model="comments" type="textarea" :rows="5" maxlength="500" show-word-limit placeholder="记录选择依据、风险或需要补充验证的内容" />

        <div class="decision-actions">
          <el-button type="primary" :icon="Check" :disabled="!selectedId" :loading="submitting" @click="review('approve')">
            通过所选假设
          </el-button>
          <el-button :icon="Close" :loading="submitting" @click="review('reject')">驳回并重新生成</el-button>
        </div>

        <p class="integration-note">提交结果由 feedback 接口保存，后续工作流推进状态由编排服务决定。</p>
      </aside>
    </div>

    <el-collapse v-if="lastResponse" v-model="responseOpen" class="response-collapse">
      <el-collapse-item title="查看最近一次接口响应" name="response">
        <JsonBlock :value="lastResponse" />
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<style scoped>
.review-layout { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(300px, .7fr); gap: 14px; align-items: start; }
.candidate-panel, .decision-panel { padding: 18px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.decision-panel { position: sticky; top: 22px; }
.panel-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 14px; }
.panel-heading h2 { margin: 0; color: var(--text); font-size: 15px; }
.panel-heading p { margin: 4px 0 0; color: var(--text-muted); font-size: 12px; }
.candidate-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: start;
  gap: 12px;
  width: 100%;
  margin-top: 8px;
  padding: 15px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color .16s ease, background .16s ease, box-shadow .16s ease;
}
.candidate-item:hover { border-color: var(--line-strong); }
.candidate-item.selected { border-color: #7db8b1; background: #f3faf8; box-shadow: inset 3px 0 0 var(--accent); }
.select-indicator { display: grid; place-items: center; width: 18px; height: 18px; margin-top: 2px; border: 1px solid var(--line-strong); border-radius: 50%; background: var(--surface); }
.candidate-item.selected .select-indicator { border-color: var(--accent); }
.candidate-item.selected .select-indicator i { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.candidate-copy { display: grid; gap: 5px; min-width: 0; }
.candidate-copy small { color: var(--accent); font-family: Consolas, monospace; font-size: 10px; }
.candidate-copy strong { color: var(--text); font-size: 14px; line-height: 1.55; }
.candidate-copy > span { color: var(--text-muted); font-size: 12px; line-height: 1.5; }
.selected-summary { min-height: 118px; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); }
.selected-summary > span { color: var(--text-muted); font-size: 11px; }
.selected-summary > strong { display: block; margin-top: 4px; color: var(--accent); font-family: Consolas, monospace; font-size: 13px; }
.selected-summary p { margin: 8px 0 0; color: var(--text-secondary); font-size: 13px; line-height: 1.6; }
.selected-summary.empty { display: grid; place-items: center; color: var(--text-muted); font-size: 12px; }
.comment-label { display: block; margin: 17px 0 8px; color: var(--text-secondary); font-size: 12px; font-weight: 700; }
.decision-actions { display: grid; gap: 8px; margin-top: 14px; }
.decision-actions .el-button { width: 100%; margin-left: 0; }
.integration-note { margin: 13px 0 0; color: var(--text-muted); font-size: 11px; line-height: 1.55; }
.response-collapse { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.response-collapse :deep(.el-collapse-item__header) { padding: 0 16px; }
.response-collapse :deep(.el-collapse-item__content) { padding: 0 16px 16px; }

@media (max-width: 980px) {
  .review-layout { grid-template-columns: 1fr; }
  .decision-panel { position: static; }
}

@media (max-width: 600px) {
  .candidate-panel, .decision-panel { padding: 14px; }
  .candidate-item { grid-template-columns: auto minmax(0, 1fr); }
  .candidate-item > .score-badge { grid-column: 2; }
}
</style>
