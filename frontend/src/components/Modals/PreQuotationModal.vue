<template>
  <StageFormDialog
    v-model="show"
    :title="__('Prepare for Quotation')"
    :subtitle="subtitle"
    size="2xl"
  >
    <StageSection :title="__('Customer')" icon="building">
      <StageCallout
        :theme="customerExists ? 'green' : 'amber'"
        :icon="customerExists ? 'check' : 'alert'"
        class="mb-3"
      >
        <template v-if="customerExists">
          {{ __('Customer') }} <b>{{ org }}</b>
          {{ __('already exists in ERPNext — its master will be used.') }}
        </template>
        <template v-else>
          {{ __('No ERPNext customer yet — one will be') }}
          <b>{{ __('created') }}</b>
          {{ __('from these details before the quotation.') }}
        </template>
      </StageCallout>
      <FieldGrid :cols="2">
        <FieldText
          v-model="legalName"
          :label="__('Legal / Registered Name')"
          required
          :error="errors.legalName"
        />
        <FieldText
          v-model="gstin"
          :label="__('GSTIN')"
          required
          :help="__('Required to invoice')"
          :error="errors.gstin"
        />
      </FieldGrid>
    </StageSection>

    <StageSection :title="__('Billing Address')" icon="building">
      <FieldText
        v-model="billing.address_line1"
        :label="__('Address Line 1')"
        required
        :error="errors.billingLine1"
      />
      <FieldText v-model="billing.address_line2" :label="__('Address Line 2')" />
      <FieldGrid :cols="2">
        <FieldText
          v-model="billing.city"
          :label="__('City')"
          required
          :error="errors.billingCity"
        />
        <FieldText v-model="billing.state" :label="__('State')" />
      </FieldGrid>
      <FieldGrid :cols="2">
        <FieldText v-model="billing.pincode" :label="__('Pincode')" />
        <FieldText v-model="billing.country" :label="__('Country')" />
      </FieldGrid>
    </StageSection>

    <StageSection :title="__('Shipping & Freight')" icon="package">
      <FieldCheckbox
        :label="__('Shipping address same as billing')"
        :checked="sameAsBilling"
        @change="sameAsBilling = !sameAsBilling"
      />
      <template v-if="!sameAsBilling">
        <FieldText
          v-model="shipping.address_line1"
          :label="__('Address Line 1')"
          required
          :error="errors.shippingLine1"
          class="mt-2"
        />
        <FieldText v-model="shipping.address_line2" :label="__('Address Line 2')" />
        <FieldGrid :cols="2">
          <FieldText
            v-model="shipping.city"
            :label="__('City')"
            required
            :error="errors.shippingCity"
          />
          <FieldText v-model="shipping.state" :label="__('State')" />
        </FieldGrid>
        <FieldGrid :cols="2">
          <FieldText v-model="shipping.pincode" :label="__('Pincode')" />
          <FieldText v-model="shipping.country" :label="__('Country')" />
        </FieldGrid>
      </template>
      <FieldRadioGroup
        v-model="freight"
        :label="__('Freight')"
        required
        inline
        :options="freightOptions"
        class="mt-3"
      />
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="
            customerExists
              ? __('Proceed to Quotation')
              : __('Create Customer & Proceed')
          "
          @click="proceed"
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
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import { Button, call } from 'frappe-ui'
import { ref, reactive, computed, onMounted } from 'vue'

const props = defineProps({
  org: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  customerExists: { type: Boolean, default: false },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['confirm'])

const legalName = ref(props.deal.legal_name || props.org || '')
const gstin = ref(props.deal.gstin || '')
const billing = reactive({
  address_line1: '',
  address_line2: '',
  city: '',
  state: '',
  pincode: '',
  country: 'India',
})
const sameAsBilling = ref(true)
const shipping = reactive({
  address_line1: '',
  address_line2: '',
  city: '',
  state: '',
  pincode: '',
  country: 'India',
})
const freight = ref(props.deal.freight_terms || 'To Pay')

function fillAddress(target, addr) {
  target.address_line1 = addr.address_line1 || ''
  target.address_line2 = addr.address_line2 || ''
  target.city = addr.city || ''
  target.state = addr.state || ''
  target.pincode = addr.pincode || ''
  target.country = addr.country || 'India'
}

onMounted(async () => {
  const { billing_address, shipping_address } = props.deal
  if (billing_address) {
    const addr = await call('frappe.client.get', {
      doctype: 'Address',
      name: billing_address,
    })
    fillAddress(billing, addr)
  }
  sameAsBilling.value =
    !shipping_address || shipping_address === billing_address
  if (!sameAsBilling.value) {
    const addr = await call('frappe.client.get', {
      doctype: 'Address',
      name: shipping_address,
    })
    fillAddress(shipping, addr)
  }
})

const freightOptions = [
  { label: __('To Pay (customer pays carrier)'), value: 'To Pay' },
  { label: __('Charged (added to invoice)'), value: 'Charged' },
  { label: __('Paid upfront'), value: 'Paid Upfront' },
]

const attempted = ref(false)
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  if (!legalName.value) e.legalName = __('Required')
  if (!gstin.value) e.gstin = __('Required')
  if (!billing.address_line1) e.billingLine1 = __('Required')
  if (!billing.city) e.billingCity = __('Required')
  if (!sameAsBilling.value) {
    if (!shipping.address_line1) e.shippingLine1 = __('Required')
    if (!shipping.city) e.shippingCity = __('Required')
  }
  return e
})

function proceed() {
  attempted.value = true
  if (Object.keys(errors.value).length) return
  emit('confirm', {
    legalName: legalName.value,
    gstin: gstin.value,
    billing: { ...billing },
    sameAsBilling: sameAsBilling.value,
    shipping: sameAsBilling.value ? { ...billing } : { ...shipping },
    freight_terms: freight.value,
  })
  show.value = false
}
</script>
