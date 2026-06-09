<template>
  <div
    class="flex items-center justify-between gap-4 py-2 text-base"
    :class="bordered ? 'border-b border-outline-gray-1' : ''"
  >
    <span class="text-ink-gray-5">{{ label }}</span>
    <span class="text-right font-medium text-ink-gray-8">
      <slot>{{ value }}</slot>
    </span>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  value: { type: [String, Number], default: '' },
  bordered: { type: Boolean, default: true },
})
</script>
