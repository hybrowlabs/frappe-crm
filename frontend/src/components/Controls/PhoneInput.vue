<template>
  <div>
    <div class="relative flex items-center">
      <div
        class="absolute inset-y-0 left-0 flex select-none items-center pl-2 text-base"
        :class="disabled ? 'text-ink-gray-4' : 'text-ink-gray-5'"
      >
        {{ countryCode }}
      </div>
      <input
        type="text"
        inputmode="numeric"
        autocomplete="off"
        maxlength="10"
        :value="localNumber"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="inputClasses"
        @input="onInput"
      />
    </div>
    <p v-if="description" class="mt-1.5 text-p-sm text-ink-gray-5">
      {{ description }}
    </p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  value: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  description: { type: String, default: '' },
  countryCode: { type: String, default: '+91' },
})

const emit = defineEmits(['change'])

const digitsOnly = (v) => String(v ?? '').replace(/\D/g, '')

// "+919861094351" / "919861094351" / "9861094351" -> "9861094351"
function toLocalNumber(value) {
  let digits = digitsOnly(value)
  const code = digitsOnly(props.countryCode)
  if (digits.length > 10 && digits.startsWith(code)) {
    digits = digits.slice(code.length)
  }
  return digits.slice(0, 10)
}

// local state is the source of truth while typing, so the async round trip
// through the document store cannot reset the input mid keystroke
const localNumber = ref(toLocalNumber(props.value))

watch(
  () => props.value,
  (value) => {
    // ignore the echo of what we just emitted, sync only on external changes
    if (digitsOnly(value) === digitsOnly(props.countryCode + localNumber.value))
      return
    localNumber.value = toLocalNumber(value)
  },
)

function onInput(e) {
  const digits = digitsOnly(e.target.value).slice(0, 10)
  localNumber.value = digits
  // reflect the sanitized value back, otherwise typed letters stay in the input
  e.target.value = digits
  emit('change', digits ? props.countryCode + digits : '')
}

const inputClasses = [
  'h-7 w-full rounded py-1.5 pl-11 pr-2 text-base transition-colors dark:[color-scheme:dark]',
  'border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 text-ink-gray-8',
  'hover:border-outline-gray-modals hover:bg-surface-gray-3',
  'focus:border-outline-gray-4 focus:bg-surface-white focus:shadow-sm focus:ring-0',
  'focus-visible:ring-2 focus-visible:ring-outline-gray-3',
  'disabled:border-transparent disabled:bg-surface-gray-1 disabled:text-ink-gray-5',
]
</script>
