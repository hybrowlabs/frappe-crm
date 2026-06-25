<template>
  <div class="mb-2">
    <div class="mb-1.5 text-sm text-ink-gray-5">
      {{ label }} <span v-if="required" class="text-ink-red-3">*</span>
    </div>
    <FormControl
      type="select"
      :modelValue="modelValue"
      :options="normalizedOptions"
      :disabled="disabled"
      :class="error ? 'rounded [&_select]:!border-outline-red-2' : ''"
      @update:modelValue="$emit('update:modelValue', $event)"
    />
    <div v-if="error" class="mt-1 text-xs text-ink-red-3">{{ error }}</div>
    <div v-else-if="help" class="mt-1 text-xs text-ink-gray-4">{{ help }}</div>
  </div>
</template>

<script setup>
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  help: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  error: { type: String, default: '' },
})

defineEmits(['update:modelValue'])

const normalizedOptions = computed(() => {
  const opts = props.options.map((o) =>
    typeof o === 'object' ? o : { label: o, value: o },
  )
  if (props.placeholder) {
    opts.unshift({ label: props.placeholder, value: '' })
  }
  return opts
})
</script>
