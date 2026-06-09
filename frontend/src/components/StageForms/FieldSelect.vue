<template>
  <div class="mb-2">
    <div class="mb-1.5 text-sm text-ink-gray-5">
      {{ label }} <span v-if="required" class="text-ink-red-3">*</span>
    </div>
    <FormControl
      type="select"
      :modelValue="modelValue"
      :options="normalizedOptions"
      @update:modelValue="$emit('update:modelValue', $event)"
    />
    <div v-if="help" class="mt-1 text-xs text-ink-gray-4">{{ help }}</div>
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
  help: { type: String, default: '' },
})

defineEmits(['update:modelValue'])

const normalizedOptions = computed(() =>
  props.options.map((o) =>
    typeof o === 'object' ? o : { label: o, value: o },
  ),
)
</script>
