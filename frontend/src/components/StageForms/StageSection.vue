<template>
  <div class="mb-3 overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white">
    <button
      type="button"
      class="flex w-full items-center gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5 text-left"
      @click="open = !open"
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="text-ink-gray-5 transition-transform duration-150"
        :class="open ? '' : '-rotate-90'"
      >
        <path d="m6 9 6 6 6-6" />
      </svg>
      <span class="flex text-ink-gray-5"><slot name="icon" /></span>
      <span class="text-base font-semibold text-ink-gray-8">{{ title }}</span>
    </button>
    <div v-show="open" class="p-3.5">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  title: { type: String, default: '' },
})

const open = ref(true)
</script>
