<template>
  <StageFormDialog
    v-model="show"
    :statusLabel="statusLabel"
    :subtitle="subtitle"
    :steps="steps"
  >
    <template #default="{ step }">
    <div v-show="step === 0">
    <StageCallout theme="green" icon="check" class="mb-3">
      {{
        __(
          'Qualify the commercial opportunity — decision maker, criteria, volume and value. The trial decision & tech assignment come next.',
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
        <span class="text-ink-red-3">*</span>
      </div>
      <div class="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
        <FieldCheckbox
          v-for="c in criteriaOptions"
          :key="c"
          :label="c"
          :checked="criteria.includes(c)"
          @change="toggleCriteria(c)"
        />
      </div>
      <div v-if="errors.criteria" class="mt-1 text-xs text-ink-red-3">
        {{ errors.criteria }}
      </div>
      <div class="my-3.5 h-px bg-outline-gray-2" />
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="timeline"
          :label="__('Decision Timeline')"
          required
          :options="timelineOptions"
          :error="errors.timeline"
        />
        <FieldSelect
          v-model="forecast"
          :label="__('Forecast Category')"
          required
          :options="forecastOptions"
          :error="errors.forecast"
        />
        <FieldText
          v-model="volume"
          type="number"
          :label="__('Expected Monthly Volume')"
          required
          :error="errors.volume"
        />
        <div>
          <div class="mb-1.5 text-sm text-ink-gray-5">
            {{ __('Unit') }} <span class="text-ink-red-3">*</span>
          </div>
          <Link
            class="form-control"
            :value="volumeUom"
            doctype="UOM"
            :filters="uomFilters"
            :placeholder="__('Select unit')"
            @change="(v) => (volumeUom = v)"
          />
          <div v-if="errors.volumeUom" class="mt-1 text-xs text-ink-red-3">
            {{ errors.volumeUom }}
          </div>
        </div>
        <FieldText
          v-model="dealValue"
          type="number"
          :label="__('Deal Value (INR)')"
          required
          :error="errors.dealValue"
        />
      </FieldGrid>
    </StageSection>
    </div>

    <div v-show="step === 1">
    <StageCallout theme="blue" icon="beaker" class="mb-3">
      {{
        __(
          'Make the trial decision and assign the tech team. On save, the team is auto-assigned by Product Category × Region and the waiting-time clock starts.',
        )
      }}
    </StageCallout>

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
          :label="__('Technical Person')"
          :required="assignTech === 'y'"
          :options="techCategoryOptions"
          :error="errors.techCategory"
          :help="__('Auto-routed by category × region')"
        />
        <FieldText
          v-model="evalStart"
          type="date"
          :label="__('Trial Start Date')"
          :required="trialRequired === 'y'"
          :error="errors.evalStart"
        />
      </FieldGrid>
      <FieldGrid :cols="2" class="mt-1">
        <FieldText v-model="assignNotes" :label="__('Assignment Notes')" />
      </FieldGrid>
    </StageSection>
    </div>
    </template>

    <template #actions="{ step, next, back, isLast }">
      <div class="flex w-full items-center gap-2">
        <Button v-if="step === 0" :label="__('Save Draft')" @click="saveDraft" />
        <Button v-else :label="__('Back')" @click="back">
          <template #prefix><StageIcon name="arrowLeft" class="h-4 w-4" /></template>
        </Button>
        <span class="flex-1" />
        <Button
          v-if="!isLast"
          variant="solid"
          :label="__('Next: Technical Assignment')"
          @click="next"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else
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
import Link from '@/components/Controls/Link.vue'
import { Button, call, createResource, toast } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save'])

// wizard steps: commercial qualification first, technical assignment last
const steps = [
  { label: __('Commercial Qualification') },
  { label: __('Technical Assignment') },
]

const oppType = ref('')
const dmInvolved = ref('')
const criteria = ref([])
const timeline = ref('')
const volume = ref('')
const volumeUom = ref('')
const dealValue = ref('')
const forecast = ref('')
const trialRequired = ref('y')
const assignTech = ref('y')
const techCategory = ref('')
const evalStart = ref('')
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
  params: {
    territory: props.deal?.territory,
    product_category: props.deal?.product_category,
  },
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

// Allowed units per product category (UOM master names, seeded via fixture).
const UOM_BY_CATEGORY = {
  Alloys: ['Gram', 'Kg'],
  Plating: ['Millilitre', 'Litre', 'Pieces'],
  Machines: ['Pieces', 'Nos'],
}
const uomFilters = computed(() => {
  const allowed = UOM_BY_CATEGORY[props.deal?.product_category]
  return allowed ? { name: ['in', allowed] } : {}
})

onMounted(() => {
  const d = props.deal || {}
  oppType.value = d.opportunity_type || 'New Business'
  dmInvolved.value = d.decision_maker_involved || ''
  criteria.value = CRITERIA_FIELDS.filter((c) => d[c.key]).map((c) => c.label)
  timeline.value = d.decision_timeline || ''
  volume.value = d.expected_monthly_volume ? String(d.expected_monthly_volume) : ''
  volumeUom.value = d.expected_monthly_volume_uom || ''
  dealValue.value = d.deal_value ? String(d.deal_value) : ''
  forecast.value = d.forecast_category || ''
  trialRequired.value = d.trial_required === 0 ? 'n' : 'y'
  assignTech.value = d.assign_to_tech_team === 0 ? 'n' : 'y'
  techCategory.value = d.technical_person || ''
  evalStart.value = d.evaluation_start || ''
  assignNotes.value = d.assignment_notes || ''
})

function toggleCriteria(item) {
  if (criteria.value.includes(item))
    criteria.value = criteria.value.filter((x) => x !== item)
  else criteria.value = [...criteria.value, item]
}

function buildValues() {
  const values = {
    opportunity_type: oppType.value || null,
    decision_maker_involved: dmInvolved.value || null,
    decision_timeline: timeline.value || null,
    expected_monthly_volume: parseFloat(volume.value) || 0,
    expected_monthly_volume_uom: volumeUom.value || null,
    deal_value: parseFloat(dealValue.value) || 0,
    forecast_category: forecast.value || null,
    trial_required: trialRequired.value === 'y' ? 1 : 0,
    assign_to_tech_team: assignTech.value === 'y' ? 1 : 0,
    technical_person: techCategory.value || null,
    evaluation_start: evalStart.value || null,
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
  { key: 'criteria', label: __('Decision Criteria'), val: () => criteria.value.length },
  { key: 'timeline', label: __('Decision Timeline'), val: () => timeline.value },
  { key: 'volume', label: __('Expected Monthly Volume'), val: () => volume.value },
  { key: 'volumeUom', label: __('Unit'), val: () => volumeUom.value },
  { key: 'dealValue', label: __('Deal Value'), val: () => dealValue.value },
  { key: 'forecast', label: __('Forecast Category'), val: () => forecast.value },
  { key: 'evalStart', label: __('Trial Start Date'), val: () => trialRequired.value !== 'y' || evalStart.value },
]
function techCategoryError() {
  // Technical Person is only required when assigning to the tech team.
  if (assignTech.value !== 'y') return ''
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
    missing.push(__('Technical Person'))
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

  // Every deal advances to Tech Assignment next, where the tech team recommends a
  // product. The trial / no-trial branch is applied there (trial → Technical
  // Evaluation, no trial → straight to the quotation flow). Emit the explicit target
  // so the move never depends on the cached status order.
  emit('save', { values, advance: true, status: 'Tech Assignment' })
  show.value = false
}
</script>
