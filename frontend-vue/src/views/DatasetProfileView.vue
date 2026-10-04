<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Picture, Refresh, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ChartPanel from '../components/ChartPanel.vue'
import JsonBlock from '../components/JsonBlock.vue'
import MetricTile from '../components/MetricTile.vue'
import PageHeader from '../components/PageHeader.vue'
import { useRunStore } from '../stores/runStore'
import { getDatasetName } from '../utils/format'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()
const runId = computed(() => String(route.params.runId || ''))
const creating = ref(false)
const autoRefresh = ref(false)
const activeTab = ref('overview')
const runOptions = ref([])
let timer = null

const form = reactive({
  dataset_path: 'app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle',
})

const result = computed(() => runStore.selectedRun?.result || {})
const artifacts = computed(() => result.value?.artifacts || {})
const charts = computed(() => artifacts.value?.interactive_charts || [])
const samples = computed(() => artifacts.value?.sample_images || [])
const observations = computed(() => result.value?.observations || [])
const splits = computed(() => result.value?.splits || {})
const splitRows = computed(() => {
  const total = Object.values(splits.value).reduce((sum, count) => sum + Number(count || 0), 0)
  return Object.entries(splits.value).map(([name, count]) => ({
    name,
    count,
    ratio: total ? Math.round((Number(count) / total) * 100) : 0,
  }))
})
const qualityRows = computed(() => flattenDatasetGroups(result.value?.quality_statistics, (item) => ({
  imageCount: item.num_images,
  blur: item.quality_statistics?.blur_score_mean,
  brightness: item.quality_statistics?.brightness_mean,
  noise: item.quality_statistics?.noise_score_mean,
})))
const analysisRows = computed(() => flattenDatasetGroups(result.value?.image_analysis, (item) => ({
  imageCount: item.num_images,
  widthMean: item.image_size_distribution?.width_mean,
  heightMean: item.image_size_distribution?.height_mean,
  widthRange: formatRange(item.image_size_distribution?.width_min, item.image_size_distribution?.width_max),
  heightRange: formatRange(item.image_size_distribution?.height_min, item.image_size_distribution?.height_max),
  defectMean: item.defect_ratio?.mean,
  defectMin: item.defect_ratio?.min,
  defectMax: item.defect_ratio?.max,
  maskCount: item.defect_ratio?.mask_count ?? 0,
  hasMask: Boolean(item.defect_ratio?.has_mask),
})))
const classRows = computed(() => Object.entries(result.value?.class_distribution || {}).map(([name, count]) => ({ name, count })))
const categoryRows = computed(() => Object.entries(result.value?.category_distribution || {}).flatMap(([split, categories]) =>
  Object.entries(categories || {}).map(([category, count]) => ({ split, category, count })),
))
const fileRows = computed(() => {
  const fileSplits = artifacts.value?.file_tree?.splits || {}
  return Object.entries(fileSplits).flatMap(([split, groups]) =>
    Object.entries(groups || {}).map(([category, files]) => ({
      id: `${split}/${category}`,
      split,
      category,
      files: Array.isArray(files) ? files : [],
    })),
  )
})
const sourceGroups = computed(() => [
  { label: '图像目录', values: result.value?.image_dirs || [] },
  { label: '标注文件', values: result.value?.annotation_files || [] },
  { label: 'Mask 目录', values: result.value?.mask_dirs || [] },
])
const annotationFormat = computed(() => {
  const value = result.value?.annotation_format
  if (Array.isArray(value)) return value.join(', ') || '-'
  return value || '-'
})

function flattenDatasetGroups(groups, mapper) {
  return Object.entries(groups || {}).flatMap(([split, categories]) =>
    Object.entries(categories || {}).map(([category, item]) => ({
      id: `${split}/${category}`,
      split,
      category,
      path: item.path,
      ...mapper(item),
    })),
  )
}

function formatNumber(value, digits = 2) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '-'
  return number.toFixed(digits).replace(/\.00$/, '')
}

function formatPercent(value) {
  if (value == null || value === '') return '-'
  const number = Number(value)
  return Number.isFinite(number) ? `${(number * 100).toFixed(2)}%` : '-'
}

function formatRange(min, max) {
  if (min == null || max == null) return '-'
  return `${formatNumber(min, 0)}–${formatNumber(max, 0)}`
}

