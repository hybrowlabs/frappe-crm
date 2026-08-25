<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout :theme="declined ? 'red' : 'blue'" icon="beaker" class="mb-3">
      <template v-if="declined">
        {{
          __(
            'This new product development was declined and the deal was closed. The remarks recorded at the time are shown below.',
          )
        }}
      </template>
      <template v-else>
        {{
          __(
            'The technical team could not match an existing product and proposed developing a new one. Review their figures, then decide whether the deal proceeds to Tech Evaluation.',
          )
        }}
      </template>
    </StageCallout>

    <!-- Everything the tech team captured, read-only. Every figure is optional on
         their side, so only the ones they actually filled in are shown. -->
    <StageSection :title="__('Proposed by the Technical Team')" icon="beaker">
      <FieldGrid :cols="2">
        <FieldStatic :label="__('Proposed by (Tech Person)')" :value="assignedTo" />
        <FieldStatic :label="__('Product context')" :value="productSummary || '—'" />
        <FieldStatic v-if="karatage" :label="__('Karatage')" :value="karatage" />
      </FieldGrid>
      <FieldGrid v-if="hasFigures" :cols="2" class="mt-1">
        <FieldStatic
          v-if="deal.npd_composition"
          :label="__('Composition (%)')"
          :value="String(deal.npd_composition)"
        />
        <FieldStatic
          v-if="deal.npd_hardness"
          :label="__('Hardness')"
          :value="String(deal.npd_hardness)"
        />
        <FieldStatic
          v-if="deal.npd_xrf"
          :label="__('XRF (%)')"
          :value="String(deal.npd_xrf)"
        />
        <FieldStatic
          v-if="deal.npd_icp"
          :label="__('ICP')"
          :value="String(deal.npd_icp)"
        />
      </FieldGrid>
      <p v-else class="text-p-sm text-ink-gray-5">
        {{ __('No lab figures were recorded with this proposal.') }}
      </p>
    </StageSection>

    <!-- Already answered: show the outcome instead of the form. -->
    <StageSection
      v-if="declined"
      :title="__('Decision')"
      icon="flag"
    >
      <FieldGrid :cols="1">
        <FieldStatic :label="__('Proceed?')" :value="deal.npd_decision || '—'" />
      </FieldGrid>
      <div class="mt-2 whitespace-pre-line rounded-lg bg-surface-gray-2 px-3.5 py-2.5 text-p-sm text-ink-gray-7">
        {{ deal.npd_remarks || __('No remarks were recorded.') }}
      </div>
    </StageSection>

    <StageSection v-else :title="__('Decision Point — proceed with development?')" icon="flag">
      <FieldRadioGroup
        v-model="decision"
        inline
        :label="__('Proceed?')"
        required
        :options="decisionOptions"
        :error="errors.decision"
      />
      <FieldTextarea
        v-model="remarks"
        class="mt-3"
        :label="__('Remarks')"
        :rows="2"
        :placeholder="__('Add a note for the record (optional)')"
      />
      <StageCallout
        v-if="decision === 'No'"
        theme="red"
        icon="alert"
        class="mt-1"
      >
        {{
          __(
            'The deal is closed and the flow stops here. It is moved to the Closed stage — not marked Lost, since it never reached a commercial decision.',
          )
        }}
      </StageCallout>
    </StageSection>

    <template #actions>
      <div class="flex w-full items-center gap-2">
        <span class="flex-1" />
        <Button
          v-if="declined"
          variant="solid"
          :label="__('Close')"
          @click="show = false"
        />
        <Button
          v-else-if="decision === 'Yes'"
          variant="solid"
          :label="__('Approve → Tech Evaluation')"
          :loading="working"
          @click="submit"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else-if="decision === 'No'"
          variant="solid"
          theme="red"
          :label="__('Decline → Close deal')"
          :loading="working"
          @click="submit"
        >
          <template #suffix><StageIcon name="x" class="h-4 w-4" /></template>
        </Button>
        <Button v-else variant="solid" disabled :label="__('Select Yes or No above')" />
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
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import { productChain } from '@/components/StageForms/productContext'
import { Button, call, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['done'])

const decision = ref(null) // null | 'Yes' | 'No'
const remarks = ref('')
const working = ref(false)

// A declined proposal is read-only — the flow stopped, there is nothing left to answer.
const declined = computed(() => !!props.deal?.npd_declined)

const decisionOptions = [
  { label: __('Yes — proceed to Tech Evaluation'), value: 'Yes' },
  { label: __('No — close the deal'), value: 'No' },
]

const assignedTo = computed(() => {
  const d = props.deal || {}
  return d.technical_person || d.assigned_tech_member || '—'
})
const productSummary = computed(() => productChain(props.deal))
const karatage = computed(() => props.deal?.karatage || '')
const hasFigures = computed(() => {
  const d = props.deal || {}
  return !!(d.npd_composition || d.npd_hardness || d.npd_xrf || d.npd_icp)
})

// validation — errors surface only after an attempt, then clear live
const attempted = ref(false)
const errors = computed(() => {
  if (!attempted.value) return {}
  return decision.value ? {} : { decision: __('Select Yes or No') }
})

async function submit() {
  attempted.value = true
  if (!decision.value) {
    toast.error(__('Please select Yes or No.'))
    return
  }
  working.value = true
  try {
    await call('crm.api.tech_team.respond_npd', {
      deal: props.deal?.name,
      decision: decision.value,
      remarks: remarks.value || '',
    })
    toast.success(
      decision.value === 'Yes'
        ? __('Approved — deal moved to Tech Evaluation')
        : __('Declined — the deal has been closed'),
    )
    emit('done')
    show.value = false
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error recording the decision'))
  } finally {
    working.value = false
  }
}
</script>
