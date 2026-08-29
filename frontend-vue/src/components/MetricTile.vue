<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '-' },
  hint: { type: String, default: '' },
})

const compact = computed(() => String(props.value ?? '').length > 16)
</script>

<template>
  <div class="metric-tile">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value" :class="{ compact }" :title="String(value)">{{ value }}</div>
    <div v-if="hint" class="metric-hint" :title="hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.metric-tile {
  position: relative;
  overflow: hidden;
  min-height: 108px;
  padding: 17px 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.metric-tile::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  background: #bfd8d4;
  content: "";
}

.metric-label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 750;
}

.metric-value {
  margin-top: 10px;
  color: var(--text);
  font-size: 24px;
  line-height: 1.15;
  font-weight: 780;
  overflow-wrap: anywhere;
}

.metric-value.compact {
  font-size: 18px;
  line-height: 1.3;
}

.metric-hint {
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
