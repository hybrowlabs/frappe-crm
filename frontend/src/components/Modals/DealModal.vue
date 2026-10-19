<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Deal') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              icon="x"
              @click="show = false"
            />
          </div>
        </div>
        <div>
          <div class="mb-5">
            <div class="mb-2 text-sm text-ink-gray-5">
              {{ __('What does the customer need?') }}
            </div>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <button
                v-for="option in dealFlowOptions"
                :key="option.value"
                type="button"
                class="rounded-lg border p-3 text-left"
                :class="
                  dealFlow === option.value
                    ? 'border-outline-gray-4 bg-surface-gray-2'
                    : 'border-outline-gray-1 hover:bg-surface-gray-1'
                "
                @click="dealFlow = option.value"
              >
                <div class="flex items-center gap-2">
                  <span
                    class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-outline-gray-4"
                  >
                    <span
                      v-if="dealFlow === option.value"
                      class="h-2 w-2 rounded-full bg-surface-gray-7"
                    />
                  </span>
                  <span class="text-base font-medium text-ink-gray-9">
                    {{ option.label }}
                  </span>
                </div>
                <div class="mt-1 pl-6 text-sm text-ink-gray-5">
                  {{ option.description }}
                </div>
              </button>
            </div>
          </div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3"
          >
            <div
              v-if="hasOrganizationSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Organization') }}</div>
              <Switch v-model="chooseExistingOrganization" />
            </div>
            <div
              v-if="hasContactSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Contact') }}</div>
              <Switch v-model="chooseExistingContact" />
            </div>
          </div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="h-px w-full border-t my-5"
          />
          <div v-if="!chooseExistingOrganization" class="mb-4">
            <FieldSelect
              v-model="gstType"
              :label="__('GST Registration Type')"
              required
              :options="GST_TYPE_OPTIONS"
            />
            <template v-if="!exempt">
              <FieldText
                v-model="gstin"
                :label="__('GSTIN')"
                required
                placeholder="27AABCM1234E1Z5"
                :help="gstinHelp"
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
              <FieldText v-model="billing.address_line1" :label="__('Address Line 1')" />
              <FieldText v-model="billing.address_line2" :label="__('Address Line 2')" />
              <FieldGrid :cols="2">
                <FieldText v-model="billing.city" :label="__('City')" />
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
                  class="mt-2"
                />
                <FieldText v-model="shipping.address_line2" :label="__('Address Line 2')" />
                <FieldGrid :cols="2">
                  <FieldText v-model="shipping.city" :label="__('City')" required />
                  <FieldText v-model="shipping.state" :label="__('State')" />
                </FieldGrid>
                <FieldGrid :cols="2">
                  <FieldText v-model="shipping.pincode" :label="__('Pincode')" />
                  <FieldText v-model="shipping.country" :label="__('Country')" />
                </FieldGrid>
              </template>
            </StageSection>
          </div>
          <FieldLayout
            v-if="tabs.data?.length"
            :tabs="tabs.data"
            :data="deal.doc"
            doctype="CRM Deal"
            :context="deal"
          />
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isDealCreating"
            @click="createDeal"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import { isTenDigitPhone } from '@/utils/phoneFields'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import StageSection from '@/components/StageForms/StageSection.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldGrid from '@/components/StageForms/FieldGrid.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import { useGstin, GST_TYPE_OPTIONS } from '@/composables/useGstin'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { useTelemetry } from 'frappe-ui/frappe'
import { Switch, createResource } from 'frappe-ui'
import { computed, ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: { type: Object, default: () => ({}) },
})

const { getUser, isManager } = usersStore()
const { getDealStatus, statusOptions } = statusesStore()

const show = defineModel({ type: Boolean })
const router = useRouter()
const error = ref(null)

const { document: deal, triggerOnBeforeCreate } = useDocument('CRM Deal')

const hasOrganizationSections = ref(true)
const hasContactSections = ref(true)

// "Needs discussion / trial" is today's flow (starts at Req. Discussion).
// "Ready to buy" creates the deal, then opens Create Customer and moves it to
// Proposal/Quotation on the Deal page.
const dealFlowOptions = [
  {
    value: 'discussion',
    label: __('Needs discussion / trial'),
    description: __(
      'We first understand their need, suggest a product, and may run a trial before the quotation.',
    ),
  },
  {
    value: 'ready',
    label: __('Ready to buy – send quotation now'),
    description: __(
      'Small or medium business that already knows what it wants. Go straight to the price quote.',
    ),
  },
]
const dealFlow = ref('discussion')

const isDealCreating = ref(false)
const chooseExistingContact = ref(false)
const chooseExistingOrganization = ref(false)
const { capture } = useTelemetry()

