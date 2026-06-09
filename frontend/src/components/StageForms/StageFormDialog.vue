<template>
  <Dialog v-model="show" :options="{ title: dialogTitle, size }">
    <template #body-content>
      <div v-if="subtitle" class="-mt-2 mb-4 text-base text-ink-gray-5">
        {{ subtitle }}
      </div>
      <slot />
    </template>
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // The deal status label, e.g. "Req. Discussion" → title "Req. Discussion — stage form".
  statusLabel: { type: String, default: '' },
  // Explicit title; when set it overrides the "<statusLabel> — stage form" pattern.
  title: { type: String, default: '' },
  // Secondary line under the title, e.g. "Mehta Jewellers · CRM-DEAL-2026-0034".
  subtitle: { type: String, default: '' },
  // frappe-ui Dialog size token (xs … 7xl). 3xl ≈ 760px (prototype width).
  size: { type: String, default: '3xl' },
})

const show = defineModel({ type: Boolean })

const dialogTitle = computed(
  () => props.title || `${props.statusLabel} — ${__('stage form')}`,
)
</script>
