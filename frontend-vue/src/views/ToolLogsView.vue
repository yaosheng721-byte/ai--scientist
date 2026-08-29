<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import JsonBlock from '../components/JsonBlock.vue'
import MetricTile from '../components/MetricTile.vue'
import PageHeader from '../components/PageHeader.vue'
import { getToolCalls } from '../api/runs'

const route = useRoute()
const runId = computed(() => String(route.params.runId || ''))
const loading = ref(false)
const calls = ref([])

const successCount = computed(() => calls.value.filter((item) => item.status === 'success').length)
const duration = computed(() =>
  calls.value.reduce((sum, item) => sum + Number(item.duration_sec || 0), 0).toFixed(2),
)

async function fetchLogs() {
  loading.value = true
  try {
    const data = await getToolCalls(runId.value)
    calls.value = data.tool_calls || []
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<template>
  <div class="page-stack">
    <PageHeader title="工具执行日志" description="查看工具调用输入、输出、状态、耗时和错误。" :run-id="runId" back>
      <template #kicker>{{ runId }}</template>
      <template #actions>
        <el-button :icon="Refresh" :loading="loading" @click="fetchLogs">刷新</el-button>
      </template>
    </PageHeader>

    <div class="metric-grid">
      <MetricTile label="调用次数" :value="calls.length" />
      <MetricTile label="成功次数" :value="successCount" />
      <MetricTile label="总耗时" :value="`${duration}s`" />
      <MetricTile label="失败次数" :value="calls.length - successCount" />
    </div>

    <el-table v-loading="loading" :data="calls" border>
      <el-table-column prop="tool_name" label="Tool" min-width="180" />
      <el-table-column prop="status" label="Status" width="110">
        <template #default="{ row }">
          <el-tag :type="row.status === 'success' ? 'success' : 'danger'" effect="plain">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="duration_sec" label="Duration" width="110" />
      <el-table-column prop="output_summary" label="Output" min-width="320" show-overflow-tooltip />
      <el-table-column prop="timestamp" label="Time" width="190" />
      <el-table-column label="Input" width="96" fixed="right">
        <template #default="{ row }">
          <el-popover trigger="click" width="520">
            <JsonBlock :value="row.input || {}" />
            <template #reference>
              <el-button text>查看</el-button>
            </template>
          </el-popover>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
