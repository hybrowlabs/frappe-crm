<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="amber" icon="bell" class="mb-3">
      {{
        __(
          'This evaluation was partially successful and needs a Sales Manager decision before proceeding.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Trial Result')" icon="flag">
      <FieldStatic :label="__('Trial Outcome')">
        <Badge :label="deal.trial_outcome || '—'" theme="amber" variant="subtle" />
      </FieldStatic>
      <FieldStatic :label="__('Technical Person')">
        {{ techPersonName }}
      </FieldStatic>
      <FieldGrid :cols="2">
        <FieldText
          :label="__('Performance — Baseline')"
          :modelValue="deal.performance_baseline || '—'"
          readonly
        />
        <FieldText
          :label="__('Performance — Trial')"
          :modelValue="deal.performance_trial || '—'"
          readonly
        />
      </FieldGrid>
      <FieldTextarea
        :label="__('Observations')"
        :modelValue="deal.evaluation_observations || '—'"
        :rows="3"
        readonly
      />
      <FieldTextarea
        :label="__('Customer Feedback')"
        :modelValue="deal.customer_feedback || '—'"
        :rows="2"
        readonly
      />
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button variant="solid" theme="green" :label="__('Approve')" @click="approve">
          <template #prefix><StageIcon name="check" class="h-4 w-4" /></template>
        </Button>
      </div>
    </template>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageSection from '@/components/StageForms/StageSection.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import FieldGrid from '@/components/StageForms/FieldGrid.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import { Button, Badge, createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save'])

const techTeamResource = createResource({
  url: 'crm.api.tech_team.get_tech_teams',
  auto: true,
})
const techPersonName = computed(() => {
  const o = (techTeamResource.data || []).find(
    (x) => x.value === props.deal.technical_person,
  )
  return o?.full_name || props.deal.technical_person || '—'
})

function approve() {
  emit('save', { values: { sales_manager_approved: 1 }, advance: false })
  show.value = false
}
</script>
