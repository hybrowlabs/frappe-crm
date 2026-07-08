<template>
  <StageFormDialog
    v-model="show"
    :statusLabel="statusLabel"
    :subtitle="subtitle"
    :steps="steps"
  >
    <template #default="{ step }">
    <div v-show="step === 0">
    <!-- Product Selection -->
    <StageSection :title="__('Product Selection')" icon="package">
      <FieldGrid :cols="3">
        <FieldSelect
          v-model="cat"
          :label="__('Product Category')"
          required
          :options="categories"
          :placeholder="__('Select category')"
          :error="errors.cat"
          @update:modelValue="onCategoryChange"
        />
        <FieldSelect
          v-model="sub"
          :label="__('Sub-Category')"
          required
          :options="subs"
          :placeholder="__('Select sub-category')"
          :error="errors.sub"
          @update:modelValue="onSubChange"
        />
        <FieldSelect
          v-model="variant"
          :label="__('Variant')"
          required
          :options="variants"
          :placeholder="__('Select variant')"
          :error="errors.variant"
        />
      </FieldGrid>
    </StageSection>

    <!-- Commercial Pain Points -->
    <StageSection
      :title="
        sub
          ? __('Commercial Pain Points — {0} for {1}', [commercialPains.length, sub])
          : __('Commercial Pain Points')
      "
      icon="rupee"
    >
      <p v-if="!sub" class="text-p-sm text-ink-gray-5">
        {{ __('Select a sub-category to load relevant pain points.') }}
      </p>
      <p v-else-if="!commercialPains.length" class="text-p-sm text-ink-gray-5">
        {{ __('No commercial pain points mapped to this sub-category yet.') }}
      </p>
      <div
        v-if="sub && commercialPains.length"
        class="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-3"
      >
        <FieldCheckbox
          v-for="p in commercialPains"
          :key="p.name"
          :label="p.name"
          :checked="pains.includes(p.name)"
          @change="togglePain(p.name)"
        />
      </div>
    </StageSection>

    <!-- Technical Pain Points -->
    <StageSection
      :title="
        sub
          ? __('Technical Pain Points — {0} for {1}', [technicalPains.length, sub])
          : __('Technical Pain Points')
      "
      icon="alert"
    >
      <p v-if="!sub" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('Select a sub-category to load relevant pain points.') }}
      </p>
      <p v-else-if="!technicalPains.length" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('No technical pain points mapped to this sub-category yet.') }}
      </p>
      <div
        v-if="sub && technicalPains.length"
        class="mb-3.5 grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-3"
      >
        <FieldCheckbox
          v-for="p in technicalPains"
          :key="p.name"
          :label="p.name"
          :checked="pains.includes(p.name)"
          @change="togglePain(p.name)"
        />
      </div>
      <FieldText
        v-if="otherPainSelected"
        v-model="otherPainPoint"
        :label="__('Other Pain Point')"
        required
        :placeholder="__('Enter other pain point')"
        :error="errors.otherPainPoint"
        class="mb-3"
      />
      <div v-if="errors.pains" class="mb-3 text-xs text-ink-red-3">
        {{ errors.pains }}
      </div>
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="freq"
          :label="__('Pain Frequency')"
          required
          :options="freqOptions"
          :placeholder="__('Select frequency')"
          :error="errors.freq"
        />
        <FieldSelect
          v-model="severity"
          :label="__('Pain Severity')"
          required
          :options="severityOptions"
          :placeholder="__('Select severity')"
          :error="errors.severity"
        />
      </FieldGrid>
    </StageSection>

    <!-- Operational Impact -->
    <StageSection :title="__('Operational Impact')" icon="trendingUp">
      <p v-if="!cat" class="text-p-sm text-ink-gray-5">
        {{ __('Select a product category to load relevant operational impacts.') }}
      </p>
      <p v-else-if="!opImpactOpts.length" class="text-p-sm text-ink-gray-5">
        {{ __('No operational impacts mapped to this category yet.') }}
      </p>
      <div v-if="cat" class="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-2">
        <FieldCheckbox
          v-for="o in opImpactOpts"
          :key="o.name"
          :label="o.name"
          :checked="opImpacts.includes(o.name)"
          @change="toggleOpImpact(o.name)"
        />
        <FieldCheckbox
          :label="__('Other')"
          :checked="otherOperationalImpactSelected"
          @change="toggleOtherOperationalImpact"
        />
      </div>
      <FieldText
        v-if="otherOperationalImpactSelected"
        v-model="otherOperationalImpact"
        :label="__('Other Operational Impact')"
        required
        :placeholder="__('Enter other operational impact')"
        :error="errors.otherOperationalImpact"
        class="mt-3"
      />
      <div v-if="errors.opImpacts" class="mt-1 text-xs text-ink-red-3">
        {{ errors.opImpacts }}
      </div>
    </StageSection>
    </div>

    <div v-show="step === 1">
    <!-- Commercial Context -->
    <StageSection :title="__('Commercial Context')" icon="fileText">
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="supplier"
          :label="__('Current Supplier')"
          :options="supplierOptions"
          :placeholder="__('Select supplier')"
        />
        <div>
          <div class="mb-1.5 text-sm text-ink-gray-5">
            {{ __('Decision Maker') }} <span class="text-ink-red-3">*</span>
          </div>
          <Link
            class="form-control"
            :value="decisionMaker"
            doctype="Contact"
            :filters="contactFilters"
            :placeholder="__('Link to a Contact')"
            @change="(v) => (decisionMaker = v)"
          />
          <div v-if="errors.decisionMaker" class="mt-1 text-xs text-ink-red-3">
            {{ errors.decisionMaker }}
          </div>
        </div>
      </FieldGrid>
      <div class="my-3.5 h-px bg-outline-gray-2" />
      <FieldRadioGroup
        v-model="credit"
        :label="__('Credit Check')"
        inline
        :options="creditOptions"
        class="mb-3"
      />
      <StageCallout v-if="credit" theme="amber" icon="lock">
        <b>{{ __('Quotation locked') }}</b>
        {{
          __(
            'until Credit Control approves terms for this customer. Advance / 0 / 7 / 15 / 30 / 45 days.',
          )
        }}
      </StageCallout>
      <StageCallout v-else theme="gray" icon="clock">
        {{ __('Credit assessment not yet started.') }}
      </StageCallout>
      <div class="my-3.5 h-px bg-outline-gray-2" />
      <FieldTextarea
        v-model="requirementNote"
        :label="__('Requirement Note')"
        required
        :rows="2"
        :placeholder="__('Add requirement note')"
        :error="errors.requirementNote"
      />
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
          :label="__('Next: Commercial Context')"
          @click="next"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else
          variant="solid"
          :label="__('Mark Ready to Qualify')"
          @click="markReadyToQualify"
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
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import Link from '@/components/Controls/Link.vue'
import { Button, createListResource, toast } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save'])

