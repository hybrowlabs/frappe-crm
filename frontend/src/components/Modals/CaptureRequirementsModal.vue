<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <!-- intro callout -->
    <StageCallout theme="blue" icon="zap" class="mb-3">
      <b>{{ __('3-layer pain capture.') }}</b>
      {{
        __(
          'Pain points auto-filter by Product Category → Sub-Category → Variant. Capture commercial & operational impact to qualify the opportunity.',
        )
      }}
    </StageCallout>

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

    <!-- Pain Points -->
    <StageSection
      :title="
        sub
          ? __('Pain Points — {0} options for {1}', [painOpts.length, sub])
          : __('Pain Points')
      "
      icon="alert"
    >
      <p v-if="!sub" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('Select a sub-category to load relevant pain points.') }}
      </p>
      <p v-else-if="!painOpts.length" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('No pain points mapped to this sub-category yet.') }}
      </p>
      <div v-else class="mb-3.5 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
        <FieldCheckbox
          v-for="p in painOpts"
          :key="p.name"
          :label="p.name"
          :checked="pains.includes(p.name)"
          @change="togglePain(p.name)"
        />
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
      <div class="grid gap-2">
        <FieldCheckbox
          v-for="o in OP_FIELDS"
          :key="o.key"
          :label="__(o.label)"
          :checked="opImpact[o.key]"
          @change="opImpact[o.key] = !opImpact[o.key]"
        />
      </div>
    </StageSection>

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
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Save Draft')" @click="saveDraft" />
        <Button
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
import Link from '@/components/Controls/Link.vue'
import { Button, createListResource, toast } from 'frappe-ui'
import { ref, reactive, computed, onMounted } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save'])

// fields required to mark the deal ready to qualify (not enforced on draft)
const REQUIRED_FIELDS = [
  { key: 'cat', label: __('Product Category') },
  { key: 'sub', label: __('Sub-Category') },
  { key: 'variant', label: __('Variant') },
  { key: 'freq', label: __('Pain Frequency') },
  { key: 'severity', label: __('Pain Severity') },
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
// operational-impact fields are fixed checkboxes on CRM Deal
const OP_FIELDS = [
  {
    key: 'production_downtime_due_to_casting_failure',
    label: 'Production downtime due to casting failure',
  },
  { key: 'increased_scrap_and_metal_loss', label: 'Increased scrap and metal loss' },
  { key: 'high_rework_cost', label: 'High rework cost' },
  { key: 'delayed_order_fulfillment', label: 'Delayed order fulfillment' },
]

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

const categories = computed(() => (categoryList.data || []).map((d) => d.name))
const subs = computed(() => (subCategoryList.data || []).map((d) => d.name))
const variants = computed(() => (variantList.data || []).map((d) => d.name))
const painOpts = computed(() => painPointList.data || [])

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
function loadPains(subCat) {
  if (!subCat) {
    painPointList.data = []
    return
  }
  // filter the parent via its Sub-Category multiselect child table
  painPointList.update({
    filters: [
      ['CRM Product Sub Category Select', 'product_sub_category', '=', subCat],
    ],
  })
  painPointList.reload()
}

// ---- form state (prefilled from the deal) ----
const cat = ref('')
const sub = ref('')
const variant = ref('')
const pains = ref([])
const freq = ref('')
const severity = ref('')
const opImpact = reactive({})
const supplier = ref('')
const decisionMaker = ref('')
const credit = ref(false)

// validation — errors only surface after a qualify attempt, then clear live
const attempted = ref(false)
const fieldValues = { cat, sub, variant, freq, severity, decisionMaker }
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  for (const f of REQUIRED_FIELDS) {
    if (!fieldValues[f.key].value) e[f.key] = __('Required')
  }
  return e
})

onMounted(() => {
  const d = props.deal || {}
  cat.value = d.product_category || ''
  sub.value = d.product_sub_category || ''
  variant.value = d.product_variant || ''
  pains.value = (d.pain_points || []).map((r) => r.pain_point)
  freq.value = d.pain_frequency || ''
  severity.value = d.pain_severity || ''
  OP_FIELDS.forEach((o) => (opImpact[o.key] = !!d[o.key]))
  supplier.value = d.current_supplier || ''
  decisionMaker.value = d.decision_maker || ''
  credit.value = !!d.credit_check

  // hydrate dependent dropdowns for the already-selected values
  if (cat.value) loadSubs(cat.value)
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
  variantList.data = []
  painPointList.data = []
  loadSubs(v)
}

function onSubChange(v) {
  sub.value = v
  variant.value = ''
  pains.value = []
  loadVariants(v)
  loadPains(v)
}

function togglePain(p) {
  pains.value = pains.value.includes(p)
    ? pains.value.filter((x) => x !== p)
    : [...pains.value, p]
}

function buildValues() {
  const values = {
    product_category: cat.value || null,
    product_sub_category: sub.value || null,
    product_variant: variant.value || null,
    pain_points: pains.value.map((p) => ({ pain_point: p })),
    pain_frequency: freq.value || '',
    pain_severity: severity.value || '',
    current_supplier: supplier.value || '',
    decision_maker: decisionMaker.value || null,
    credit_check: credit.value ? 1 : 0,
  }
  OP_FIELDS.forEach((o) => (values[o.key] = opImpact[o.key] ? 1 : 0))
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
