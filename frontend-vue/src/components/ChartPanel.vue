<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chart: { type: Object, required: true },
})

const el = ref(null)
let chartInstance = null

const option = computed(() => {
  const spec = props.chart || {}
  const data = spec.data || {}
  const labels = data.labels || []
  const series = data.series || []
  const colors = data.colors || series.map((item) => item.color).filter(Boolean)

  if (spec.type === 'pie') {
    return {
      color: colors.length ? colors : ['#0f766e', '#2563eb', '#d97706', '#db6b55'],
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#526169' } },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '43%'],
          avoidLabelOverlap: true,
          data: labels.map((name, index) => ({ name, value: data.values?.[index] || 0 })),
        },
      ],
    }
  }

  const echartsSeries = (series.length ? series : [{ name: 'value', values: data.values || [] }]).map(
    (item) => ({
      name: item.name,
      type: 'bar',
      barMaxWidth: 22,
      itemStyle: { color: item.color || '#0f766e', borderRadius: [3, 3, 0, 0] },
      data: item.values || [],
    }),
  )

  if (spec.orientation === 'h') {
    return {
      color: colors,
      tooltip: { trigger: 'axis' },
      legend: { top: 0, textStyle: { color: '#526169' } },
      grid: { left: 140, right: 20, top: 42, bottom: 34 },
      xAxis: { type: 'value', name: spec.xaxis_title || '', splitLine: { lineStyle: { color: '#e3e9eb' } }, axisLabel: { color: '#66757d' } },
      yAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: '#d4dddf' } }, axisLabel: { color: '#526169' } },
      series: echartsSeries,
    }
  }

  return {
    color: colors,
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { color: '#526169' } },
    grid: { left: 48, right: 24, top: 42, bottom: 42 },
    xAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: '#d4dddf' } }, axisLabel: { color: '#526169' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#e3e9eb' } }, axisLabel: { color: '#66757d' } },
    series: echartsSeries,
  }
})

function render() {
  if (!el.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(el.value)
  }
  chartInstance.setOption(option.value, true)
}

function resize() {
  chartInstance?.resize()
}

onMounted(async () => {
  await nextTick()
  render()
  window.addEventListener('resize', resize)
})

watch(option, () => nextTick(render), { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chartInstance?.dispose()
})
</script>

<template>
  <el-card class="chart-card" shadow="never">
    <div class="chart-title">{{ chart.title || chart.id }}</div>
    <div ref="el" class="chart"></div>
  </el-card>
</template>

<style scoped>
.chart-card {
  min-width: 0;
}

.chart-title {
  margin-bottom: 10px;
  color: var(--text);
  font-size: 14px;
  font-weight: 760;
}

.chart {
  width: 100%;
  height: 320px;
}
</style>
