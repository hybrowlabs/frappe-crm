<template>
  <label
    class="inline-flex cursor-pointer select-none items-center gap-2"
    @click="$emit('select')"
  >
    <span
      class="relative flex h-[15px] w-[15px] shrink-0 items-center justify-center rounded-full border-[1.5px] transition-colors"
      :class="selected ? 'border-blue-500' : 'border-outline-gray-3'"
    >
      <span v-if="selected" class="h-[7px] w-[7px] rounded-full bg-blue-500" />
    </span>
    <span class="text-base text-ink-gray-8">{{ label }}</span>
  </label>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  selected: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>