const apiBase = import.meta.env.VITE_API_BASE || '/api'

function sampleMediaUrl(index, kind) {
  return `${apiBase}/runs/${encodeURIComponent(runId.value)}/samples/${index}/${kind}`
}

function fileName(path) {
  if (!path) return '-'
  return String(path).split(/[\\/]/).pop() || path
}

async function refresh() {
  if (!runId.value) return
  await runStore.fetchRun(runId.value)
  if (runStore.lastError) ElMessage.warning(runStore.lastError)
}

async function runProfiling() {
  creating.value = true
  try {
    const data = await runStore.create({
      query: 'dataset profiling',
      task_type: 'dataset_profiling',
      dataset_path: form.dataset_path,
    })
    ElMessage.success('Dataset Profiling 任务已创建')
    router.push({ name: 'dataset-profile', params: { runId: data.run_id } })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    creating.value = false
  }
}

function toggleAutoRefresh(value) {
  clearInterval(timer)
  timer = null
  if (value) timer = setInterval(refresh, 2000)
}

onMounted(refresh)
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="page-stack">
    <PageHeader
      title="数据集画像"
      description="运行 Dataset Profiling Agent，查看扫描、标注、图像质量和可视化产物。"
      :run-id="runId"
      back
    >
      <template #kicker>{{ runId }}</template>
      <template #actions>
        <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleAutoRefresh" />
        <el-button :icon="Refresh" :loading="runStore.loadingRun" @click="refresh">刷新</el-button>
      </template>
    </PageHeader>

    <div class="metric-grid">
      <MetricTile label="状态" :value="runStore.selectedRun?.status || '-'" />
      <MetricTile label="图像总数" :value="result.image_count ?? '-'" :hint="getDatasetName(result.dataset_path)" />
      <MetricTile label="划分数量" :value="Object.keys(splits).length" :hint="Object.keys(splits).join(', ') || '-'" />
      <MetricTile label="标注格式" :value="annotationFormat" :hint="`${result.valid_annotation_count ?? 0} 个有效文件`" />
    </div>

    <el-alert
      v-if="runStore.selectedRun?.status === 'running'"
      title="Agent 正在运行，开启自动刷新可以实时查看结果。"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-alert
      v-if="runStore.selectedRun?.error"
      type="error"
      :title="runStore.selectedRun.error"
      :closable="false"
      show-icon
    />

    <el-alert
      v-if="result.observation_warning"
      type="warning"
      :title="result.observation_warning"
      :closable="false"
      show-icon
    />

    <el-alert
      v-for="(warning, index) in (artifacts.warnings || [])"
      :key="`artifact-warning-${index}`"
      type="warning"
      :title="warning"
      :closable="false"
      show-icon
    />

    <el-collapse v-model="runOptions" class="run-options">
      <el-collapse-item name="rerun">
        <template #title>
          <div class="run-options-title">
            <strong>使用其它数据集重新运行</strong>
            <span>展开后修改数据集路径并创建新的 Dataset Profiling 任务</span>
          </div>
        </template>
        <div class="run-panel">
          <el-input v-model="form.dataset_path" placeholder="请输入数据集路径" />
          <el-button type="primary" :icon="VideoPlay" :loading="creating" @click="runProfiling">
            运行 Agent
          </el-button>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-tabs v-model="activeTab" class="profile-tabs">
      <el-tab-pane label="概览" name="overview">
        <div class="overview-stack">
          <section class="dataset-summary">
            <div class="dataset-identity">
              <span class="summary-eyebrow">DATASET PROFILE</span>
              <h2>{{ result.dataset_name || getDatasetName(result.dataset_path) || '未命名数据集' }}</h2>
              <p>{{ result.dataset_path || '-' }}</p>
            </div>
            <div class="summary-facts">
              <div><span>图像格式</span><strong>{{ (result.image_extensions || []).join(', ') || '-' }}</strong></div>
              <div><span>图像目录</span><strong>{{ (result.image_dirs || []).length }}</strong></div>
              <div><span>Mask 目录</span><strong>{{ (result.mask_dirs || []).length }}</strong></div>
              <div><span>标注文件</span><strong>{{ result.annotation_file_count ?? 0 }}</strong></div>
            </div>
          </section>

          <section v-if="observations.length" class="observation-panel">
            <div class="subsection-head">
              <div><h3>数据观察</h3><p>Agent 从扫描和质量分析中提取的关键结论</p></div>
              <span class="observation-count">{{ observations.length }} 条</span>
            </div>
            <div class="observations">
              <div v-for="(item, index) in observations" :key="index" class="observation-item">
                <span>{{ String(index + 1).padStart(2, '0') }}</span>
                <p>{{ item }}</p>
              </div>
            </div>
          </section>

          <section>
            <div class="subsection-head">
              <div><h3>数据划分</h3><p>各数据分区的图像数量及占比</p></div>
            </div>
            <div class="split-grid">
              <article v-for="item in splitRows" :key="item.name" class="split-card">
                <div><strong>{{ item.name }}</strong><span>{{ item.ratio }}%</span></div>
                <b>{{ item.count }}</b>
                <div class="ratio-track"><i :style="{ width: `${item.ratio}%` }" /></div>
              </article>
            </div>
          </section>

          <section class="detail-grid">
            <div class="detail-panel">
              <div class="subsection-head">
                <div><h3>资源清单</h3><p>扫描得到的目录和标注来源</p></div>
              </div>
              <div class="resource-list">
                <div v-for="group in sourceGroups" :key="group.label" class="resource-row">
                  <span>{{ group.label }}</span>
                  <strong>{{ group.values.length }}</strong>
                  <el-tooltip v-if="group.values.length" :content="group.values.join('\n')" placement="top">
                    <small>{{ fileName(group.values[0]) }}</small>
                  </el-tooltip>
                  <small v-else>无</small>
                </div>
              </div>
            </div>

            <div class="detail-panel">
              <div class="subsection-head">
                <div><h3>分布差异</h3><p>训练集与测试集的统计差值</p></div>
              </div>
              <div class="difference-grid">
                <div><span>平均宽度差</span><strong>{{ formatNumber(result.distribution_difference?.width_mean_difference) }}</strong></div>
                <div><span>平均高度差</span><strong>{{ formatNumber(result.distribution_difference?.height_mean_difference) }}</strong></div>
                <div><span>缺陷占比差</span><strong>{{ formatPercent(result.distribution_difference?.defect_ratio_difference) }}</strong></div>
              </div>
            </div>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="交互图表" name="charts" lazy>
        <div v-if="charts.length" class="content-grid">
          <ChartPanel v-for="chart in charts" :key="chart.id || chart.title" :chart="chart" />
        </div>
        <div v-else class="empty-panel">暂无图表数据</div>
      </el-tab-pane>

      <el-tab-pane label="图像质量" name="quality" lazy>
        <el-table v-if="qualityRows.length" :data="qualityRows" stripe class="data-table">
          <el-table-column prop="split" label="数据划分" width="110" />
          <el-table-column prop="category" label="类别" min-width="150" />
          <el-table-column prop="imageCount" label="图像数" width="100" align="right" />
          <el-table-column label="清晰度" min-width="130" align="right">
            <template #default="scope">{{ formatNumber(scope.row.blur) }}</template>
          </el-table-column>
          <el-table-column label="亮度" min-width="130" align="right">
            <template #default="scope">{{ formatNumber(scope.row.brightness, 4) }}</template>
          </el-table-column>
          <el-table-column label="噪声" min-width="130" align="right">
            <template #default="scope">{{ formatNumber(scope.row.noise, 4) }}</template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-panel">暂无图像质量数据</div>
      </el-tab-pane>

      <el-tab-pane label="图像分析" name="analysis" lazy>
        <el-table v-if="analysisRows.length" :data="analysisRows" stripe class="data-table">
          <el-table-column prop="split" label="数据划分" width="100" />
          <el-table-column prop="category" label="类别" min-width="140" />
          <el-table-column prop="imageCount" label="图像数" width="90" align="right" />
          <el-table-column label="平均尺寸" min-width="130">
            <template #default="scope">{{ formatNumber(scope.row.widthMean, 0) }} × {{ formatNumber(scope.row.heightMean, 0) }}</template>
          </el-table-column>
          <el-table-column prop="widthRange" label="宽度范围" min-width="120" />
          <el-table-column prop="heightRange" label="高度范围" min-width="120" />
          <el-table-column label="平均缺陷占比" min-width="140" align="right">
            <template #default="scope"><strong class="table-emphasis">{{ scope.row.maskCount ? formatPercent(scope.row.defectMean) : '无有效 Mask' }}</strong></template>
          </el-table-column>
          <el-table-column label="Mask" width="90" align="center">
            <template #default="scope"><el-tag :type="scope.row.maskCount ? 'success' : 'info'" effect="plain">{{ scope.row.maskCount ? `${scope.row.maskCount} 张` : (scope.row.hasMask ? '未匹配' : '无') }}</el-tag></template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-panel">暂无图像分析数据</div>
      </el-tab-pane>

      <el-tab-pane label="标注" name="annotation" lazy>
        <div class="annotation-layout">
          <section class="annotation-metrics">
            <div><span>标注格式</span><strong>{{ annotationFormat }}</strong></div>
            <div><span>标注文件</span><strong>{{ result.annotation_file_count ?? 0 }}</strong></div>
            <div><span>有效文件</span><strong>{{ result.valid_annotation_count ?? 0 }}</strong></div>
            <div><span>小目标占比</span><strong>{{ result.bbox_statistics?.total_bbox ? formatPercent(result.small_object_ratio) : '无边界框标注' }}</strong></div>
          </section>
          <el-alert
            v-if="result.annotation_errors?.length"
            type="warning"
            :title="`有 ${result.invalid_annotation_count} 个标注文件未能解析；下方列出原因。有效文件数只统计通过校验的文件。`"
            :closable="false"
            show-icon
          />
          <el-alert
            v-for="(item, index) in (result.annotation_errors || [])"
            :key="`annotation-error-${index}`"
            type="error"
            :title="`${fileName(item.file)}（${item.format}）：${item.error}`"
            :closable="false"
            show-icon
          />
          <el-alert
            v-for="(item, index) in (result.annotation_warnings || [])"
            :key="`annotation-warning-${index}`"
            type="info"
            :title="`${item.count} 个文件：${item.warning}${item.files?.length ? `（例如：${item.files.join('、')}）` : ''}`"
            :closable="false"
            show-icon
          />
          <section class="bbox-panel">
            <div class="subsection-head"><div><h3>边界框统计</h3><p>{{ result.bbox_statistics?.total_bbox ? '通过校验的边界框面积统计' : (result.valid_annotation_count ? '标注文件通过校验，但没有目标框' : '未发现有效框标注；Mask 缺陷面积见图像分析页') }}</p></div></div>
            <div class="difference-grid">
              <div><span>总数</span><strong>{{ result.valid_annotation_count ? (result.bbox_statistics?.total_bbox ?? 0) : '未提供' }}</strong></div>
              <div><span>平均面积</span><strong>{{ result.valid_annotation_count ? formatNumber(result.bbox_statistics?.mean_area) : '未提供' }}</strong></div>
              <div><span>面积范围</span><strong>{{ result.valid_annotation_count ? formatRange(result.bbox_statistics?.min_area, result.bbox_statistics?.max_area) : '未提供' }}</strong></div>
            </div>
          </section>
          <section class="class-panel">
            <div class="subsection-head"><div><h3>目录类别分布</h3><p>按 train/test/val 下的类别目录统计图片数；不等同于目标框类别</p></div></div>
            <el-table v-if="categoryRows.length" :data="categoryRows" stripe>
              <el-table-column prop="split" label="数据划分" />
              <el-table-column prop="category" label="目录类别" />
              <el-table-column prop="count" label="图片数" align="right" />
            </el-table>
            <div v-else class="compact-empty">未识别到按类别分组的目录</div>
            <div class="subsection-head annotation-subhead"><div><h3>目标框类别</h3><p>仅由有效的 COCO/VOC/YOLO 框标注解析得到</p></div></div>
            <el-table v-if="classRows.length" :data="classRows" stripe>
              <el-table-column prop="name" label="类别" />
              <el-table-column prop="count" label="数量" align="right" />
            </el-table>
            <div v-else class="compact-empty">没有可用的目标框类别标注；这不代表没有异常类别或 Mask</div>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="样本图片" name="samples" lazy>
        <div v-if="samples.length" class="sample-grid">
          <article v-for="(sample, index) in samples" :key="`${sample.title}-${index}`" class="sample-card">
            <div class="sample-card-head">
              <div><h3>{{ sample.title || `样本 ${index + 1}` }}</h3><span>{{ fileName(sample.image_path) }}</span></div>
              <span class="sample-index">{{ String(index + 1).padStart(2, '0') }}</span>
            </div>
            <div class="sample-media" :class="{ 'with-mask': sample.mask_path }">
              <figure>
                <el-image :src="sampleMediaUrl(index, 'image')" :preview-src-list="[sampleMediaUrl(index, 'image')]" fit="cover" loading="lazy" preview-teleported>
                  <template #error><div class="image-error"><el-icon><Picture /></el-icon><span>图像加载失败</span></div></template>
                </el-image>
                <figcaption>原图</figcaption>
              </figure>
              <figure v-if="sample.mask_path">
                <el-image :src="sampleMediaUrl(index, 'mask')" :preview-src-list="[sampleMediaUrl(index, 'mask')]" fit="cover" loading="lazy" preview-teleported>
                  <template #error><div class="image-error"><el-icon><Picture /></el-icon><span>Mask 加载失败</span></div></template>
                </el-image>
                <figcaption>Mask · {{ fileName(sample.mask_path) }}</figcaption>
              </figure>
            </div>
          </article>
        </div>
        <div v-else class="empty-panel">暂无样本数据</div>
      </el-tab-pane>

      <el-tab-pane label="文件索引" name="files" lazy>
        <div class="file-index-note">图片文件默认折叠，仅展示目录分组和文件数量。点击行首箭头查看具体文件。</div>
        <el-table v-if="fileRows.length" :data="fileRows" row-key="id" stripe class="data-table">
          <el-table-column type="expand">
            <template #default="scope">
              <div class="file-list">
                <span v-for="file in scope.row.files" :key="file">{{ file }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="split" label="数据划分" min-width="140" />
          <el-table-column prop="category" label="类别目录" min-width="220" />
          <el-table-column label="图片文件数" width="140" align="right">
            <template #default="scope"><strong>{{ scope.row.files.length }}</strong></template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-panel">暂无文件索引</div>
      </el-tab-pane>

      <el-tab-pane label="原始 JSON" name="raw" lazy>
        <div class="raw-json-head"><strong>完整任务结果</strong><span>保留原始数据用于核对与调试</span></div>
        <JsonBlock :value="result || {}" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.run-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  padding: 0 2px 16px;
}

