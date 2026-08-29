<script setup>
import { Back } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  runId: { type: String, default: '' },
  back: { type: Boolean, default: false },
})

const router = useRouter()

function backToWorkspace() {
  if (props.runId) {
    router.push({ name: 'workspace', params: { runId: props.runId } })
  } else {
    router.push({ name: 'create-run' })
  }
}
</script>

<template>
  <header class="page-header">
    <div class="page-heading">
      <div class="page-kicker"><slot name="kicker">Workspace</slot></div>
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </div>
    <div class="page-actions">
      <slot name="actions" />
      <el-button v-if="back" :icon="Back" circle title="返回工作台" @click="backToWorkspace" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
}

.page-heading {
  min-width: 0;
}

.page-kicker {
  margin-bottom: 6px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 750;
  text-transform: uppercase;
  overflow-wrap: anywhere;
}

h1 {
  margin: 0;
  color: var(--text);
  font-size: 27px;
  line-height: 1.25;
  font-weight: 780;
  letter-spacing: 0;
}

p {
  max-width: 720px;
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

@media (max-width: 720px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
    padding-bottom: 15px;
  }

  h1 {
    font-size: 24px;
  }

  p {
    font-size: 13px;
  }

  .page-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}
</style>
