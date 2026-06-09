<template>
  <div>
    <div v-if="label" class="mb-1.5 text-sm text-ink-gray-5">
      {{ label }} <span v-if="required" class="text-ink-red-3">*</span>
    </div>
    <div
      class="flex gap-x-4 gap-y-2"
      :class="inline ? 'flex-row flex-wrap' : 'flex-col'"
    >
      <FieldRadio
        v-for="opt in normalized"
        :key="opt.value"
        :label="opt.label"
        :selected="modelValue === opt.value"
        @select="$emit('update:modelValue', opt.value)"
      />
    </div>
  </div>
</template>

<script setup>
import FieldRadio from '@/components/StageForms/FieldRadio.vue'
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  modelValue: { type: [String, Number, Boolean], default: '' },
  // Each option may be a string or { label, value }.
  options: { type: Array, default: () => [] },
  required: { type: Boolean, default: false },
  inline: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const normalized = computed(() =>
  props.options.map((o) =>
    typeof o === 'object' ? o : { label: o, value: o },
  ),
)
</script>