.run-options {
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.run-options :deep(.el-collapse-item__header) {
  height: auto;
  min-height: 54px;
  padding: 0 4px;
  background: transparent;
}

.run-options :deep(.el-collapse-item__wrap) {
  background: transparent;
}

.run-options :deep(.el-collapse-item__content) {
  padding-bottom: 0;
}

.run-options-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
  text-align: left;
}

.run-options-title strong {
  color: var(--text-secondary);
  font-size: 13px;
}

.run-options-title span {
  color: var(--text-muted);
  font-size: 12px;
}

.profile-tabs {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  padding: 0 2px;
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 18px;
}

.profile-tabs :deep(.el-tabs__nav-wrap),
.profile-tabs :deep(.el-tabs__nav-scroll),
.profile-tabs :deep(.el-tabs__content),
.profile-tabs :deep(.el-tab-pane) {
  min-width: 0;
  max-width: 100%;
}

.overview-stack {
  display: grid;
  gap: 22px;
}

.dataset-summary {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(380px, 1fr);
  align-items: stretch;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.dataset-summary::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--accent);
  content: '';
}

.dataset-identity {
  min-width: 0;
  padding: 24px;
}

.summary-eyebrow {
  color: var(--accent);
  font-size: 11px;
  font-weight: 800;
}

