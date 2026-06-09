<template>
  <div class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white">
    <div class="flex items-center gap-2 border-b border-outline-gray-2 px-3.5 py-2.5">
      <StageIcon v-if="icon" :name="icon" class="text-ink-gray-5" />
      <span class="text-base font-medium text-ink-gray-8">{{ title }}</span>
      <span class="flex-1" />
      <slot name="header-right" />
    </div>
    <div class="p-3.5">
      <slot />
    </div>
  </div>
</template>

<script setup>
import StageIcon from '@/components/StageForms/StageIcon.vue'

defineProps({
  title: { type: String, default: '' },
  icon: { type: String, default: '' },
})
</script>
