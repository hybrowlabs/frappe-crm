<template>
  <StageFormDialog
    v-model="show"
    :title="__('New Deal')"
    :subtitle="subtitle"
    size="2xl"
  >
    <StageCallout theme="blue" icon="zap" class="mb-3">
      {{ __('Confirm this is') }} <b>{{ __('new business') }}</b>
      {{
        __(
          '— not a reorder. Capture the trigger, product interest and pain points to start the deal at Requirements Discussion.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Why are you converting?')" icon="zap">
      <FieldRadioGroup
        v-model="why"
        :options="whyOptions"
        :error="errors.why"
      />
    </StageSection>

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

    <StageSection
      :title="
        cat
          ? __('Pain Points — {0} options for {1}', [painOpts.length, cat])
          : __('Pain Points')
      "
      icon="alert"
    >
      <p v-if="!cat" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('Select a product category to load relevant pain points.') }}
      </p>
      <p v-else-if="!painOpts.length" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('No pain points mapped to this category yet.') }}
      </p>
      <div v-else class="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-3">
        <FieldCheckbox
          v-for="p in painOpts"
          :key="p.name"
          :label="p.name"
          :checked="pains.includes(p.name)"
          @change="togglePain(p.name)"
        />
      </div>
    </StageSection>

    <StageSection :title="__('Timeline')" icon="clock">
      <FieldSelect
        v-model="timeline"
        :label="__('Close Timeline')"
        required
        :options="timelineOptions"
        :placeholder="__('Select timeline')"
        :error="errors.timeline"
      />
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create & Open Deal')"
          :loading="creating"
          @click="createDeal"
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
import { usersStore } from '@/stores/users'
import { Button, createResource, createListResource, toast } from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  org: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const router = useRouter()
const { getUser } = usersStore()

const whyOptions = [
  __('New product or application — first time enquiry'),
  __('Existing customer wants to try a different product'),
  __('Problem identified — needs technical recommendation'),
  __('Trial requested by customer'),
]
const timelineOptions = [
  'Immediate (<1 month)',
  'Short (<2 months)',
  'Medium (3-6 months)',
]

// ---- live master data (mirrors CaptureRequirementsModal) ----
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
  variantList.update({
    filters: [
      ['CRM Product Sub Category Select', 'product_sub_category', '=', subCat],
    ],
  })
  variantList.reload()
}
function loadPains(category) {
  if (!category) {
    painPointList.data = []
    return
  }
  painPointList.update({
    filters: [
      ['CRM Product Category Select', 'product_category', '=', category],
    ],
  })
  painPointList.reload()
}

// ---- form state ----
const territory = ref('')
createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Organization',
    filters: props.org,
    fieldname: 'territory',
  },
  auto: true,
  onSuccess: (d) => (territory.value = d?.territory || ''),
})

const why = ref('')
const cat = ref('')
const sub = ref('')
const variant = ref('')
const pains = ref([])
const timeline = ref('')
const creating = ref(false)

const attempted = ref(false)
const fieldValues = { why, cat, sub, variant, timeline }
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  for (const k of Object.keys(fieldValues)) {
    if (!fieldValues[k].value) e[k] = __('Required')
  }
  return e
})

function onCategoryChange(v) {
  cat.value = v
  sub.value = ''
  variant.value = ''
  pains.value = []
  variantList.data = []
  painPointList.data = []
  loadSubs(v)
  loadPains(v)
}
function onSubChange(v) {
  sub.value = v
  variant.value = ''
  loadVariants(v)
}
function togglePain(p) {
  pains.value = pains.value.includes(p)
    ? pains.value.filter((x) => x !== p)
    : [...pains.value, p]
}

function createDeal() {
  attempted.value = true
  if (Object.keys(errors.value).length) return
  creating.value = true
  createResource({
    url: 'crm.fcrm.doctype.crm_deal.crm_deal.create_deal',
    params: {
      doc: {
        organization: props.org,
        territory: territory.value,
        status: 'Req. Discussion',
        deal_owner: getUser().name,
        conversion_reason: why.value,
        close_timeline: timeline.value,
        product_category: cat.value,
        product_sub_category: sub.value,
        product_variant: variant.value,
        pain_points: pains.value.map((p) => ({ pain_point: p })),
      },
    },
    auto: true,
    onSuccess(name) {
      creating.value = false
      show.value = false
      router.push({ name: 'Deal', params: { dealId: name } })
    },
    onError(err) {
      creating.value = false
      toast.error(err.messages?.[0] || __('Error creating deal'))
    },
  })
}
</script>
