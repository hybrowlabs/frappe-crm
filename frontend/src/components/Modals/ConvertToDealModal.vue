<template>
  <StageFormDialog
    v-model="show"
    :title="__('Convert to Deal')"
    :subtitle="subtitle"
    size="xl"
  >
    <StageCallout theme="blue" icon="fileText" class="mb-4">
      {{ __('A') }} <b>{{ __('GST number') }}</b>
      {{
        __(
          'is required to create the customer account and enable quotation & invoicing.',
        )
      }}
    </StageCallout>

    <FieldSelect
      v-model="gstType"
      :label="__('GST Registration Type')"
      required
      :options="gstTypeOptions"
    />

    <template v-if="!exempt">
      <FieldText
        v-model="gstin"
        :label="__('GSTIN')"
        required
        placeholder="27AABCM1234E1Z5"
        :help="gstinHelp"
        :error="errors.gstin"
      />
      <FieldText
        v-model="legalName"
        :label="__('Legal / Registered Name')"
        required
        :help="__('As per GST certificate')"
        :error="errors.legalName"
      />
      <StageCallout v-if="valid" theme="green" icon="check" class="mt-1">
        {{ __('State') }} <b>{{ fetchedState || stateCode }}</b>
        {{
          __(
            '· Deal territory and tax (CGST/SGST vs IGST) will be set from this GSTIN.',
          )
        }}
      </StageCallout>
    </template>
    <StageCallout v-else theme="amber" icon="alert" class="mt-1">
      {{
        __(
          'Unregistered — quotation allowed on advance payment only. No input tax credit; credit terms blocked.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Billing Address')" icon="building" class="mt-2">
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

    <StageSection :title="__('Shipping Address')" icon="package">
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

    <ErrorMessage class="mt-4" :message="error" />

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Convert & Open Deal')"
          :loading="converting"
          @click="convertToDeal"
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
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldGrid from '@/components/StageForms/FieldGrid.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import { useDocument } from '@/data/document'
import { sessionStore } from '@/stores/session'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Button, ErrorMessage, call, toast } from 'frappe-ui'
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: { type: Object, required: true },
})

const show = defineModel({ type: Boolean })

const router = useRouter()
const { user } = sessionStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

const { triggerConvertToDeal } = useDocument('CRM Lead', props.lead.name)
const { document: deal } = useDocument('CRM Deal')

const subtitle = computed(
  () =>
    [props.lead.organization, props.lead.lead_name].filter(Boolean).join(' · '),
)

const gstTypeOptions = [
  'Registered — Regular',
  'Registered — Composition',
  'SEZ / Export',
  'Unregistered / Composition',
]

const gstType = ref('Registered — Regular')
const gstin = ref('')
const legalName = ref(props.lead.organization || '')
const error = ref('')
const converting = ref(false)
const attempted = ref(false)
const gstinLoading = ref(false)
const fetchedState = ref('')
let lastFetchedGstin = ''

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

function resetAddress(target) {
  fillAddress(target, {})
}

watch(show, (val) => {
  if (val) {
    gstType.value = 'Registered — Regular'
    gstin.value = ''
    legalName.value = props.lead.organization || ''
    error.value = ''
    attempted.value = false
    fetchedState.value = ''
    lastFetchedGstin = ''
    resetAddress(billing)
    resetAddress(shipping)
    sameAsBilling.value = true
  }
})

// GSTIN format: 2 digit state + 5 letters + 4 digits + 1 letter + 1 entity + Z + 1 checksum = 15
const clean = computed(() => gstin.value.toUpperCase().replace(/\s/g, ''))
const valid = computed(() =>
  /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/.test(clean.value),
)
const stateCode = computed(() => clean.value.slice(0, 2))
const exempt = computed(() => gstType.value === 'Unregistered / Composition')

const gstinHelp = computed(() => {
  if (gstinLoading.value) return __('Fetching GST details…')
  if (!gstin.value)
    return __('15-character GSTIN — 2-digit state code + 10-char PAN + 3 suffix')
  if (valid.value)
    return __('Valid format') + (fetchedState.value ? ` · ${fetchedState.value} (${stateCode.value})` : '')
  return __('{0}/15 characters — check the format', [clean.value.length])
})

// Auto-fetch the legal name from the GSTIN via india_compliance.
watch(clean, (value) => {
  fetchedState.value = ''
  if (!valid.value || value === lastFetchedGstin) return
  lastFetchedGstin = value
  fetchGstinInfo(value)
})

async function fetchGstinInfo(value) {
  gstinLoading.value = true
  try {
    const info = await call(
      'india_compliance.gst_india.utils.gstin_info.get_gstin_info',
      { gstin: value },
    )
    if (info?.business_name) legalName.value = info.business_name
    if (info?.permanent_address?.state) fetchedState.value = info.permanent_address.state
    if (info?.permanent_address) fillAddress(billing, info.permanent_address)
    toast.success(__('GST details fetched'))
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not fetch GST details'))
  } finally {
    gstinLoading.value = false
  }
}

const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  if (!exempt.value) {
    if (!valid.value) e.gstin = __('Enter a valid 15-character GSTIN')
    if (!legalName.value) e.legalName = __('Required')
  }
  if (!billing.address_line1) e.billingLine1 = __('Required')
  if (!billing.city) e.billingCity = __('Required')
  if (!sameAsBilling.value) {
    if (!shipping.address_line1) e.shippingLine1 = __('Required')
    if (!shipping.city) e.shippingCity = __('Required')
  }
  return e
})

async function convertToDeal() {
  error.value = ''
  attempted.value = true
  if (Object.keys(errors.value).length) return

  if (!exempt.value) {
    deal.doc.gstin = clean.value
    deal.doc.legal_name = legalName.value
  }

  await triggerConvertToDeal?.(props.lead, deal.doc, () => (show.value = false))

  converting.value = true
  let newDeal = await call(
    'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal',
    {
      lead: props.lead.name,
      deal: deal.doc,
      existing_contact: '',
      existing_organization: '',
    },
  ).catch((err) => {
    error.value = __('Error converting to deal: {0}', [err.messages?.[0]])
  })
  converting.value = false

  if (newDeal) {
    await createDealAddresses(newDeal)
    show.value = false
    error.value = ''
    updateOnboardingStep('convert_lead_to_deal', true, false, () => {
      localStorage.setItem('firstDeal' + user, newDeal)
    })
    capture('convert_lead_to_deal')
    router.push({ name: 'Deal', params: { dealId: newDeal } })
  }
}

async function createDealAddresses(dealName) {
  const addressTitle = legalName.value || props.lead.organization || dealName
  const gstinValue = exempt.value ? '' : clean.value
  const links = [{ link_doctype: 'CRM Deal', link_name: dealName }]
  try {
    const billingAddress = await call('frappe.client.insert', {
      doc: {
        doctype: 'Address',
        address_title: addressTitle,
        address_type: 'Billing',
        gstin: gstinValue,
        ...billing,
        links,
      },
    })
    const updates = { billing_address: billingAddress.name }
    if (!sameAsBilling.value) {
      const shippingAddress = await call('frappe.client.insert', {
        doc: {
          doctype: 'Address',
          address_title: addressTitle,
          address_type: 'Shipping',
          gstin: gstinValue,
          ...shipping,
          links,
        },
      })
      updates.shipping_address = shippingAddress.name
    } else {
      updates.shipping_address = billingAddress.name
    }
    await call('frappe.client.set_value', {
      doctype: 'CRM Deal',
      name: dealName,
      fieldname: updates,
    })
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error creating address'))
  }
}
</script>