.dataset-identity h2 {
  margin: 8px 0 6px;
  font-size: 22px;
}

.dataset-identity p {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.summary-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border-left: 1px solid var(--line);
  background: var(--surface-soft);
}

.summary-facts div {
  display: grid;
  align-content: center;
  gap: 5px;
  min-height: 76px;
  padding: 14px 18px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.summary-facts span,
.difference-grid span,
.annotation-metrics span {
  color: var(--text-muted);
  font-size: 12px;
}

.summary-facts strong {
  color: var(--text);
  font-size: 16px;
}

.subsection-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.subsection-head h3 {
  margin: 0;
  color: var(--text);
  font-size: 14px;
}

.subsection-head p {
  margin: 3px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.split-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.split-card {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.split-card:hover,
.sample-card:hover {
  border-color: #b6bec9;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  transform: translateY(-2px);
}

.split-card > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 13px;
}

.split-card b {
  display: block;
  margin: 12px 0;
  color: var(--text);
  font-size: 24px;
}

.ratio-track {
  height: 6px;
  overflow: hidden;
  border-radius: 3px;
  background: #e5e7eb;
}

.ratio-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 0.55s ease;
}

.detail-grid,
.annotation-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.detail-panel,
.bbox-panel,
.class-panel {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.resource-list {
  display: grid;
}

.resource-row {
  display: grid;
  grid-template-columns: minmax(90px, auto) 48px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
}

.resource-row > span,
.resource-row small {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.difference-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.difference-grid div,
.annotation-metrics div {
  display: grid;
  align-content: center;
  gap: 7px;
  min-height: 80px;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.difference-grid strong,
.annotation-metrics strong {
  overflow-wrap: anywhere;
  color: var(--text);
  font-size: 17px;
}

.data-table {
  border: 1px solid var(--line);
  border-radius: 8px;
}

.table-emphasis {
  color: var(--text);
}

.annotation-metrics {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.compact-empty,
.file-index-note,
.raw-json-head {
  color: var(--text-muted);
  font-size: 12px;
}

.compact-empty {
  display: grid;
  place-items: center;
  min-height: 120px;
  border: 1px dashed var(--line-strong);
  border-radius: 8px;
  background: var(--surface-soft);
}

.file-index-note,
.raw-json-head {
  margin-bottom: 12px;
  padding: 11px 13px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.raw-json-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.raw-json-head strong {
  color: var(--text-secondary);
}

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 14px 56px;
  background: var(--surface-soft);
}

.file-list span {
  padding: 4px 7px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text-secondary);
  font-family: Consolas, monospace;
  font-size: 11px;
}

.observation-panel {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.observation-count {
  padding: 3px 7px;
  border-radius: 5px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
}

.observations {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.observation-item {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.observation-item span {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--accent-soft);
  color: var(--accent);
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 10px;
  font-weight: 800;
}

.observation-item p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.sample-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.sample-card {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.sample-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}

.sample-card-head h3 {
  margin: 0;
  color: var(--text);
  font-size: 14px;
  line-height: 1.4;
}

.sample-card-head span {
  display: block;
  margin-top: 3px;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-card-head .sample-index {
  flex: 0 0 auto;
  margin: 0;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
  font-weight: 800;
}

.sample-media {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1px;
  background: var(--line);
}

.sample-media.with-mask {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.sample-media figure {
  min-width: 0;
  margin: 0;
  background: var(--surface-soft);
}

.sample-media .el-image {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  background: #eef1f4;
}

.sample-media figcaption {
  padding: 9px 12px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-error {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  width: 100%;
  height: 100%;
  color: var(--text-muted);
  font-size: 12px;
}

.image-error .el-icon {
  font-size: 24px;
}

@media (max-width: 1180px) {
  .sample-grid {
    grid-template-columns: 1fr;
  }

  .dataset-summary,
  .detail-grid,
  .annotation-layout {
    grid-template-columns: 1fr;
  }

  .summary-facts {
    border-top: 1px solid var(--line);
    border-left: 0;
  }

  .observations {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .run-panel {
    grid-template-columns: 1fr;
  }

  .run-options-title {
    align-items: flex-start;
    flex-direction: column;
    gap: 2px;
    padding: 10px 0;
  }

  .profile-tabs :deep(.el-tabs__nav-scroll) {
    overflow-x: auto;
    scrollbar-width: none;
  }

  .profile-tabs :deep(.el-tabs__nav-next),
  .profile-tabs :deep(.el-tabs__nav-prev) {
    display: none;
  }

  .sample-media.with-mask {
    grid-template-columns: 1fr;
  }

  .split-grid,
  .annotation-metrics,
  .difference-grid {
    grid-template-columns: 1fr;
  }

  .summary-facts {
    grid-template-columns: 1fr;
  }

  .file-list {
    padding: 12px;
  }
}
</style>
