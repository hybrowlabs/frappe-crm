<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="px-4 pt-5 pb-6 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('New Organization') }}
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
        <div class="mb-4">
          <FormControl
            type="text"
            :label="__('GSTIN')"
            v-model="organization.doc.gstin"
            placeholder="27AABCM1234E1Z5"
          />
          <p class="mt-1 text-xs text-ink-gray-5">{{ gstinHelp }}</p>
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="organization.doc"
          doctype="CRM Organization"
        />
        <ErrorMessage v-if="error" class="mt-8" :message="__(error)" />
      </div>
      <div class="px-4 pt-4 pb-7 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createOrganization"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import { FormControl, call, createResource, toast } from 'frappe-ui'
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
  options: {
    type: Object,
    default: () => ({ redirect: true, afterInsert: () => {} }),
  },
})

const { isManager } = usersStore()
const { capture } = useTelemetry()

const router = useRouter()
const show = defineModel({ type: Boolean })

const loading = ref(false)
const error = ref(null)

const { document: organization, triggerOnBeforeCreate } =
  useDocument('CRM Organization')

// Auto-fetch name & address from the GSTIN via india_compliance.
const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/
const gstinLoading = ref(false)
let lastFetchedGstin = ''
const fetchedAddress = ref(null)

const gstinHelp = computed(() =>
  gstinLoading.value
    ? __('Fetching GST details…')
    : __('Enter a valid GSTIN to auto-fill name & address'),
)

watch(
  () => organization.doc.gstin,
  (value) => {
    const clean = (value || '').toUpperCase().replace(/\s/g, '')
    if (clean !== value) organization.doc.gstin = clean
    if (!GSTIN_REGEX.test(clean) || clean === lastFetchedGstin) return
    lastFetchedGstin = clean
    fetchGstinInfo(clean)
  },
)

async function fetchGstinInfo(value) {
  gstinLoading.value = true
  try {
    const info = await call(
      'india_compliance.gst_india.utils.gstin_info.get_gstin_info',
      { gstin: value },
    )
    if (info?.business_name) organization.doc.organization_name = info.business_name
    if (info?.permanent_address) {
      fetchedAddress.value = info.permanent_address
      await createAddressFromGstin()
    }
    toast.success(__('GST details fetched'))
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not fetch GST details'))
  } finally {
    gstinLoading.value = false
  }
}

async function createAddressFromGstin() {
  const addr = fetchedAddress.value
  const address = await call('frappe.client.insert', {
    doc: {
      doctype: 'Address',
      address_title: organization.doc.organization_name || organization.doc.gstin,
      address_type: 'Billing',
      gstin: organization.doc.gstin || '',
      address_line1: addr.address_line1 || '',
      address_line2: addr.address_line2 || '',
      city: addr.city || '',
      state: addr.state || '',
      pincode: addr.pincode || '',
      country: addr.country || 'India',
    },
  }).catch(() => null)
  if (address?.name) organization.doc.address = address.name
}

async function createOrganization() {
  loading.value = true
  error.value = null

  if (!organization.doc.gstin) {
    error.value = __('GSTIN is required')
    loading.value = false
    return
  }

  await triggerOnBeforeCreate?.()

  if (fetchedAddress.value && !organization.doc.address) {
    await createAddressFromGstin()
  }

  const doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: 'CRM Organization',
        ...organization.doc,
      },
    },
    {
      onError: (err) => {
        error.value = err.error?.messages?.[0]
        loading.value = false
      },
    },
  )
  loading.value = false
  if (doc.name) {
    capture('organization_created')
    handleOrganizationUpdate(doc)
    organization.doc = {}
  }
}

function handleOrganizationUpdate(doc) {
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Organization',
      params: { organizationId: doc.name },
    })
  }
  show.value = false
  props.options.afterInsert?.(doc)
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Organization'],
  params: { doctype: 'CRM Organization', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'address') {
              field.create = (value, close) => {
                organization.doc.address = value
                showAddressModal()
                close()
              }
              field.edit = (address) => showAddressModal(address)
            } else if (field.fieldtype === 'Table') {
              organization.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

onMounted(() => {
  organization.doc.no_of_employees = '1-10'
  Object.assign(organization.doc, props.data)
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Organization' }
  nextTick(() => (show.value = false))
}

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        organization.doc.address = d.name
      },
    },
  })
}
</script>
