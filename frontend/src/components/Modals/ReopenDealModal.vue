<template>
  <Dialog
    v-model="show"
    :options="{ title: `${statusLabel} — ${__('stage form')}`, size: '2xl' }"
  >
    <template #body-content>
      <div class="-mt-2 mb-4 text-base text-ink-gray-5">
        {{ subtitle }}
      </div>
      <div
        class="flex items-start gap-2.5 rounded-lg border border-outline-red-1 bg-surface-red-1 p-3 text-base leading-5 text-ink-red-4"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="mt-0.5 shrink-0"
        >
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </svg>
        <span>
          {{ __('This deal is marked Lost. Reopen by changing Status in the panel.') }}
        </span>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { Dialog } from 'frappe-ui'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
</script>
