<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="orange" icon="beaker" class="mb-3">
      <b>{{ __('Hard gate.') }}</b>
      {{ __('Manager Reviewed') }} <b>{{ __('AND') }}</b>
      {{
        __(
          'Customer Validation must both be Yes before the Proposal stage unlocks.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Trial Logistics')" icon="calendar">
      <FieldGrid :cols="3">
        <FieldText
          v-model="start"
          type="date"
          :label="__('Evaluation Start')"
          required
          :error="errors.start"
        />
        <FieldText
          v-model="end"
          type="date"
          :label="__('Evaluation End')"
          required
          :error="errors.end"
        />
        <FieldSelect
          v-model="techPerson"
          :label="__('Technical Person')"
          required
          :options="['Suraj', 'Pankaj', 'Akshay']"
          :error="errors.techPerson"
        />
      </FieldGrid>
    </StageSection>

    <StageSection :title="__('Technical Observations')" icon="fileText">
      <FieldTextarea
        v-model="observations"
        :label="__('Observations')"
        required
        :rows="3"
        :error="errors.observations"
      />
      <FieldGrid :cols="2">
        <FieldText v-model="perfBaseline" :label="__('Performance — Baseline')" />
        <FieldText v-model="perfTrial" :label="__('Performance — Trial')" />
      </FieldGrid>
      <FieldTextarea
        v-model="feedback"
        :label="__('Customer Feedback')"
        required
        :rows="2"
        :error="errors.feedback"
      />
      <!-- Photos / Test Reports: backed by a separate doctype (wired later) -->
      <FieldStatic :label="__('Photos / Test Reports')">
        <span class="flex items-center gap-2">
          <span class="cursor-pointer text-ink-blue-3">+ {{ __('Add') }}</span>
        </span>
      </FieldStatic>
      <FieldCheckbox
        :label="__('Testimonial Captured?')"
        :checked="testimonialCaptured"
        @change="testimonialCaptured = !testimonialCaptured"
      />
    </StageSection>

    <StageSection :title="__('Outcome — both gates required')" icon="flag">
      <FieldGrid :cols="2">
        <FieldRadioGroup
          v-model="mgrReviewed"
          :label="__('Manager Reviewed?')"
          required
          inline
          :options="yesNoOptions"
        />
        <FieldRadioGroup
          v-model="custValidation"
          :label="__('Customer Validation Received?')"
          required
          inline
          :options="yesNoOptions"
        />
      </FieldGrid>
      <div class="my-3.5 h-px bg-outline-gray-2" />
      <FieldRadioGroup
        v-model="outcome"
        :label="__('Trial Outcome')"
        required
        :options="outcomeOptions"
        :error="errors.outcome"
      />

      <StageCallout
        :theme="gatesUnlocked ? 'green' : 'gray'"
        :icon="gatesUnlocked ? 'check' : 'lock'"
        class="mt-3"
      >
        <template v-if="gatesUnlocked">
          <b>{{ __('Both gates cleared → PROPOSAL UNLOCKED.') }}</b>
        </template>
        <template v-else>
          {{
            __(
              'Proposal stays locked until both gates are Yes and outcome is Successful.',
            )
          }}
        </template>
      </StageCallout>

      <div v-if="outcome === 'Partial'" class="mt-3">
        <StageCallout theme="amber" icon="bell" class="mb-2.5">
          <b>{{ __('Notification sent to Sales Manager (Kisan).') }}</b>
          {{
            __(
              'Partial result needs a decision. A lab request can be raised to investigate further before proceeding.',
            )
          }}
        </StageCallout>
        <Button :label="__('Create Lab Request')" @click="$emit('lab')">
          <template #prefix><StageIcon name="beaker" class="h-4 w-4" /></template>
        </Button>
      </div>

      <div v-if="outcome === 'Unsuccessful'" class="mt-3">
        <StageCallout theme="red" icon="alert" class="mb-2.5">
          {{ __('Trial unsuccessful. Send for a') }} <b>{{ __('retrial') }}</b>,
          {{ __('or close the deal as') }} <b>{{ __('Lost') }}</b>
          {{ __('with a reason.') }}
        </StageCallout>
        <FieldSelect
          v-model="lostReason"
          :label="__('Lost Reason')"
          required
          :options="lostReasonOptions"
          :error="errors.lostReason"
        />
        <FieldTextarea
          v-model="lostNotes"
          :label="__('Lost Notes')"
          :rows="2"
          :placeholder="__('What went wrong, competitor, learnings…')"
        />
      </div>
    </StageSection>

    <template #actions>
      <div class="flex w-full flex-wrap items-center gap-2 gap-y-2">
        <Button :label="__('Save Draft')" @click="saveDraft" />
        <Button
          v-if="outcome === 'Successful'"
          :label="__('Create Service Request')"
        >
          <template #prefix><StageIcon name="headphones" class="h-4 w-4" /></template>
        </Button>
        <span class="flex-1" />
        <template v-if="outcome === 'Unsuccessful'">
          <Button :label="__('Send to Retrial (+1)')">
            <template #prefix><StageIcon name="refresh" class="h-4 w-4" /></template>
          </Button>
          <Button
            variant="solid"
            theme="red"
            :label="__('Mark as Lost')"
            :disabled="!lostReason"
            @click="markAsLost"
          >
            <template #prefix><StageIcon name="x" class="h-4 w-4" /></template>
          </Button>
        </template>
        <Button
          v-else-if="outcome === 'Partial'"
          variant="solid"
          :label="__('Send to Sales Manager')"
          @click="sendToSalesManager"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else
          variant="solid"
          :label="__('Submit Evaluation')"
          :disabled="!gatesCleared"
          @click="submitEvaluation"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
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
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import { Button, toast } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save', 'lab'])

const start = ref('')
const end = ref('')
const techPerson = ref('')
const observations = ref('')
const perfBaseline = ref('')
const perfTrial = ref('')
const feedback = ref('')
const testimonialCaptured = ref(false)
const mgrReviewed = ref('n')
const custValidation = ref('n')
const outcome = ref('Successful')
const lostReason = ref('')
const lostNotes = ref('')

const yesNoOptions = [
  { label: __('Yes'), value: 'y' },
  { label: __('No'), value: 'n' },
]
const outcomeOptions = [
  { label: __('Successful → unlocks Proposal'), value: 'Successful' },
  { label: __('Partially Successful → Sales Manager decides'), value: 'Partial' },
  { label: __('Unsuccessful → +1 Retrial or Close (Lost)'), value: 'Unsuccessful' },
]
const lostReasonOptions = [
  '',
  'Trial failed — quality',
  'Price too high',
  'Competitor selected',
  'Budget / no decision',
  'Timeline mismatch',
  'No requirement',
  'Other',
]

onMounted(() => {
  const d = props.deal || {}
  start.value = d.evaluation_start || ''
  end.value = d.evaluation_end || ''
  techPerson.value = d.technical_person || ''
  observations.value = d.evaluation_observations || ''
  perfBaseline.value = d.performance_baseline || ''
  perfTrial.value = d.performance_trial || ''
  feedback.value = d.customer_feedback || ''
  testimonialCaptured.value = !!d.testimonial_captured
  mgrReviewed.value = d.manager_reviewed ? 'y' : 'n'
  custValidation.value = d.customer_validation_received ? 'y' : 'n'
  outcome.value = d.trial_outcome || 'Successful'
  lostReason.value = d.lost_reason || ''
  lostNotes.value = d.lost_notes || ''
})

const gatesCleared = computed(
  () => mgrReviewed.value === 'y' && custValidation.value === 'y',
)
const gatesUnlocked = computed(
  () => gatesCleared.value && outcome.value === 'Successful',
)

function buildValues() {
  return {
    evaluation_start: start.value || null,
    evaluation_end: end.value || null,
    technical_person: techPerson.value || null,
    evaluation_observations: observations.value || '',
    performance_baseline: perfBaseline.value || '',
    performance_trial: perfTrial.value || '',
    customer_feedback: feedback.value || '',
    testimonial_captured: testimonialCaptured.value ? 1 : 0,
    manager_reviewed: mgrReviewed.value === 'y' ? 1 : 0,
    customer_validation_received: custValidation.value === 'y' ? 1 : 0,
    trial_outcome: outcome.value || null,
    lost_reason: lostReason.value || null,
    lost_notes: lostNotes.value || '',
  }
}

// validation — errors surface only after a submit attempt, then clear live
const attempted = ref(false)
const requiredFields = [
  { key: 'start', label: __('Evaluation Start'), val: () => start.value },
  { key: 'end', label: __('Evaluation End'), val: () => end.value },
  { key: 'techPerson', label: __('Technical Person'), val: () => techPerson.value },
  { key: 'observations', label: __('Observations'), val: () => observations.value },
  { key: 'feedback', label: __('Customer Feedback'), val: () => feedback.value },
  { key: 'outcome', label: __('Trial Outcome'), val: () => outcome.value },
]
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  for (const f of requiredFields) if (!f.val()) e[f.key] = __('Required')
  if (outcome.value === 'Unsuccessful' && !lostReason.value)
    e.lostReason = __('Required')
  return e
})

function validate() {
  attempted.value = true
  const missing = requiredFields.filter((f) => !f.val()).map((f) => f.label)
  if (outcome.value === 'Unsuccessful' && !lostReason.value)
    missing.push(__('Lost Reason'))
  if (missing.length) {
    toast.error(__('Please fill all required fields: {0}', [missing.join(', ')]))
    return false
  }
  return true
}

function saveDraft() {
  emit('save', { values: buildValues(), advance: false })
  show.value = false
}

function submitEvaluation() {
  if (!validate()) return
  emit('save', { values: buildValues(), advance: true })
  show.value = false
}

function sendToSalesManager() {
  if (!validate()) return
  emit('save', { values: buildValues(), advance: false })
  show.value = false
}

function markAsLost() {
  if (!validate()) return
  emit('save', { values: buildValues(), advance: false })
  show.value = false
}
</script>
