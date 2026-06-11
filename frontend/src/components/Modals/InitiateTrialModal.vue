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
          :error="errors.oppType"
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
        :error="errors.dmInvolved"
        class="mb-3"
      />
      <div class="mb-1.5 text-sm text-ink-gray-5">
        {{ __('Decision Criteria (multi-select)') }}
      </div>
      <div class="mb-3.5 grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
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
          :error="errors.timeline"
        />
        <FieldText
          v-model="volume"
          type="number"
          :label="__('Expected Monthly Volume (KG)')"
          required
          :error="errors.volume"
        />
        <FieldText
          v-model="dealValue"
          type="number"
          :label="__('Deal Value (INR)')"
          required
          :error="errors.dealValue"
        />
        <FieldSelect
          v-model="forecast"
          :label="__('Forecast Category')"
          required
          :options="forecastOptions"
          :error="errors.forecast"
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
          :error="errors.techCategory"
          :help="__('Auto-routed by category × region')"
        />
        <FieldText v-model="assignNotes" :label="__('Assignment Notes')" />
      </FieldGrid>
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Save Draft')" @click="saveDraft" />
        <Button
          variant="solid"
          :label="__('Assign & Notify Tech Team')"
          :loading="assigning"
          @click="assignAndNotify"
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
import { Button, call, createResource, toast } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save'])

const oppType = ref('')
const dmInvolved = ref('')
const criteria = ref([])
const trialBeforeDecision = ref(false)
const timeline = ref('')
const volume = ref('')
const dealValue = ref('')
const forecast = ref('')
const trialRequired = ref('y')
const assignTech = ref('y')
const techCategory = ref('')
const assignNotes = ref('')
const assigning = ref(false)

const oppTypeOptions = ['New Business', 'New Product', 'Expansion', 'Win-back']
const dmOptions = [
  { label: __('Yes — Strong Deal'), value: 'Yes — Strong Deal' },
  { label: __('Partial'), value: 'Partial' },
  { label: __('No'), value: 'No' },
]
// each criterion is a Check field on CRM Deal
const CRITERIA_FIELDS = [
  { key: 'dc_performance_metal_loss', label: 'Performance — Metal Loss' },
  { key: 'dc_performance_colour', label: 'Performance — Colour' },
  { key: 'dc_price_competitive', label: 'Price — Competitive' },
  { key: 'dc_delivery_lead_time', label: 'Delivery — Lead Time' },
]
const criteriaOptions = CRITERIA_FIELDS.map((c) => c.label)
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

// Tech Team options come from the CRM Tech Team doctype; label reads as
// "Category — Member First Name" (as in the prototype), value is the record name.
const techTeamResource = createResource({
  url: 'crm.api.tech_team.get_tech_teams',
  auto: true,
})
const techCategoryOptions = computed(() => techTeamResource.data || [])
const techCategoryValues = computed(() =>
  (techTeamResource.data || []).map((o) => o.value),
)

const productSummary = computed(() => {
  const d = props.deal || {}
  return [d.product_category, d.product_sub_category, d.product_variant]
    .filter(Boolean)
    .join(' → ')
})

onMounted(() => {
  const d = props.deal || {}
  oppType.value = d.opportunity_type || 'New Business'
  dmInvolved.value = d.decision_maker_involved || ''
  criteria.value = CRITERIA_FIELDS.filter((c) => d[c.key]).map((c) => c.label)
  trialBeforeDecision.value = !!d.trial_required_before_decision
  timeline.value = d.decision_timeline || ''
  volume.value = d.expected_monthly_volume ? String(d.expected_monthly_volume) : ''
  dealValue.value = d.deal_value ? String(d.deal_value) : ''
  forecast.value = d.forecast_category || ''
  trialRequired.value = d.trial_required ? 'y' : 'n'
  assignTech.value = d.assign_to_tech_team === 0 ? 'n' : 'y'
  techCategory.value = d.tech_team_category || ''
  assignNotes.value = d.assignment_notes || ''
})

function toggle(list, item) {
  const i = list.value.indexOf(item)
  if (i === -1) list.value = [...list.value, item]
  else list.value = list.value.filter((x) => x !== item)
}

function buildValues() {
  const values = {
    opportunity_type: oppType.value || null,
    decision_maker_involved: dmInvolved.value || null,
    trial_required_before_decision: trialBeforeDecision.value ? 1 : 0,
    decision_timeline: timeline.value || null,
    expected_monthly_volume: parseFloat(volume.value) || 0,
    deal_value: parseFloat(dealValue.value) || 0,
    forecast_category: forecast.value || null,
    trial_required: trialRequired.value === 'y' ? 1 : 0,
    assign_to_tech_team: assignTech.value === 'y' ? 1 : 0,
    tech_team_category: techCategory.value || null,
    assignment_notes: assignNotes.value || '',
  }
  CRITERIA_FIELDS.forEach(
    (c) => (values[c.key] = criteria.value.includes(c.label) ? 1 : 0),
  )
  return values
}

function saveDraft() {
  emit('save', { values: buildValues(), advance: false })
  show.value = false
}

// validation — errors surface only after an assign attempt, then clear live
const attempted = ref(false)
const requiredFields = [
  { key: 'oppType', label: __('Opportunity Type'), val: () => oppType.value },
  { key: 'dmInvolved', label: __('Decision Maker Involved?'), val: () => dmInvolved.value },
  { key: 'timeline', label: __('Decision Timeline'), val: () => timeline.value },
  { key: 'volume', label: __('Expected Monthly Volume'), val: () => volume.value },
  { key: 'dealValue', label: __('Deal Value'), val: () => dealValue.value },
  { key: 'forecast', label: __('Forecast Category'), val: () => forecast.value },
]
function techCategoryError() {
  if (!techCategory.value) return __('Required')
  if (!techCategoryValues.value.includes(techCategory.value))
    return __('Select a configured Tech Team category')
  return ''
}
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  for (const f of requiredFields) if (!f.val()) e[f.key] = __('Required')
  const techErr = techCategoryError()
  if (techErr) e.techCategory = techErr
  return e
})

async function assignAndNotify() {
  attempted.value = true
  const missing = requiredFields.filter((f) => !f.val()).map((f) => f.label)
  if (techCategoryError()) {
    missing.push(__('Tech Team Category'))
  }
  if (missing.length) {
    toast.error(__('Please fill all required fields: {0}', [missing.join(', ')]))
    return
  }

  const values = buildValues()
  if (assignTech.value === 'y') {
    assigning.value = true
    try {
      const member = await call('crm.api.tech_team.assign_tech_team', {
        deal: props.deal?.name,
        tech_team: techCategory.value,
        notes: assignNotes.value,
      })
      values.assigned_tech_member = member
      toast.success(__('Assigned to {0}', [member]))
    } catch (err) {
      toast.error(err.messages?.[0] || __('Error assigning tech team'))
      assigning.value = false
      return
    }
    assigning.value = false
  }

  emit('save', { values, advance: true })
  show.value = false
}
</script>
