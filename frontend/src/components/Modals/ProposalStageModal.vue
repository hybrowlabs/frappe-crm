<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="blue" icon="fileText" class="mb-3.5">
      {{ __('Quotations are created & managed in the') }}
      <b>{{ __('ERPNext Desk') }}</b>
      {{
        __(
          '(10-step auto-pricing, discount approvals, PDF). From the CRM you can review existing quotations or jump to the Desk to draft a new one.',
        )
      }}
    </StageCallout>

    <div class="flex items-center gap-2">
      <Button :label="__('View Quotations')" @click="$emit('view-quotations')">
        <template #prefix><StageIcon name="fileText" class="h-4 w-4" /></template>
      </Button>
      <Button :label="__('Create in Desk')">
        <template #prefix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
      </Button>
      <span class="flex-1" />
      <Button
        variant="solid"
        theme="green"
        :label="__('Mark Won')"
        @click="show = false"
      >
        <template #prefix><StageIcon name="check" class="h-4 w-4" /></template>
      </Button>
    </div>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import { Button } from 'frappe-ui'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
defineEmits(['view-quotations'])
</script>
