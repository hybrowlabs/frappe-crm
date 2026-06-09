<template>
  <StageFormDialog
    v-model="show"
    :statusLabel="statusLabel"
    :subtitle="subtitle"
  >
    <!-- intro callout -->
    <StageCallout theme="blue" class="mb-3">
      <template #icon><ZapIcon /></template>
      <b>{{ __('3-layer pain capture.') }}</b>
      {{
        __(
          'Pain points auto-filter by Product Category → Sub-Category → Variant. Capture commercial & operational impact to qualify the opportunity.',
        )
      }}
    </StageCallout>

    <!-- Product Selection -->
    <StageSection :title="__('Product Selection')">
      <template #icon><PackageIcon /></template>
      <FieldGrid :cols="3">
        <FieldSelect
          v-model="cat"
          :label="__('Product Category')"
          required
          :options="categories"
          @update:modelValue="onCategoryChange"
        />
        <FieldSelect
          v-model="sub"
          :label="__('Sub-Category')"
          required
          :options="subs"
          @update:modelValue="onSubChange"
        />
        <FieldSelect
          v-model="variant"
          :label="__('Variant')"
          required
          :options="variants"
        />
      </FieldGrid>
    </StageSection>

    <!-- Pain Points -->
    <StageSection
      :title="
        __('Pain Points — {0} options for {1} → {2}', [
          painOpts.length,
          cat,
          variant,
        ])
      "
    >
      <template #icon><AlertIcon /></template>
      <div class="mb-3.5 grid grid-cols-3 gap-x-4 gap-y-2">
        <FieldCheckbox
          v-for="p in painOpts"
          :key="p"
          :label="p"
          :checked="pains.includes(p)"
          @change="togglePain(p)"
        />
      </div>
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="freq"
          :label="__('Pain Frequency')"
          required
          :options="freqOptions"
        />
        <FieldSelect
          v-model="severity"
          :label="__('Pain Severity')"
          required
          :options="severityOptions"
        />
      </FieldGrid>
    </StageSection>

    <!-- Operational Impact -->
    <StageSection :title="__('Operational Impact')">
      <template #icon><TrendingUpIcon /></template>
      <div class="grid gap-2">
        <FieldCheckbox
          v-for="o in opOptions"
          :key="o"
          :label="o"
          :checked="opImpact.includes(o)"
          @change="toggleOp(o)"
        />
      </div>
    </StageSection>

    <!-- Commercial Context -->
    <StageSection :title="__('Commercial Context')">
      <template #icon><FileTextIcon /></template>
      <FieldGrid :cols="2">
        <FieldSelect
          v-model="supplier"
          :label="__('Current Supplier')"
          :options="supplierOptions"
        />
        <FieldText
          v-model="dm"
          :label="__('Decision Maker')"
          required
          :help="__('Must link to a Contact record')"
        />
      </FieldGrid>
      <div class="my-3.5 h-px bg-outline-gray-2" />
      <FieldRadioGroup
        v-model="credit"
        :label="__('Credit Check')"
        required
        inline
        :options="creditOptions"
        class="mb-3"
      />
      <StageCallout v-if="credit" theme="amber">
        <template #icon><LockIcon /></template>
        <b>{{ __('Quotation locked') }}</b>
        {{
          __(
            'until Tejal (Credit Control) approves terms for this new customer. Advance / 0 / 7 / 15 / 30 / 45 days.',
          )
        }}
      </StageCallout>
      <StageCallout v-else theme="gray">
        <template #icon><ClockIcon /></template>
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
          <template #suffix><ArrowRightIcon class="h-4 w-4" /></template>
        </Button>
      </div>
    </template>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageSection from '@/components/StageForms/StageSection.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import FieldGrid from '@/components/StageForms/FieldGrid.vue'
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import PackageIcon from '@/components/Icons/PackageIcon.vue'
import FileTextIcon from '@/components/Icons/FileTextIcon.vue'
import ZapIcon from '@/components/StageForms/icons/ZapIcon.vue'
import AlertIcon from '@/components/StageForms/icons/AlertIcon.vue'
import TrendingUpIcon from '@/components/StageForms/icons/TrendingUpIcon.vue'
import LockIcon from '@/components/StageForms/icons/LockIcon.vue'
import ClockIcon from '@/components/StageForms/icons/ClockIcon.vue'
import ArrowRightIcon from '@/components/StageForms/icons/ArrowRightIcon.vue'
import { Button, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['ready'])