// wizard steps: capture through operational impact first, commercial context last
const steps = [
  { label: __('Requirements & Impact') },
  { label: __('Commercial Context') },
]

// fields required to mark the deal ready to qualify (not enforced on draft)
const REQUIRED_FIELDS = [
  { key: 'cat', label: __('Product Category') },
  { key: 'sub', label: __('Sub-Category') },
  { key: 'variant', label: __('Variant') },
  { key: 'freq', label: __('Pain Frequency') },
  { key: 'severity', label: __('Pain Severity') },
  { key: 'requirementNote', label: __('Requirement Note') },
  { key: 'decisionMaker', label: __('Decision Maker') },
]

// ---- static select options (mirror the CRM Deal field definitions) ----
const freqOptions = ['Every Production Cycle', 'Weekly', 'Monthly', 'Occasional']
const severityOptions = ['Critical', 'High', 'Medium', 'Low']
const supplierOptions = ['Indian Supplier', 'Imported', 'In-house', 'None / New']
const creditOptions = [
  { label: __('Yes — credit assessed'), value: true },
  { label: __('No — pending'), value: false },
]
const OTHER_PAIN_POINT = 'Other'
// ---- live master data ----
const categoryList = createListResource({
  doctype: 'CRM Product Category',
  fields: ['name'],
  orderBy: 'product_category asc',
  pageLength: 0,
  auto: true,
})
const subCategoryList = createListResource({
  doctype: 'CRM Product Sub Category',
  fields: ['name'],
  orderBy: 'product_sub_category asc',
  pageLength: 0,
  auto: false,
})
const variantList = createListResource({
  doctype: 'CRM Product Variant',
  fields: ['name'],
  orderBy: 'product_variant asc',
  pageLength: 0,
  auto: false,
})
const painPointList = createListResource({
  doctype: 'CRM Pain Point',
  fields: ['name', 'pain_type'],
  orderBy: 'pain_point asc',
  pageLength: 0,
  auto: false,
})
const operationImpactList = createListResource({
  doctype: 'CRM Operation Impact',
  fields: ['name'],
  orderBy: 'operation_impact asc',
  pageLength: 0,
  auto: false,
})

