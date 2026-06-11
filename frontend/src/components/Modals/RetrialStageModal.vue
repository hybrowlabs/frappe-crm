<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="amber" icon="refresh" class="mb-3.5">
      <b>{{ __('Retrial #{0}.', [count]) }}</b>
      {{
        __(
          'Trial was unsuccessful. The Tech Head runs a repeat trial via the Service module. If it fails again, the Technical Director closes the deal as Lost.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Retrial')" icon="beaker">
      <FieldStatic :label="__('Retrial Count')">
        <Badge :label="String(count)" theme="red" variant="subtle" />
      </FieldStatic>
      <FieldStatic :label="__('Owner')" value="Tech Head" :bordered="false" />
      <FieldTextarea
        v-model="reason"
        :label="__('Retrial Reason / Adjustment')"
        :rows="2"
        :placeholder="
          __('e.g. Adjust alloy ratio, re-run casting at lower temp')
        "
        class="mt-2"
      />
      <div class="mt-3 flex flex-wrap items-center gap-2 gap-y-2">
        <Button :label="__('Create Service Ticket')" @click="$emit('ticket')">
          <template #prefix><StageIcon name="headphones" class="h-4 w-4" /></template>
        </Button>
        <span class="flex-1" />
        <Button theme="red" :label="__('Close as Lost')" @click="show = false" />
        <Button
          variant="solid"
          theme="green"
          :label="__('Retrial Passed → Proposal')"
          @click="show = false"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
      </div>
    </StageSection>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageSection from '@/components/StageForms/StageSection.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import { Button, Badge } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  count: { type: Number, default: 1 },
})

const show = defineModel({ type: Boolean })
defineEmits(['ticket'])

const reason = ref('')
</script>