// ---- product tree & pain options (from the prototype) ----
const PRODUCT_TREE = {
  Alloys: {
    'Casting Alloys': ['Yellow Gold', 'White Gold', 'Rose Gold'],
    'Stamping Alloys': ['Yellow Gold 22K', 'Yellow Gold 18K'],
    'Solder Alloys': ['Easy', 'Medium', 'Hard'],
  },
  Plating: {
    Rhodium: ['Bright Rhodium', 'White Rhodium'],
    'Gold Plating': ['Hard Gold', 'Soft Gold'],
  },
  Machines: {
    'Casting Machine': ['VC-Series', 'IC-Series'],
    'Plating Line': ['Manual', 'Automatic'],
  },
}
const PAIN_OPTIONS = {
  'Yellow Gold': [
    'Porosity / Pin Holes',
    'Poor Casting Yield',
    'Shrinkage',
    'Fire Scale',
    'Hardness',
    'Brittleness',
    'Non-Fill',
    'Stone Breakage',
    'Colour Mismatch',
    'Discoloration',
    'High Rework',
    'Metal Loss',
    'Delayed Fulfillment',
    'Inconsistent Batches',
  ],
  _default: [
    'Porosity / Pin Holes',
    'Poor Yield',
    'Discoloration',
    'Hardness',
    'High Rework',
    'Metal Loss',
  ],
}

// ---- reactive form state (prototype defaults) ----
const cat = ref('Alloys')
const sub = ref('Casting Alloys')
const variant = ref('Yellow Gold')
const pains = ref(['Porosity / Pin Holes', 'Poor Casting Yield'])
const freq = ref('Every Production Cycle')
const severity = ref('Critical')
const opImpact = ref([
  'Production downtime due to casting failure',
  'Increased scrap and metal loss',
])
const supplier = ref('Indian Supplier')
const dm = ref('')
const credit = ref(true)

const categories = Object.keys(PRODUCT_TREE)
const freqOptions = ['Every Production Cycle', 'Weekly', 'Monthly', 'Occasional']
const severityOptions = ['Critical', 'High', 'Medium', 'Low']
const supplierOptions = ['Indian Supplier', 'Imported', 'In-house', 'None / New']
const opOptions = [
  'Production downtime due to casting failure',
  'Increased scrap and metal loss',
  'High rework cost',
  'Delayed order fulfillment',
]
const creditOptions = [
  { label: __('Yes — credit assessed'), value: true },
  { label: __('No — pending'), value: false },
]

const subs = computed(() => Object.keys(PRODUCT_TREE[cat.value] || {}))
const variants = computed(() => (PRODUCT_TREE[cat.value] || {})[sub.value] || [])
const painOpts = computed(() => PAIN_OPTIONS[variant.value] || PAIN_OPTIONS._default)

function onCategoryChange(v) {
  cat.value = v
  const firstSub = Object.keys(PRODUCT_TREE[v])[0]
  sub.value = firstSub
  variant.value = PRODUCT_TREE[v][firstSub][0]
  pains.value = []
}

function onSubChange(v) {
  sub.value = v
  variant.value = PRODUCT_TREE[cat.value][v][0]
}

function togglePain(p) {
  pains.value = pains.value.includes(p)
    ? pains.value.filter((x) => x !== p)
    : [...pains.value, p]
}

function toggleOp(o) {
  opImpact.value = opImpact.value.includes(o)
    ? opImpact.value.filter((x) => x !== o)
    : [...opImpact.value, o]
}

function saveDraft() {
  toast.success(__('Draft saved'))
}

function markReadyToQualify() {
  show.value = false
  emit('ready')
}
</script>