// limit Decision Maker to contacts of the deal's organization
const contactFilters = computed(() => {
  const org = (props.deal || {}).organization
  return org ? { company_name: org } : {}
})

const categories = computed(() => (categoryList.data || []).map((d) => d.name))
const subs = computed(() => (subCategoryList.data || []).map((d) => d.name))
const variants = computed(() => (variantList.data || []).map((d) => d.name))
// Keep the catch-all "Other" option pinned to the end of the list, regardless of
// the alphabetical order the master data comes back in.
function otherLast(list) {
  return [...(list || [])].sort((a, b) => {
    const ao = a.name === OTHER_PAIN_POINT
    const bo = b.name === OTHER_PAIN_POINT
    return ao === bo ? 0 : ao ? 1 : -1
  })
}
const painOpts = computed(() => otherLast(painPointList.data))
// Pain points are captured in two parts — Technical and Commercial — driven by
// the master data's pain_type. The "Other" catch-all (pain_type Technical) stays
// pinned to the end of the Technical group via otherLast above.
const technicalPains = computed(() =>
  painOpts.value.filter((p) => p.pain_type === 'Technical'),
)
const commercialPains = computed(() =>
  painOpts.value.filter((p) => p.pain_type === 'Commercial'),
)
// Operational impact has its own dedicated "Other" checkbox rendered last, so
// drop any "Other" coming from the master data to avoid a duplicate.
const opImpactOpts = computed(() =>
  (operationImpactList.data || []).filter((d) => d.name !== OTHER_PAIN_POINT),
)
const otherPainSelected = computed(() => pains.value.includes(OTHER_PAIN_POINT))

function loadSubs(category) {
  if (!category) return
  subCategoryList.update({ filters: { product_category: category } })
  subCategoryList.reload()
}
function loadVariants(subCat) {
  if (!subCat) return
  // a variant maps to many sub-categories via its product_sub_categories
  // multiselect child table — filter the parent through that child
  variantList.update({
    filters: [
      ['CRM Product Sub Category Select', 'product_sub_category', '=', subCat],
    ],
  })
  variantList.reload()
}
function loadPains(subCategory) {
  if (!subCategory) {
    painPointList.data = []
    return
  }
  // filter the parent via its Sub-Category multiselect child table
  painPointList.update({
    filters: [
      ['CRM Product Sub Category Select', 'product_sub_category', '=', subCategory],
    ],
  })
  painPointList.reload()
}
function loadOpImpacts(category) {
  if (!category) {
    operationImpactList.data = []
    return
  }
  operationImpactList.update({ filters: { product_category: category } })
  operationImpactList.reload()
}

// ---- form state (prefilled from the deal) ----
const cat = ref('')
const sub = ref('')
const variant = ref('')
const pains = ref([])
const otherPainPoint = ref('')
const freq = ref('')
const severity = ref('')
const opImpacts = ref([])
const otherOperationalImpactSelected = ref(false)
const otherOperationalImpact = ref('')
const requirementNote = ref('')
const supplier = ref('')
const decisionMaker = ref('')
const credit = ref(false)

// validation — errors only surface after a qualify attempt, then clear live
const attempted = ref(false)
const fieldValues = {
  cat,
  sub,
  variant,
  freq,
  severity,
  requirementNote,
  decisionMaker,
}
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  for (const f of REQUIRED_FIELDS) {
    if (!fieldValues[f.key].value) e[f.key] = __('Required')
  }
  if (otherPainSelected.value && !otherPainPoint.value.trim()) {
    e.otherPainPoint = __('Required')
  }
  if (!pains.value.length) {
    e.pains = __('Select at least one pain point')
  }
  if (!opImpacts.value.length && !otherOperationalImpactSelected.value) {
    e.opImpacts = __('Select at least one operational impact')
  }
  if (
    otherOperationalImpactSelected.value &&
    !otherOperationalImpact.value.trim()
  ) {
    e.otherOperationalImpact = __('Required')
  }
  return e
})

