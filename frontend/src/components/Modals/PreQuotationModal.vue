<template>
  <StageFormDialog
    v-model="show"
    :title="__('Create Customer')"
    :subtitle="subtitle"
    size="2xl"
  >
    <StageSection :title="__('Customer')" icon="building">
      <div class="mb-3 flex items-center justify-between">
        <div class="text-base text-ink-gray-7">
          {{ __('Use an existing customer') }}
        </div>
        <Switch v-model="chooseExistingCustomer" />
      </div>

      <template v-if="chooseExistingCustomer">
        <Link
          :label="__('Customer') + ' *'"
          doctype="Customer"
          :value="existingCustomer"
          @change="existingCustomer = $event"
        />
        <ErrorMessage v-if="errors.existingCustomer" class="mt-1" :message="errors.existingCustomer" />
        <div class="mt-1 text-sm text-ink-gray-5">
          {{ gstinMatched
            ? __('Auto-selected by GSTIN. Change if needed.')
            : __('Pick the ERPNext customer to use for this quotation.') }}
        </div>
      </template>

      <template v-else>
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
            :help="gstinHelp"
            :error="errors.gstin"
          />
        </FieldGrid>
        <Link
          :label="__('Currency') + ' *'"
          doctype="Currency"
          :value="currency"
          @change="currency = $event"
        />
        <ErrorMessage v-if="errors.currency" class="mt-1" :message="errors.currency" />
      </template>
    </StageSection>

    <StageSection
      v-if="!chooseExistingCustomer"
      :title="__('Billing Address')"
      icon="building"
    >
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

    <StageSection
      v-if="!chooseExistingCustomer"
      :title="__('Shipping Address')"
      icon="package"
    >
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
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <div class="flex items-center gap-2">
          <Button
            v-if="!customerExists"
            :label="__('Skip customer creation')"
            @click="skip"
          />
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
import Link from '@/components/Controls/Link.vue'
import { Button, ErrorMessage, Switch, call, toast } from 'frappe-ui'
import { ref, reactive, computed, onMounted, watch } from 'vue'

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
const currency = ref(props.deal.currency || 'INR')
// Use-existing-customer option + selector.
const chooseExistingCustomer = ref(false)
const existingCustomer = ref('')
const gstinMatched = ref(false)
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
  // If the deal already carries a GSTIN, try to auto-select a matching customer.
  if (gstin.value) lookupCustomerByGstin(gstin.value)
})

// Find an existing ERPNext customer with this GSTIN and pre-select it.
async function lookupCustomerByGstin(value) {
  const clean = (value || '').toUpperCase().replace(/\s/g, '')
  if (!GSTIN_REGEX.test(clean)) return
  try {
    const rows = await call('frappe.client.get_list', {
      doctype: 'Customer',
      filters: { gstin: clean },
      fields: ['name'],
      limit_page_length: 1,
      order_by: 'creation asc',
    })
    if (rows && rows.length) {
      existingCustomer.value = rows[0].name
      chooseExistingCustomer.value = true
      gstinMatched.value = true
    } else {
      gstinMatched.value = false
    }
  } catch (e) {
    // non-fatal: user can still pick manually
  }
}

// Auto-fetch legal name + billing address from the GSTIN via india_compliance.
const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/
const gstinLoading = ref(false)
// Skip the value pre-filled from the deal so we don't overwrite saved details.
let lastFetchedGstin = (gstin.value || '').toUpperCase()

const gstinHelp = computed(() =>
  gstinLoading.value
    ? __('Fetching GST details…')
    : __('Required to invoice'),
)

watch(gstin, (value) => {
  const clean = (value || '').toUpperCase().replace(/\s/g, '')
  if (clean !== value) gstin.value = clean
  if (!GSTIN_REGEX.test(clean) || clean === lastFetchedGstin) return
  lastFetchedGstin = clean
  lookupCustomerByGstin(clean)
  if (!chooseExistingCustomer.value) fetchGstinInfo(clean)
})

async function fetchGstinInfo(value) {
  gstinLoading.value = true
  try {
    const info = await call(
      'india_compliance.gst_india.utils.gstin_info.get_gstin_info',
      { gstin: value },
    )
    if (info?.business_name) legalName.value = info.business_name
    if (info?.permanent_address) fillAddress(billing, info.permanent_address)
    toast.success(__('GST details fetched'))
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not fetch GST details'))
  } finally {
    gstinLoading.value = false
  }
}

const attempted = ref(false)
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  // Using an existing customer — only the selector is required.
  if (chooseExistingCustomer.value) {
    if (!existingCustomer.value) e.existingCustomer = __('Required')
    return e
  }
  if (!legalName.value) e.legalName = __('Required')
  if (!gstin.value) e.gstin = __('Required')
  if (!currency.value) e.currency = __('Required')
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
  if (chooseExistingCustomer.value) {
    emit('confirm', {
      existingCustomer: existingCustomer.value,
    })
  } else {
    emit('confirm', {
      legalName: legalName.value,
      gstin: gstin.value,
      currency: currency.value,
      billing: { ...billing },
      sameAsBilling: sameAsBilling.value,
      shipping: sameAsBilling.value ? { ...billing } : { ...shipping },
    })
  }
  show.value = false
}

// Skip customer creation entirely and advance to the next stage without a customer.
function skip() {
  emit('confirm', { skip: true })
  show.value = false
}
</script>
