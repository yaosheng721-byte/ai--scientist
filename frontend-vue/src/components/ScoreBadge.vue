<script setup>
import { computed } from 'vue'
import { scoreLevel } from '../utils/format'

const props = defineProps({
  score: { type: [Number, String], default: 0 },
})

const level = computed(() => scoreLevel(props.score))
</script>

<template>
  <span class="score-badge" :class="level">{{ Number(score) || 0 }}</span>
</template>

<style scoped>
.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 28px;
  padding: 0 10px;
  border-radius: 8px;
  color: #ffffff;
  font-size: 13px;
  font-weight: 850;
}

.strong {
  background: #047857;
}

.good {
  background: #2563eb;
}

.normal {
  background: #b45309;
}

.weak {
  background: #b91c1c;
}
</style>