watch(
  [chooseExistingOrganization, chooseExistingContact],
  ([organization, contact]) => {
    tabs.data.forEach((tab) => {
      tab.sections.forEach((section) => {
        if (section.name === 'organization_section') {
          section.hidden = !organization
        } else if (section.name === 'organization_details_section') {
          section.hidden = organization
        } else if (section.name === 'contact_section') {
          section.hidden = !contact
        } else if (section.name === 'contact_details_section') {
          section.hidden = contact
        }
      })
    })
  },
)

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Deal'],
  params: { doctype: 'CRM Deal', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    hasOrganizationSections.value = false
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          if (
            ['organization_section', 'organization_details_section'].includes(
              section.name,
            )
          ) {
            hasOrganizationSections.value = true
          } else if (
            ['contact_section', 'contact_details_section'].includes(
              section.name,
            )
          ) {
            hasContactSections.value = true
          }
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = dealStatuses.value
              field.prefix = getDealStatus(deal.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              deal.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const dealStatuses = computed(() => statusOptions('deal'))

// Auto-fill name, GST type, state and address from the GSTIN (same as Lead → Deal).
const {
  gstType,
  gstin,
  fetchedState,
  billing,
  shipping,
  sameAsBilling,
  clean,
  valid,
  stateCode,
  exempt,
  gstinHelp,
  createDealAddresses,
} = useGstin({
  onBusinessName(name) {
    deal.doc.legal_name = name
    deal.doc.organization_name = name
  },
})

async function createDeal() {
  if (deal.doc.website && !deal.doc.website.startsWith('http')) {
    deal.doc.website = 'https://' + deal.doc.website
  }
  if (chooseExistingContact.value) {
    deal.doc['first_name'] = null
    deal.doc['last_name'] = null
    deal.doc['email'] = null
    deal.doc['mobile_no'] = null
  } else deal.doc['contact'] = null

  if (!chooseExistingOrganization.value) {
    deal.doc.gstin = exempt.value ? '' : clean.value
  }
  deal.doc.direct_quotation = dealFlow.value === 'ready' ? 1 : 0

  await triggerOnBeforeCreate?.()

  createResource({
    url: 'crm.fcrm.doctype.crm_deal.crm_deal.create_deal',
    params: { doc: deal.doc },
    auto: true,
    validate() {
      error.value = null
      if (!chooseExistingOrganization.value) {
        if (!exempt.value && !valid.value) {
          error.value = __('Enter a valid 15-character GSTIN')
          return error.value
        }
        if (
          !sameAsBilling.value &&
          (!shipping.address_line1 || !shipping.city)
        ) {
          error.value = __('Shipping address line 1 and city are required')
          return error.value
        }
      }
      if (deal.doc.annual_revenue) {
        if (typeof deal.doc.annual_revenue === 'string') {
          deal.doc.annual_revenue = deal.doc.annual_revenue.replace(/,/g, '')
        } else if (isNaN(deal.doc.annual_revenue)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (
        deal.doc.mobile_no &&
        isNaN(deal.doc.mobile_no.replace(/[-+() ]/g, ''))
      ) {
        error.value = __('Mobile No. should be a number')
        return error.value
      }
      if (deal.doc.mobile_no && !isTenDigitPhone(deal.doc.mobile_no)) {
        error.value = __('Mobile No. must be a 10 digit number')
        return error.value
      }
      if (deal.doc.email && !deal.doc.email.includes('@')) {
        error.value = __('Invalid email address')
        return error.value
      }
      if (!deal.doc.status) {
        error.value = __('Status is required')
        return error.value
      }
      isDealCreating.value = true
    },
    async onSuccess(name) {
      capture('deal_created')
      if (!chooseExistingOrganization.value) {
        await createDealAddresses(
          name,
          deal.doc.legal_name || deal.doc.organization_name,
        )
      }
      isDealCreating.value = false
      show.value = false
      router.push({
        name: 'Deal',
        params: { dealId: name },
        // Tells the Deal page to open Create Customer straight away.
        query: dealFlow.value === 'ready' ? { quote: '1' } : {},
      })
    },
    onError(err) {
      isDealCreating.value = false
      if (!err.messages) {
        error.value = err.message
        return
      }
      error.value = err.messages.join('\n')
    },
  })
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Deal' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  deal.doc.no_of_employees = '1-10'
  Object.assign(deal.doc, props.defaults)
  if (deal.doc.gstin) gstin.value = deal.doc.gstin

  if (!deal.doc.deal_owner) {
    deal.doc.deal_owner = getUser().name
  }
  if (!deal.doc.status && dealStatuses.value[0].value) {
    deal.doc.status = dealStatuses.value[0].value
  }
})
</script>
