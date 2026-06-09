<template>
  <div class="mb-2">
    <div class="mb-1.5 text-sm text-ink-gray-5">
      {{ label }} <span v-if="required" class="text-ink-red-3">*</span>
    </div>
    <FormControl
      :type="type"
      :modelValue="modelValue"
      :placeholder="placeholder"
      :readonly="readonly"
      @update:modelValue="$emit('update:modelValue', $event)"
    />
    <div v-if="help" class="mt-1 text-xs text-ink-gray-4">{{ help }}</div>
  </div>
</template>

<script setup>
import { FormControl } from 'frappe-ui'

defineProps({
  label: { type: String, default: '' },
  modelValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  required: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  help: { type: String, default: '' },
})

defineEmits(['update:modelValue'])
</script>
