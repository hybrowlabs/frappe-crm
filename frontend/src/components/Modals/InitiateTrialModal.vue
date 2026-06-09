<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="green" icon="check" class="mb-3">
      {{
        __(
          'Qualifies the commercial opportunity. Trial decision is made here. On save, the Tech team is auto-assigned by Product Category × Region and the waiting-time clock starts.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Qualification')" icon="target">
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="oppType"
          :label="__('Opportunity Type')"
          required
          :options="oppTypeOptions"
        />
        <FieldText
          :label="__('Product Category')"
          :modelValue="productSummary"
          readonly
          :help="__('Carried forward from Requirements')"
        />
      </FieldGrid>
    </StageSection>

    <StageSection :title="__('Deal Qualification')" icon="checkSquare">
      <FieldRadioGroup
        v-model="dmInvolved"
        :label="__('Decision Maker Involved?')"
        required
        inline
        :options="dmOptions"
        class="mb-3"
      />
      <div class="mb-1.5 text-sm text-ink-gray-5">
        {{ __('Decision Criteria (multi-select)') }}
      </div>
      <div class="mb-3.5 grid grid-cols-2 gap-x-4 gap-y-2">
        <FieldCheckbox
          v-for="c in criteriaOptions"
          :key="c"
          :label="c"
          :checked="criteria.includes(c)"
          @change="toggle(criteria, c)"
        />
      </div>
      <FieldCheckbox
        :label="__('Trial Required Before Decision')"
        :checked="trialBeforeDecision"
        @change="trialBeforeDecision = !trialBeforeDecision"
      />
      <div class="my-3.5 h-px bg-outline-gray-2" />
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="timeline"
          :label="__('Decision Timeline')"
          required
          :options="timelineOptions"
        />
        <FieldText
          v-model="volume"
          :label="__('Expected Monthly Volume (KG)')"
          required
        />
        <FieldText
          v-model="dealValue"
          :label="__('Deal Value (INR)')"
          required
        />
        <FieldSelect
          v-model="forecast"
          :label="__('Forecast Category')"
          required
          :options="forecastOptions"
        />
      </FieldGrid>
    </StageSection>

    <StageSection :title="__('Technical Assignment')" icon="beaker">
      <FieldGrid :cols="2">
        <FieldRadioGroup
          v-model="trialRequired"
          :label="__('Trial Required?')"
          required
          inline
          :options="yesNoOptions"
        />
        <FieldRadioGroup
          v-model="assignTech"
          :label="__('Assign to Tech Team?')"
          required
          inline
          :options="yesNoOptions"
        />
      </FieldGrid>
      <FieldGrid :cols="2" class="mt-1">
        <FieldSelect
          v-model="techCategory"
          :label="__('Tech Team Category')"
          required
          :options="techCategoryOptions"
          :help="__('Auto-routed by category × region')"
        />
        <FieldText v-model="assignNotes" :label="__('Assignment Notes')" />
      </FieldGrid>
      <StageCallout theme="blue" icon="bell" class="mt-2">
        {{ __('On save —') }}
        <b>{{ __('3 simultaneous notifications') }}</b>
        {{
          __(
            ': WhatsApp · Email · Frappe Task. Waiting-time clock starts at notification send.',
          )
        }}
      </StageCallout>
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Save Draft')" @click="toast.success(__('Draft saved'))" />
        <Button
          variant="solid"
          :label="__('Assign & Notify Tech Team')"
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
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import { Button, toast } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })

const oppType = ref('New Business')
const dmInvolved = ref('strong')
const criteria = ref(['Performance — Metal Loss', 'Performance — Colour'])
const trialBeforeDecision = ref(true)
const timeline = ref('Immediate (<1 month)')
const volume = ref('12')
const dealValue = ref('130000')
const forecast = ref('Pipeline')
const trialRequired = ref('y')
const assignTech = ref('y')
const techCategory = ref('Alloys — Pankaj')
const assignNotes = ref('Casting yield ~8% loss')

const productSummary = 'Alloys → Casting Alloys → Yellow Gold'

const oppTypeOptions = ['New Business', 'New Product', 'Expansion', 'Win-back']
const dmOptions = [
  { label: __('Yes — Strong Deal'), value: 'strong' },
  { label: __('Partial'), value: 'weak' },
  { label: __('No'), value: 'no' },
]
const criteriaOptions = [
  'Performance — Metal Loss',
  'Performance — Colour',
  'Price — Competitive',
  'Delivery — Lead Time',
]
const timelineOptions = [
  'Immediate (<1 month)',
  'Short (<2 months)',
  'Medium (3-6 months)',
  'Long (6 months+)',
]
const forecastOptions = ['Pipeline', 'Best Case', 'Commit', 'Omitted']
const yesNoOptions = [
  { label: __('Yes'), value: 'y' },
  { label: __('No'), value: 'n' },
]
const techCategoryOptions = [
  'Alloys — Pankaj',
  'Plating — Akshay',
  'Machines — Manoj',
]

function toggle(list, item) {
  const i = list.value.indexOf(item)
  if (i === -1) list.value = [...list.value, item]
  else list.value = list.value.filter((x) => x !== item)
}
</script>
