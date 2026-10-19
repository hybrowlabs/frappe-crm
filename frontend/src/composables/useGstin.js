import { call, toast } from 'frappe-ui'
import { ref, reactive, computed, watch } from 'vue'

// GSTIN lookup, GST type and billing/shipping address state for deal-creation
// forms. Mirrors the behaviour of ConvertToDealModal so a directly created deal
// gets the same details auto-filled from the GSTIN.

export const GST_TYPE_OPTIONS = [
  'Registered — Regular',
  'Registered — Composition',
  'SEZ / Export',
  'Unregistered / Composition',
]

// Map india_compliance GST Category to our registration-type options.
const GST_CATEGORY_MAP = {
  'Registered Regular': 'Registered — Regular',
  'Registered Composition': 'Registered — Composition',
  SEZ: 'SEZ / Export',
  Overseas: 'SEZ / Export',
  'Deemed Export': 'SEZ / Export',
  Unregistered: 'Unregistered / Composition',
}

// GSTIN format: 2 digit state + 5 letters + 4 digits + 1 letter + 1 entity + Z + 1 checksum = 15
const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/

function emptyAddress() {
  return {
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    pincode: '',
    country: 'India',
  }
}

function fillAddress(target, addr) {
  target.address_line1 = addr.address_line1 || ''
  target.address_line2 = addr.address_line2 || ''
  target.city = addr.city || ''
  target.state = addr.state || ''
  target.pincode = addr.pincode || ''
  target.country = addr.country || 'India'
}

// onBusinessName(name) is called with the legal name returned by the GST portal.
export function useGstin({ onBusinessName } = {}) {
  const gstType = ref(GST_TYPE_OPTIONS[0])
  const gstin = ref('')
  const gstinLoading = ref(false)
  const fetchedState = ref('')
  const billing = reactive(emptyAddress())
  const shipping = reactive(emptyAddress())
  const sameAsBilling = ref(true)
  let lastFetchedGstin = ''

  const clean = computed(() => gstin.value.toUpperCase().replace(/\s/g, ''))
  const valid = computed(() => GSTIN_REGEX.test(clean.value))
  const stateCode = computed(() => clean.value.slice(0, 2))
  const exempt = computed(() => gstType.value === 'Unregistered / Composition')

  const gstinHelp = computed(() => {
    if (gstinLoading.value) return __('Fetching GST details…')
    if (!gstin.value)
      return __('15-character GSTIN — 2-digit state code + 10-char PAN + 3 suffix')
    if (valid.value)
      return (
        __('Valid format') +
        (fetchedState.value ? ` · ${fetchedState.value} (${stateCode.value})` : '')
      )
    return __('{0}/15 characters — check the format', [clean.value.length])
  })

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
      if (info?.business_name) onBusinessName?.(info.business_name)
      if (info?.gst_category && GST_CATEGORY_MAP[info.gst_category])
        gstType.value = GST_CATEGORY_MAP[info.gst_category]
      if (info?.permanent_address?.state) fetchedState.value = info.permanent_address.state
      if (info?.permanent_address) fillAddress(billing, info.permanent_address)
      toast.success(__('GST details fetched'))
    } catch (err) {
      toast.error(err.messages?.[0] || __('Could not fetch GST details'))
    } finally {
      gstinLoading.value = false
    }
  }

  function reset() {
    gstType.value = GST_TYPE_OPTIONS[0]
    gstin.value = ''
    fetchedState.value = ''
    lastFetchedGstin = ''
    fillAddress(billing, {})
    fillAddress(shipping, {})
    sameAsBilling.value = true
  }

  // Create billing (and shipping, if different) addresses and link them to the deal.
  // Skipped when no billing address was entered.
  async function createDealAddresses(dealName, addressTitle) {
    if (!billing.address_line1) return
    const gstinValue = exempt.value ? '' : clean.value
    const links = [{ link_doctype: 'CRM Deal', link_name: dealName }]
    const title = addressTitle || dealName
    try {
      const billingAddress = await call('frappe.client.insert', {
        doc: {
          doctype: 'Address',
          address_title: title,
          address_type: 'Billing',
          gstin: gstinValue,
          ...billing,
          links,
        },
      })
      const updates = {
        billing_address: billingAddress.name,
        shipping_address: billingAddress.name,
      }
      if (!sameAsBilling.value && shipping.address_line1) {
        const shippingAddress = await call('frappe.client.insert', {
          doc: {
            doctype: 'Address',
            address_title: title,
            address_type: 'Shipping',
            gstin: gstinValue,
            ...shipping,
            links,
          },
        })
        updates.shipping_address = shippingAddress.name
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

  return {
    gstType,
    gstin,
    gstinLoading,
    fetchedState,
    billing,
    shipping,
    sameAsBilling,
    clean,
    valid,
    stateCode,
    exempt,
    gstinHelp,
    reset,
    createDealAddresses,
  }
}
