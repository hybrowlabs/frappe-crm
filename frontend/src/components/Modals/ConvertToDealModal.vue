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
        {{ __('State') }} <b>{{ stateName || stateCode }}</b>
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
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import { useDocument } from '@/data/document'
import { sessionStore } from '@/stores/session'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Button, ErrorMessage, call } from 'frappe-ui'
import { ref, computed, watch } from 'vue'
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

watch(show, (val) => {
  if (val) {
    gstType.value = 'Registered — Regular'
    gstin.value = ''
    legalName.value = props.lead.organization || ''
    error.value = ''
    attempted.value = false
  }
})

// GSTIN format: 2 digit state + 5 letters + 4 digits + 1 letter + 1 entity + Z + 1 checksum = 15
const clean = computed(() => gstin.value.toUpperCase().replace(/\s/g, ''))
const valid = computed(() =>
  /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/.test(clean.value),
)
const stateCode = computed(() => clean.value.slice(0, 2))
const GST_STATES = {
  27: 'Maharashtra',
  24: 'Gujarat',
  '07': 'Delhi',
  29: 'Karnataka',
  33: 'Tamil Nadu',
  '09': 'Uttar Pradesh',
  19: 'West Bengal',
  36: 'Telangana',
  32: 'Kerala',
  '08': 'Rajasthan',
}
const stateName = computed(() => GST_STATES[stateCode.value])
const exempt = computed(() => gstType.value === 'Unregistered / Composition')

const gstinHelp = computed(() => {
  if (!gstin.value)
    return __('15-character GSTIN — 2-digit state code + 10-char PAN + 3 suffix')
  if (valid.value)
    return __('Valid format') + (stateName.value ? ` · ${stateName.value} (${stateCode.value})` : '')
  return __('{0}/15 characters — check the format', [clean.value.length])
})

const errors = computed(() => {
  if (!attempted.value || exempt.value) return {}
  const e = {}
  if (!valid.value) e.gstin = __('Enter a valid 15-character GSTIN')
  if (!legalName.value) e.legalName = __('Required')
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
    show.value = false
    error.value = ''
    updateOnboardingStep('convert_lead_to_deal', true, false, () => {
      localStorage.setItem('firstDeal' + user, newDeal)
    })
    capture('convert_lead_to_deal')
    router.push({ name: 'Deal', params: { dealId: newDeal } })
  }
}
</script>
