<template>
  <StageFormDialog
    v-model="show"
    :title="__('Repeat Order')"
    :subtitle="subtitle"
    size="xl"
  >
    <StageCallout theme="green" icon="zap" class="mb-3">
      {{
        __(
          'Repeat order for an already-trialed product. On submit a deal is created directly at the Proposal/Quotation stage.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Product Selection — trialed products')" icon="package">
      <p v-if="!trialed.length" class="mb-3 text-p-sm text-ink-gray-5">
        {{ __('No trialed products found for this organization.') }}
      </p>
      <FieldGrid v-else :cols="3">
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

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Submit & Create Deal')"
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
import { usersStore } from '@/stores/users'
import { Button, createResource, toast } from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  org: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const router = useRouter()
const { getUser } = usersStore()

// ---- already-trialed products for this organization ----
const trialed = ref([])
createResource({
  url: 'crm.fcrm.doctype.crm_deal.crm_deal.get_trialed_products',
  params: { organization: props.org },
  auto: true,
  onSuccess: (d) => (trialed.value = d || []),
})

const categories = computed(() => [
  ...new Set(trialed.value.map((r) => r.product_category).filter(Boolean)),
])
const subs = computed(() => [
  ...new Set(
    trialed.value
      .filter((r) => r.product_category === cat.value)
      .map((r) => r.product_sub_category)
      .filter(Boolean),
  ),
])
const variants = computed(() => [
  ...new Set(
    trialed.value
      .filter(
        (r) =>
          r.product_category === cat.value &&
          r.product_sub_category === sub.value,
      )
      .map((r) => r.product_variant)
      .filter(Boolean),
  ),
])

// ---- quotation-stage data derived from the organization ----
const orgData = ref({})
createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Organization',
    filters: props.org,
    fieldname: ['territory', 'gstin', 'address', 'organization_name'],
  },
  auto: true,
  onSuccess: (d) => (orgData.value = d || {}),
})

const cat = ref('')
const sub = ref('')
const variant = ref('')
const creating = ref(false)

const attempted = ref(false)
const fieldValues = { cat, sub, variant }
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
}
function onSubChange(v) {
  sub.value = v
  variant.value = ''
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
        territory: orgData.value.territory || '',
        status: 'Proposal/Quotation',
        repeat_deal: 1,
        deal_owner: getUser().name,
        product_category: cat.value,
        product_sub_category: sub.value,
        product_variant: variant.value,
        legal_name: orgData.value.organization_name || '',
        gstin: orgData.value.gstin || '',
        billing_address: orgData.value.address || '',
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
