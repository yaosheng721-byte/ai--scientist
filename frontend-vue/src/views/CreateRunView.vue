 <script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Collection, DataAnalysis, FolderOpened, Setting } from '@element-plus/icons-vue'
import { useRunStore } from '../stores/runStore'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const runStore = useRunStore()
const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  query: '研究工业缺陷检测中小缺陷定位不稳定的问题',
  domain: 'industrial',
  task_type: 'dataset_profiling',
  dataset_path: 'app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle',
})

const rules = {
  query: [{ required: true, message: '请输入研究问题', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  dataset_path: [{ required: true, message: '请输入数据集路径', trigger: 'blur' }],
}

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const data = await runStore.create({ ...form })
    ElMessage.success('任务已创建')
    router.push({ name: 'workspace', params: { runId: data.run_id } })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-stack create-page">
    <PageHeader
      title="新建研究任务"
      description="配置研究目标与数据集，任务创建后可在工作台持续查看执行进度和分析结果。"
    >
      <template #kicker>CV AI Scientist</template>
    </PageHeader>

    <el-card shadow="never" class="create-card">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-layout">
          <section class="form-section research-section">
            <div class="section-heading">
              <span class="section-icon"><el-icon><DataAnalysis /></el-icon></span>
              <div>
                <h2>研究内容</h2>
                <p>描述希望分析的问题，并指定本次任务使用的数据集。</p>
              </div>
            </div>

            <el-form-item label="研究问题" prop="query">
              <el-input
                v-model="form.query"
                type="textarea"
                :rows="6"
                maxlength="300"
                show-word-limit
                placeholder="例如：研究工业缺陷检测中小缺陷定位不稳定的问题"
              />
            </el-form-item>

            <el-form-item label="数据集路径" prop="dataset_path" class="dataset-field">
              <el-input
                v-model="form.dataset_path"
                clearable
                placeholder="请输入数据集所在路径"
              >
                <template #prefix>
                  <el-icon><FolderOpened /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </section>

          <section class="form-section config-section">
            <div class="section-heading">
              <span class="section-icon"><el-icon><Setting /></el-icon></span>
              <div>
                <h2>任务配置</h2>
                <p>选择数据领域、分析类型和执行范围。</p>
              </div>
            </div>

            <el-form-item label="领域" prop="domain">
              <el-select v-model="form.domain" class="full-width">
                <el-option label="Industrial" value="industrial" />
                <el-option label="Remote Sensing" value="remote_sensing" />
                <el-option label="Medical" value="medical" />
                <el-option label="General CV" value="general_cv" />
              </el-select>
            </el-form-item>

            <el-form-item label="任务类型" prop="task_type">
              <el-select v-model="form.task_type" class="full-width">
                <el-option label="Dataset Profiling" value="dataset_profiling" />
                <el-option label="Anomaly Detection" value="anomaly_detection" />
                <el-option label="Detection" value="detection" />
                <el-option label="Segmentation" value="segmentation" />
                <el-option label="Classification" value="classification" />
                <el-option label="Change Detection" value="change_detection" />
              </el-select>
            </el-form-item>

            <div class="execution-note">
              <el-icon><Collection /></el-icon>
              <span>当前完整执行链路支持数据集画像，其它任务类型将创建为待扩展任务。</span>
            </div>
          </section>
        </div>

        <div class="form-actions">
          <div>
            <strong>准备创建任务</strong>
            <span>创建后将自动进入任务工作台。</span>
          </div>
          <el-button type="primary" size="large" :loading="submitting" @click="submit">
            创建任务
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.create-page {
  width: min(100%, 1240px);
  margin: 0 auto;
}

.create-card {
  width: 100%;
}

.create-card :deep(.el-card__body) {
  padding: 0;
}

.form-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.8fr);
}

.form-section {
  min-width: 0;
  padding: 28px 30px 30px;
}

.config-section {
  border-left: 1px solid var(--line);
  background: var(--surface-soft);
}

.section-heading {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 26px;
}

.section-icon {
  display: grid;
  place-items: center;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 17px;
}

.section-heading h2 {
  margin: 0;
  color: var(--text);
  font-size: 16px;
  line-height: 1.35;
}

.section-heading p {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.research-section :deep(.el-textarea__inner) {
  min-height: 158px !important;
  padding: 12px 14px 28px;
  line-height: 1.65;
}

.dataset-field {
  margin-top: 22px;
}

.full-width {
  width: 100%;
}

.config-section :deep(.el-form-item) {
  margin-bottom: 22px;
}

.execution-note {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin-top: 6px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.execution-note .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: var(--text-muted);
}

.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 30px;
  border-top: 1px solid var(--line);
  background: var(--surface);
}

.form-actions > div {
  display: grid;
  gap: 3px;
}

.form-actions strong {
  color: var(--text);
  font-size: 13px;
}

.form-actions span {
  color: var(--text-muted);
  font-size: 12px;
}

.form-actions .el-button {
  min-width: 118px;
}

@media (max-width: 980px) {
  .form-layout {
    grid-template-columns: 1fr;
  }

  .config-section {
    border-top: 1px solid var(--line);
    border-left: 0;
  }
}

@media (max-width: 720px) {
  .form-section {
    padding: 22px 18px;
  }

  .form-actions {
    align-items: stretch;
    flex-direction: column;
    padding: 18px;
  }

  .form-actions .el-button {
    width: 100%;
  }
}
</style>
