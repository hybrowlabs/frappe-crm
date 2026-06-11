<template>
  <label class="flex cursor-pointer select-none items-start gap-2">
    <input
      type="checkbox"
      :checked="checked"
      class="mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded-sm border-outline-gray-3 accent-blue-500"
      @change="$emit('change', $event.target.checked)"
    />
    <span class="text-base leading-5 text-ink-gray-8">{{ label }}</span>
  </label>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  checked: { type: Boolean, default: false },
})

defineEmits(['change'])
</script>
