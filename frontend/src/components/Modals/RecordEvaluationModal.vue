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
        <FieldText v-model="start" :label="__('Evaluation Start')" required />
        <FieldText v-model="end" :label="__('Evaluation End')" required />
        <FieldSelect
          v-model="techPerson"
          :label="__('Technical Person')"
          required
          :options="['Suraj', 'Pankaj', 'Akshay']"
        />
      </FieldGrid>
    </StageSection>

    <StageSection :title="__('Technical Observations')" icon="fileText">
      <FieldTextarea
        v-model="observations"
        :label="__('Observations')"
        required
        :rows="3"
      />
      <FieldGrid :cols="2">
        <FieldText :label="__('Performance — Baseline')" modelValue="92%" readonly />
        <FieldText :label="__('Performance — Trial')" modelValue="97.2%" readonly />
      </FieldGrid>
      <FieldTextarea
        v-model="feedback"
        :label="__('Customer Feedback')"
        required
        :rows="2"
      />
      <FieldStatic :label="__('Photos / Test Reports')">
        <span class="flex items-center gap-2">
          <Badge :label="'trial_run1.jpg'" theme="blue" variant="subtle" />
          <span class="cursor-pointer text-ink-blue-3">+ {{ __('Add') }}</span>
        </span>
      </FieldStatic>
      <FieldStatic :label="__('Testimonial Captured?')" :bordered="false">
        <Badge :label="__('Yes')" theme="green" variant="subtle" />
      </FieldStatic>
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
      <div class="flex w-full items-center gap-2">
        <Button :label="__('Save Draft')" @click="toast.success(__('Draft saved'))" />
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
            @click="show = false"
          >
            <template #prefix><StageIcon name="x" class="h-4 w-4" /></template>
          </Button>
        </template>
        <Button
          v-else-if="outcome === 'Partial'"
          variant="solid"
          :label="__('Send to Sales Manager')"
          @click="show = false"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else
          variant="solid"
          :label="__('Submit Evaluation')"
          :disabled="!gatesCleared"
          @click="show = false"
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
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import { Button, Badge, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
defineEmits(['lab'])

const start = ref('28 Mar 2025')
const end = ref('01 Apr 2025')
const techPerson = ref('Suraj')
const observations = ref(
  'Run 1: Yield improved 92% → 97.2%. No porosity observed. Gold loss reduced by ~60%.',
)
const feedback = ref('Results significantly better')
const mgrReviewed = ref('y')
const custValidation = ref('y')
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

const gatesCleared = computed(
  () => mgrReviewed.value === 'y' && custValidation.value === 'y',
)
const gatesUnlocked = computed(
  () => gatesCleared.value && outcome.value === 'Successful',
)
</script>