onMounted(() => {
  const d = props.deal || {}
  cat.value = d.product_category || ''
  sub.value = d.product_sub_category || ''
  variant.value = d.product_variant || ''
  pains.value = (d.pain_points || []).map((r) => r.pain_point)
  otherPainPoint.value = d.other_pain_point || ''
  if (otherPainPoint.value && !pains.value.includes(OTHER_PAIN_POINT)) {
    pains.value = [...pains.value, OTHER_PAIN_POINT]
  }
  freq.value = d.pain_frequency || ''
  severity.value = d.pain_severity || ''
  opImpacts.value = (d.operational_impacts || []).map((r) => r.operation_impact)
  otherOperationalImpact.value = d.other_operational_impact || ''
  otherOperationalImpactSelected.value = !!otherOperationalImpact.value
  requirementNote.value = d.requirement_note || ''
  supplier.value = d.current_supplier || ''
  decisionMaker.value = d.decision_maker || ''
  credit.value = !!d.credit_check

  // hydrate dependent dropdowns for the already-selected values
  if (cat.value) {
    loadSubs(cat.value)
    loadOpImpacts(cat.value)
  }
  if (sub.value) {
    loadVariants(sub.value)
    loadPains(sub.value)
  }
})

function onCategoryChange(v) {
  cat.value = v
  sub.value = ''
  variant.value = ''
  pains.value = []
  otherPainPoint.value = ''
  opImpacts.value = []
  otherOperationalImpactSelected.value = false
  otherOperationalImpact.value = ''
  requirementNote.value = ''
  variantList.data = []
  painPointList.data = []
  operationImpactList.data = []
  loadSubs(v)
  loadOpImpacts(v)
}

function onSubChange(v) {
  sub.value = v
  variant.value = ''
  // pain points are filtered by sub-category — reload on every sub change
  pains.value = []
  otherPainPoint.value = ''
  loadVariants(v)
  loadPains(v)
}

function togglePain(p) {
  if (pains.value.includes(p)) {
    pains.value = pains.value.filter((x) => x !== p)
    if (p === OTHER_PAIN_POINT) otherPainPoint.value = ''
    return
  }
  pains.value = [...pains.value, p]
}

function toggleOpImpact(o) {
  opImpacts.value = opImpacts.value.includes(o)
    ? opImpacts.value.filter((x) => x !== o)
    : [...opImpacts.value, o]
}

function toggleOtherOperationalImpact() {
  otherOperationalImpactSelected.value = !otherOperationalImpactSelected.value
  if (!otherOperationalImpactSelected.value) otherOperationalImpact.value = ''
}

function buildValues() {
  const values = {
    product_category: cat.value || null,
    product_sub_category: sub.value || null,
    product_variant: variant.value || null,
    pain_points: pains.value.map((p) => ({ pain_point: p })),
    other_pain_point: otherPainSelected.value ? otherPainPoint.value.trim() : '',
    pain_frequency: freq.value || '',
    pain_severity: severity.value || '',
    operational_impacts: opImpacts.value.map((o) => ({ operation_impact: o })),
    other_operational_impact: otherOperationalImpactSelected.value
      ? otherOperationalImpact.value.trim()
      : '',
    requirement_note: requirementNote.value.trim(),
    current_supplier: supplier.value || '',
    decision_maker: decisionMaker.value || null,
    credit_check: credit.value ? 1 : 0,
  }
  return values
}

function saveDraft() {
  // drafts persist as-is — no required-field validation
  attempted.value = false
  emit('save', { values: buildValues(), advance: false })
  show.value = false
}

function markReadyToQualify() {
  attempted.value = true
  const missing = REQUIRED_FIELDS.filter((f) => !fieldValues[f.key].value)
  if (!pains.value.length) {
    missing.push({ key: 'pains', label: __('Pain Point') })
  }
  if (otherPainSelected.value && !otherPainPoint.value.trim()) {
    missing.push({ key: 'otherPainPoint', label: __('Other Pain Point') })
  }
  if (!opImpacts.value.length && !otherOperationalImpactSelected.value) {
    missing.push({ key: 'opImpacts', label: __('Operational Impact') })
  }
  if (
    otherOperationalImpactSelected.value &&
    !otherOperationalImpact.value.trim()
  ) {
    missing.push({
      key: 'otherOperationalImpact',
      label: __('Other Operational Impact'),
    })
  }
  if (missing.length) {
    toast.error(
      __('Please fill all required fields: {0}', [
        missing.map((f) => f.label).join(', '),
      ]),
    )
    return
  }
  // advance: true → Deal.vue moves the deal to the next stage (Qualified)
  emit('save', { values: buildValues(), advance: true })
  show.value = false
}
</script>
