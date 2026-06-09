<template>
  <div class="grid gap-x-4" :class="colsClass">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  cols: { type: [Number, String], default: 2 },
})

const COLS = { 1: 'grid-cols-1', 2: 'grid-cols-2', 3: 'grid-cols-3' }
const colsClass = computed(() => COLS[props.cols] || COLS[2])
</script>
