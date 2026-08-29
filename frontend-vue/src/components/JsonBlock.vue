<script setup>
defineProps({
  value: { type: [Object, Array, String, Number, Boolean], default: null },
})
</script>

<template>
  <pre class="code-panel">{{ typeof value === 'string' ? value : JSON.stringify(value, null, 2) }}</pre>
</template>
