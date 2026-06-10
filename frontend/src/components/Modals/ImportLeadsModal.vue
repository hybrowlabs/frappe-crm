<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Import Leads'),
      size: 'xl',
    }"
  >
    <template #body-content>
      <p class="text-p-sm text-ink-gray-6">
        {{ __('Marketing bulk upload · auto-dedup on Company + Mobile') }}
      </p>
      <!-- TODO: import wizard (Upload → Map Columns → Review & Import) -->
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'

const show = defineModel({ type: Boolean })
</script>
