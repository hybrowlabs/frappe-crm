<template>
  <div
    class="flex items-start gap-2.5 rounded-lg border p-3 text-base leading-5"
    :class="themeClass"
  >
    <span class="mt-0.5 shrink-0"><slot name="icon" /></span>
    <span><slot /></span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  theme: { type: String, default: 'blue' }, // blue | amber | gray | green | orange | red
})

const THEMES = {
  blue: 'border-outline-blue-1 bg-surface-blue-1 text-ink-blue-3',
  amber: 'border-outline-amber-1 bg-surface-amber-1 text-ink-amber-3',
  gray: 'border-outline-gray-2 bg-surface-gray-2 text-ink-gray-7',
  green: 'border-outline-green-1 bg-surface-green-1 text-ink-green-3',
  orange: 'border-outline-amber-1 bg-surface-amber-1 text-ink-amber-3',
  red: 'border-outline-red-1 bg-surface-red-1 text-ink-red-4',
}

const themeClass = computed(() => THEMES[props.theme] || THEMES.blue)
</script>
