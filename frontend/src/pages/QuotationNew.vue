<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Save')"
        :disabled="!ready || saving"
        :loading="saving"
        @click="save"
      />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto">
    <div class="mx-auto flex max-w-5xl flex-col gap-5 p-5">
      <!-- Sale By: the logged-in user's Sales Person -->
      <div
        v-if="salesPersonLoading"
        class="rounded-lg border border-outline-gray-2 px-4 py-3 text-base text-ink-gray-5"
      >
        {{ __('Looking up your Sales Person…') }}
      </div>
      <div
        v-else-if="!salesPerson"
        class="rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3 text-base text-ink-red-4"
      >
        {{
          __(
            'No Sales Person is linked to your login ({0}). Ask your admin to create one before making quotations.',
            [user],
          )
        }}
      </div>
      <div
        v-else-if="!branches.length"
        class="rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3 text-base text-ink-red-4"
      >
        {{
          __(
            'No Work Location / Currency is set on your Sales Person ({0}). Ask your admin to add one before making quotations.',
            [salesPerson],
          )
        }}
      </div>
      <div v-else class="text-base text-ink-gray-6">
        {{ __('Sale By') }}:
        <span class="font-medium text-ink-gray-9">{{ salesPerson }}</span>
      </div>
      <div
        v-if="timeWindow && !timeWindow.open"
        class="rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3 text-base text-ink-red-4"
      >
        {{
          __('Quotations for {0} can only be made during: {1}.', [
            doc.custom_branch,
            timeWindow.windows.join(', '),
          ])
        }}
      </div>

      <fieldset
        :disabled="!ready"
        class="flex flex-col gap-5"
        :class="{ 'pointer-events-none opacity-50': !ready }"
      >
        <!-- Tabs -->
        <div class="flex gap-7 border-b border-outline-gray-2">
          <button
            v-for="t in tabs"
            :key="t.key"
            type="button"
            class="-mb-px border-b py-2.5 text-base duration-300 ease-in-out hover:text-ink-gray-9"
            :class="
              tab === t.key
                ? 'border-outline-gray-9 text-ink-gray-9'
                : 'border-transparent text-ink-gray-5'
            "
            @click="tab = t.key"
          >
            {{ t.label }}
          </button>
        </div>

        <!-- Details -->
        <div v-show="tab === 'details'" class="flex flex-col gap-6">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <FormControl
              v-model="doc.custom_branch"
              type="select"
              :label="__('Work Location') + ' *'"
              :options="locationOptions"
              :placeholder="__('Select {0}', [__('Work Location')])"
              :disabled="locationOptions.length <= 1"
            />
            <FormControl
              v-model="doc.currency"
              type="select"
              :label="__('Currency') + ' *'"
              :options="currencyOptions"
              :placeholder="__('Select {0}', [__('Currency')])"
              :disabled="currencyOptions.length <= 1"
            />
            <Link
              v-model="doc.party_name"
              :label="__('Customer') + ' *'"
              doctype="Customer"
              :filters="customerFilters"
              :disabled="!doc.custom_branch || !doc.currency"
              :placeholder="
                doc.custom_branch && doc.currency
                  ? __('Select {0}', [__('Customer')])
                  : __('Select Work Location and Currency first')
              "
            />
            <FormControl
              :modelValue="customerName"
              type="text"
              :label="__('Customer Name')"
              disabled
            />
            <FormControl
              v-model="doc.order_type"
              type="select"
              :label="__('Order Type')"
              :options="orderTypeOptions"
              disabled
            />
            <FormControl
              v-model="doc.valid_till"
              type="date"
              :min="doc.transaction_date"
              :label="__('Valid Till')"
              disabled
            />
          </div>

          <!-- Items -->
          <div class="flex flex-col gap-2">
            <div class="text-lg font-medium text-ink-gray-9">
              {{ __('Items') }} *
            </div>
            <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
              <table class="w-full min-w-[70rem] text-base">
                <thead>
                  <tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
                    <th class="w-10 px-3 py-2 font-medium">#</th>
                    <th class="min-w-[14rem] px-3 py-2 font-medium">{{ __('Item') }}</th>
                    <th class="min-w-[12rem] px-3 py-2 font-medium">{{ __('Description') }}</th>
                    <th class="w-24 px-3 py-2 font-medium">{{ __('HSN') }}</th>
                    <th class="w-16 px-3 py-2 text-right font-medium">{{ __('GST') }}</th>
                    <th class="w-28 whitespace-nowrap px-3 py-2 font-medium">{{ __('No of Packs') }}</th>
                    <th class="w-24 px-3 py-2 font-medium">{{ __('Qty') }}</th>
                    <th class="w-16 px-3 py-2 font-medium">{{ __('UOM') }}</th>
                    <th class="w-24 px-3 py-2 text-right font-medium">{{ __('Rate') }}</th>
                    <th class="w-24 px-3 py-2 text-right font-medium">{{ __('Amount') }}</th>
                    <th class="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(row, i) in doc.items"
                    :key="row.key"
                    class="border-t border-outline-gray-1 align-top"
                  >
                    <td class="px-3 py-2.5 text-ink-gray-5">{{ i + 1 }}</td>
                    <td class="px-3 py-1.5">
                      <Link
                        v-model="row.item_code"
                        doctype="Item"
                        :filters="itemFilters"
                        :disabled="!doc.party_name"
                        :placeholder="
                          doc.party_name ? __('Select item') : __('Select a customer first')
                        "
                        @update:modelValue="onItemChange(row)"
                      />
                      <div
                        v-if="isFreight(row) && freightError(row)"
                        class="mt-1 text-sm text-ink-red-4"
                      >
                        {{ freightError(row) }}
                      </div>
                      <div
                        v-if="row.priceMessage"
                        class="mt-1 text-sm"
                        :class="row.priceState === 'error' ? 'text-ink-red-4' : 'text-ink-gray-5'"
                      >
                        {{ row.priceMessage }}
                      </div>
                    </td>
                    <td class="whitespace-pre-line px-3 py-2.5 text-sm text-ink-gray-6">
                      {{ row.description || '—' }}
                    </td>
                    <td class="px-3 py-2.5 text-ink-gray-6">{{ row.gst_hsn_code || '—' }}</td>
                    <td class="px-3 py-2.5 text-right text-ink-gray-6">
                      {{ row.gst_rate == null ? '—' : `${row.gst_rate}%` }}
                    </td>
                    <td class="px-3 py-1.5">
                      <FormControl
                        v-model="row.custom_no_of_packs"
                        type="number"
                        min="0"
                        :disabled="!row.sold_in_packs"
                        :placeholder="row.sold_in_packs ? '' : '—'"
                        @update:modelValue="onPacksChange(row)"
                      />
                      <div
                        v-if="row.sold_in_packs"
                        class="mt-1 text-sm text-ink-gray-5"
                      >
                        {{ __('{0} per pack', [row.custom_base_qty]) }}
                      </div>
                    </td>
                    <td class="px-3 py-1.5">
                      <FormControl v-model="row.qty" type="number" min="0" />
                    </td>
                    <td class="px-3 py-2.5 text-ink-gray-6">{{ row.uom || '—' }}</td>
                    <td
                      :class="isFreight(row) ? 'px-3 py-1.5' : 'px-3 py-2.5 text-right text-ink-gray-8'"
                    >
                      <FormControl
                        v-if="isFreight(row)"
                        v-model="row.rate"
                        type="number"
                        min="0"
                        :placeholder="__('Min {0}', [freightInfo(row).min_pricing])"
                      />
                      <template v-else>{{ rateLabel(row) }}</template>
                    </td>
                    <td class="px-3 py-2.5 text-right text-ink-gray-8">
                      {{ row.rate ? amount(row.rate * (row.qty || 0)) : '—' }}
                    </td>
                    <td class="px-2 py-1.5 text-right">
                      <Button
                        variant="ghost"
                        icon="x"
                        :aria-label="__('Remove row')"
                        @click="removeRow(i)"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div
              v-if="doc.party_name && customerItemsLoaded && !customerItems.length"
              class="rounded-lg bg-surface-gray-2 px-4 py-3 text-base text-ink-gray-6"
            >
              {{
                __(
                  'No items are set up for this customer in this branch. Ask your admin to add them to the Customer\'s Item Discounts.',
                )
              }}
            </div>
            <div class="flex items-center justify-between">
              <Button :label="__('Add Row')" iconLeft="plus" @click="addRow" />
              <span class="text-sm text-ink-gray-5">
                {{ __('Rates are worked out again when the quotation is saved.') }}
              </span>
            </div>
          </div>

          <!-- Totals -->
          <div class="flex justify-end">
            <div class="flex w-full max-w-xs flex-col gap-2 text-base">
              <div class="flex justify-between">
                <span class="text-ink-gray-5">{{ __('Total Quantity') }}</span>
                <span class="text-ink-gray-8">{{ formatQty(totalQty) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-ink-gray-5">{{ __('Net Total') }}</span>
                <span class="text-ink-gray-8">{{ netTotal ? amount(netTotal) : '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-ink-gray-5">{{ __('Taxes') }}</span>
                <span class="text-ink-gray-8">{{ amount(0) }}</span>
              </div>
              <div class="flex justify-between border-t border-outline-gray-2 pt-2">
                <span class="font-medium text-ink-gray-8">{{ __('Grand Total') }}</span>
                <span class="font-medium text-ink-gray-8">{{ amount(netTotal) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Address -->
        <div v-show="tab === 'address'" class="flex flex-col gap-6">
          <div
            v-if="!doc.party_name"
            class="rounded-lg bg-surface-gray-2 px-4 py-3 text-base text-ink-gray-6"
          >
            {{ __('Select a customer on the Details tab to pick its addresses.') }}
          </div>
          <div
            v-else-if="needsAddressChoice"
            class="rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-4 py-3 text-base text-ink-gray-7"
          >
            {{ __('This customer has more than one address. Please pick one before saving.') }}
          </div>

          <section class="flex flex-col gap-3">
            <div class="text-lg font-medium text-ink-gray-9">{{ __('Billing Address') }}</div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <Link
                  v-model="doc.customer_address"
                  :label="__('Customer Address')"
                  doctype="Address"
                  :filters="partyLinkFilters"
                  @update:modelValue="(v) => loadAddress(v, 'billing')"
                />
                <AddressText :text="display.billing" />
              </div>
            </div>
          </section>

          <section class="flex flex-col gap-3">
            <div class="text-lg font-medium text-ink-gray-9">{{ __('Shipping Address') }}</div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <Link
                  v-model="doc.shipping_address_name"
                  :label="__('Shipping Address')"
                  doctype="Address"
                  :filters="partyLinkFilters"
                  @update:modelValue="(v) => loadAddress(v, 'shipping')"
                />
                <AddressText :text="display.shipping" />
              </div>
            </div>
          </section>
        </div>
      </fieldset>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import { getMeta } from '@/stores/meta'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { formatQty } from '@/utils/qty'
import { useCurrencyFormat } from '@/utils/quotation'
import { Breadcrumbs, Button, FormControl, call, toast } from 'frappe-ui'
import { ref, reactive, computed, onMounted, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Multi-line read-only text under an address / contact picker.
const AddressText = (props) =>
  props.text
    ? h(
        'div',
        {
          class:
            'whitespace-pre-line rounded bg-surface-gray-1 px-3 py-2 text-sm text-ink-gray-7',
        },
        props.text,
      )
    : null
AddressText.props = ['text']

const { user } = sessionStore()
const { doctypeMeta } = getMeta('Quotation')

const tabs = [
  { key: 'details', label: __('Details') },
  { key: 'address', label: __('Address') },
]
const tab = ref('details')

// Local dates as YYYY-MM-DD; toISOString() would give yesterday before 5:30 AM IST.
const isoDate = (d) =>
  [d.getFullYear(), d.getMonth() + 1, d.getDate()]
    .map((n) => String(n).padStart(2, '0'))
    .join('-')
const today = isoDate(new Date())
let rowKey = 0
const newRow = () => ({
  key: ++rowKey,
  item_code: '',
  item_name: '',
  description: '',
  gst_hsn_code: '',
  gst_rate: null,
  uom: '',
  qty: null,
  custom_no_of_packs: null,
  custom_base_qty: 0,
  sold_in_packs: false,
  rate: 0,
  priceState: '', // '' | 'loading' | 'priced' | 'on_request' | 'error'
  priceMessage: '',
})

// Series is filled in on the server (rules pending). Sale By is the logged-in
// user's Sales Person, and Branch and Currency come from its Branch & Currency
// rows. The CRM sets no company: ERPNext puts its own on the new quotation, and
// `company` here only mirrors it for the company address / contact pickers.
const doc = reactive({
  quotation_to: 'Customer',
  party_name: '',
  company: '',
  transaction_date: today,
  valid_till: today,
  order_type: 'Sales',
  custom_deal: '',
  custom_branch: '',
  currency: '',
  items: [newRow()],
  customer_address: '',
  shipping_address_name: '',
})

const display = reactive({ billing: '', shipping: '' })

function selectOptions(fieldname) {
  const df = doctypeMeta.value?.fields?.find((f) => f.fieldname === fieldname)
  return (df?.options || '').split('\n')
}
const orderTypeOptions = computed(() => selectOptions('order_type').filter(Boolean))

const partyLinkFilters = computed(() =>
  doc.party_name
    ? [
        ['Dynamic Link', 'link_doctype', '=', 'Customer'],
        ['Dynamic Link', 'link_name', '=', doc.party_name],
      ]
    : [['Dynamic Link', 'link_name', '=', '__none__']],
)

// ---- Sale By, Branch & Currency ---------------------------------------
const salesPerson = ref('')
const salesPersonLoading = ref(true)
const branches = ref([])
// The branch's Quotation time window, checked up front so the form is not
// filled in for a save the server would refuse.
const timeWindow = ref(null)
const ready = computed(
  () => !!salesPerson.value && branches.value.length > 0 && timeWindow.value?.open !== false,
)

watch(
  () => doc.custom_branch,
  async (branch) => {
    timeWindow.value = null
    if (!branch) return
    const w = await call('crm.api.quotation.get_quotation_window', { branch }).catch(() => null)
    if (branch === doc.custom_branch) timeWindow.value = w
  },
  { immediate: true },
)

onMounted(async () => {
  try {
    const defaults = await call('crm.api.quotation.get_quotation_defaults')
    salesPerson.value = defaults?.sales_person || ''
    branches.value = defaults?.branches || []
    doc.company = defaults?.company || ''
    if (locationOptions.value.length === 1) doc.custom_branch = locationOptions.value[0]
    await applyPrefill()
  } catch {
    salesPerson.value = ''
  } finally {
    salesPersonLoading.value = false
  }
})

// Work Location, then Currency, then Customer. A field with a single choice is
// filled in and locked; the Currency choices are the chosen location's rows.
const locationOptions = computed(() => [...new Set(branches.value.map((b) => b.branch))])
const currencyOptions = computed(() =>
  branches.value.filter((b) => b.branch === doc.custom_branch).map((b) => b.currency),
)
watch(
  () => doc.custom_branch,
  () => {
    const choices = currencyOptions.value
    if (choices.includes(doc.currency) && choices.length > 1) return
    doc.currency = choices.length === 1 ? choices[0] : ''
  },
)
// The customer was picked for the old Work Location / Currency; a customer
// opened from Ordered Items comes back whenever one of its pairs is chosen.
watch(
  () => [doc.custom_branch, doc.currency],
  ([branch, currency]) => {
    const fits = prefill.pairs.some((p) => p.branch === branch && p.currency === currency)
    doc.party_name = fits ? prefill.customer : ''
  },
)

// Only customers with the chosen Work Location in their Branch Details and the
// chosen Currency as their Billing Currency, and whose Sales Team includes the
// user's Sales Person; System Managers (and Administrator) skip the Sales Team check.
const { isAdmin } = usersStore()
const customerFilters = computed(() => [
  ['Branch CT', 'branch', '=', doc.custom_branch || '__none__'],
  ['Customer', 'default_currency', '=', doc.currency || '__none__'],
  ...(isAdmin() ? [] : [['Sales Team', 'sales_person', '=', salesPerson.value || '__none__']]),
])

// ---- Party -------------------------------------------------------------
function clearPartyDetails() {
  for (const f of ['customer_address', 'shipping_address_name']) doc[f] = ''
  display.billing = display.shipping = ''
}

// The customer's name for the read-only field; the link shows only its code.
const customerName = ref('')
watch(
  () => doc.party_name,
  async (customer) => {
    customerName.value = ''
    if (!customer) return
    const row = await call('frappe.client.get_value', {
      doctype: 'Customer',
      filters: { name: customer },
      fieldname: 'customer_name',
    }).catch(() => null)
    if (customer === doc.party_name) customerName.value = row?.customer_name || ''
  },
)

// Addresses: one of a kind is taken by itself, several must be picked before
// saving. Counts drive the Address tab's hint and the save check.
const addressChoices = reactive({ billing: [], shipping: [] })
watch(
  () => doc.party_name,
  async (customer) => {
    addressChoices.billing = []
    addressChoices.shipping = []
    if (!customer) return
    const lists = await call('crm.api.quotation.get_customer_addresses', { customer }).catch(
      () => null,
    )
    if (!lists || customer !== doc.party_name) return
    addressChoices.billing = lists.billing || []
    addressChoices.shipping = lists.shipping || []
    if (addressChoices.billing.length === 1) {
      doc.customer_address = addressChoices.billing[0]
      loadAddress(doc.customer_address, 'billing')
    }
    if (addressChoices.shipping.length === 1) {
      doc.shipping_address_name = addressChoices.shipping[0]
      loadAddress(doc.shipping_address_name, 'shipping')
    }
  },
)
const needsAddressChoice = computed(
  () =>
    (addressChoices.billing.length > 1 && !doc.customer_address) ||
    (addressChoices.shipping.length > 1 && !doc.shipping_address_name),
)

// ---- Items -------------------------------------------------------------
// Only the items on the customer's Item Discounts for this branch; picking a
// different customer or branch starts the items over.
const customerItems = ref([])
const customerItemsLoaded = ref(false)
// An empty "in" list would match every item, so fall back to one that can't exist.
const itemFilters = computed(() => ({
  name: [
    'in',
    customerItems.value.length ? customerItems.value.map((i) => i.item_code) : ['__none__'],
  ],
}))

watch(
  () => [doc.party_name, doc.custom_branch],
  async ([customer, branch], [oldCustomer]) => {
    if (customer !== oldCustomer) clearPartyDetails()
    doc.items.splice(0, doc.items.length, newRow())
    customerItems.value = []
    customerItemsLoaded.value = false
    if (!customer) return
    const list = await call('crm.api.quotation.get_customer_items', {
      customer,
      branch,
    }).catch((e) => {
      toast.error(e?.messages?.[0] || __('Could not load the items for this customer.'))
      return []
    })
    // Ignore a stale reply if the customer or branch changed meanwhile.
    if (customer === doc.party_name && branch === doc.custom_branch) {
      customerItems.value = list || []
      customerItemsLoaded.value = true
      applyPrefillItems()
    }
  },
)

// Opened from an organization's Ordered Items (?customer=...&items=a,b): pick
// that customer, then add the ticked items that are set up for it. A single
// Work Location / Currency it fits is chosen too; with several, the user picks.
const route = useRoute()
let prefillItems = String(route.query.items || '')
  .split(',')
  .filter(Boolean)
const prefill = { customer: '', pairs: [] }

async function applyPrefill() {
  if (route.query.deal) doc.custom_deal = String(route.query.deal)
  const customer = String(route.query.customer || '')
  if (!customer) return
  const pairs = await call('crm.api.quotation.get_customer_branch_options', { customer }).catch(
    () => [],
  )
  if (!pairs?.length) {
    toast.error(__('{0} is not set up for any of your Work Location / Currency rows.', [customer]))
    return
  }
  Object.assign(prefill, { customer, pairs })
  const current = pairs.find((p) => p.branch === doc.custom_branch && p.currency === doc.currency)
  if (current) doc.party_name = customer
  else if (pairs.length === 1)
    Object.assign(doc, { custom_branch: pairs[0].branch, currency: pairs[0].currency })
}
// Another customer picked by hand: the prefilled one is not brought back.
watch(
  () => doc.party_name,
  (customer) => {
    if (customer && customer !== prefill.customer) prefill.pairs = []
  },
)

function applyPrefillItems() {
  if (!prefillItems.length) return
  const codes = prefillItems
  prefillItems = []
  const allowed = new Set(customerItems.value.map((i) => i.item_code))
  const usable = codes.filter((c) => allowed.has(c))
  const skipped = codes.filter((c) => !allowed.has(c))
  if (usable.length) {
    doc.items.splice(0, doc.items.length, ...usable.map(() => newRow()))
    doc.items.forEach((row, i) => {
      row.item_code = usable[i]
      onItemChange(row)
    })
  }
  if (skipped.length) {
    toast.error(__('Not set up for this customer, so left out: {0}', [skipped.join(', ')]))
  }
}

// Discount slabs (qty ranges) from the customer's Item Discounts. With slabs,
// the qty must fall inside one of them before the line can be priced; a blank
// To Qty means no upper limit. Same check as the Customer Portal.
const fmtQty = (n) => formatQty(n || 0)

// Service (freight) items from CRM Custom Settings > Non Inventory Item: no Sales
// BOM, so the rate is typed here and may not be under the branch's Min Pricing.
const freightInfo = (row) =>
  customerItems.value.find((i) => i.item_code === row.item_code && i.non_inventory)
const isFreight = (row) => !!row.item_code && !!freightInfo(row)

function freightError(row) {
  const rate = Number(row.rate)
  const minimum = Number(freightInfo(row)?.min_pricing) || 0
  if (rate > 0 && rate < minimum) {
    return __('Rate for {0} cannot be below the minimum price {1}.', [row.item_code, minimum])
  }
  return ''
}

function qtyError(row) {
  const item = customerItems.value.find((i) => i.item_code === row.item_code)
  const slabs = item?.slabs || []
  const q = Number(row.qty) || 0
  if (!slabs.length || !(q > 0)) return ''
  if (slabs.some((s) => q >= (s.from_qty || 0) && (!s.to_qty || q <= s.to_qty))) return ''

  const uom = item.stock_uom || ''
  const lo = Math.min(...slabs.map((s) => s.from_qty || 0))
  const open = slabs.some((s) => !s.to_qty)
  const hi = Math.max(...slabs.map((s) => s.to_qty || 0))
  if (q < lo) return __('Minimum {0} {1} for this customer.', [fmtQty(lo), uom])
  if (!open && q > hi) return __('Maximum {0} {1} for this customer.', [fmtQty(hi), uom])
  const spans = slabs.map((s) =>
    s.to_qty ? `${fmtQty(s.from_qty)}–${fmtQty(s.to_qty)}` : `${fmtQty(s.from_qty)}+`,
  )
  return __('Qty must be within one of these ranges: {0} {1}', [spans.join(', '), uom])
}

function addRow() {
  doc.items.push(newRow())
}

function removeRow(i) {
  doc.items.splice(i, 1)
  if (!doc.items.length) addRow()
}

// Mirrors papl_business_logic quotation.js (_sync_pack_qty_meta): items sold
// only in multiples of a base qty get No of Packs = 1 and Qty = packs x base.
async function onItemChange(row) {
  Object.assign(row, {
    item_name: '',
    description: '',
    gst_hsn_code: '',
    gst_rate: null,
    uom: '',
    rate: 0,
    custom_base_qty: 0,
    sold_in_packs: false,
  })
  if (!row.item_code) {
    row.custom_no_of_packs = null
    return
  }
  const asked = row.item_code
  const item = await call('crm.api.quotation.get_item_details', {
    customer: doc.party_name,
    item_code: row.item_code,
  }).catch(() => null)
  // Ignore a stale reply if the row's item changed meanwhile.
  if (!item || row.item_code !== asked) return
  row.item_name = item.item_name
  row.description = item.description
  row.gst_hsn_code = item.gst_hsn_code
  row.gst_rate = item.gst_rate
  row.uom = item.stock_uom
  if (item.custom_sell_only_as_a_multiple_of_base_qty && item.custom_base_qty > 0) {
    row.sold_in_packs = true
    row.custom_base_qty = item.custom_base_qty
    row.custom_no_of_packs = row.custom_no_of_packs || 1
    row.qty = row.custom_base_qty * row.custom_no_of_packs
  } else {
    row.custom_no_of_packs = null
  }
}

function onPacksChange(row) {
  const packs = Number(row.custom_no_of_packs)
  if (row.sold_in_packs && packs > 0) row.qty = row.custom_base_qty * packs
}

// ---- Price -------------------------------------------------------------
// Same PAPL Sales BOM pricing the quotation gets on save, fetched about 0.4s
// after an item or qty changes (like the Customer Portal).
const priceKey = computed(() =>
  doc.items.map((r) => `${r.item_code}:${Number(r.qty) || 0}`).join('|'),
)
let priceTimer = null
let priceRequest = 0

function clearPrice(row) {
  Object.assign(row, { rate: 0, priceState: '', priceMessage: '' })
}

watch(priceKey, () => {
  clearTimeout(priceTimer)
  for (const row of doc.items) {
    if (isFreight(row)) {
      row.priceState = 'manual'
      continue
    }
    clearPrice(row)
    const error = row.item_code ? qtyError(row) : ''
    if (error) Object.assign(row, { priceState: 'error', priceMessage: error })
  }
  priceTimer = setTimeout(fetchPrices, 400)
})

async function fetchPrices() {
  const rows = doc.items.filter(
    (r) => r.item_code && Number(r.qty) > 0 && r.priceState !== 'error' && !isFreight(r),
  )
  if (!rows.length || !doc.party_name || !doc.custom_branch || !doc.currency) return
  const request = ++priceRequest
  const asked = rows.map((r) => ({ item_code: r.item_code, qty: Number(r.qty) }))
  rows.forEach((r) => (r.priceState = 'loading'))

  let result = null
  let failure = ''
  try {
    result = await call('crm.api.quotation.get_items_price', {
      customer: doc.party_name,
      branch: doc.custom_branch,
      currency: doc.currency,
      items: asked,
    })
  } catch (e) {
    failure = e?.messages?.[0] || e?.message || __('Could not fetch the rate.')
  }
  // A newer request (or edit) has taken over.
  if (request !== priceRequest) return

  rows.forEach((row, i) => {
    if (row.item_code !== asked[i].item_code || Number(row.qty) !== asked[i].qty) return
    const line = result?.items?.[i]
    if (!line) {
      Object.assign(row, { rate: 0, priceState: 'error', priceMessage: failure })
    } else if (line.priced) {
      Object.assign(row, { rate: line.rate, priceState: 'priced', priceMessage: '' })
    } else {
      Object.assign(row, {
        rate: 0,
        priceState: line.ok ? 'on_request' : 'error',
        priceMessage: line.message || (line.ok ? __('No rate for this item.') : ''),
      })
    }
  })
}

function rateLabel(row) {
  if (row.priceState === 'loading') return __('Fetching…')
  if (row.priceState === 'on_request') return __('On request')
  return row.rate ? amount(row.rate) : '—'
}

const totalQty = computed(() =>
  doc.items.reduce((sum, r) => sum + (Number(r.qty) || 0), 0),
)
const netTotal = computed(() =>
  doc.items.reduce((sum, r) => sum + (Number(r.rate) || 0) * (Number(r.qty) || 0), 0),
)
// Taxes show 0 until the quotation is saved, when ERPNext works them out,
// so Grand Total is the Net Total for now.
const amount = useCurrencyFormat(() => doc.currency)

// ---- Address & contact -------------------------------------------------
async function loadAddress(name, target) {
  display[target] = ''
  if (!name) return
  const a = await call('frappe.client.get_value', {
    doctype: 'Address',
    filters: { name },
    fieldname: ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'country', 'gstin'],
  }).catch(() => null)
  if (!a) return
  display[target] = [
    a.address_line1,
    a.address_line2,
    [a.city, a.state, a.pincode].filter(Boolean).join(', '),
    a.country,
    a.gstin && `GSTIN: ${a.gstin}`,
  ]
    .filter(Boolean)
    .join('\n')
}

// ---- Save --------------------------------------------------------------
function validate() {
  if (!salesPerson.value) return __('No Sales Person is linked to your login.')
  if (!doc.custom_branch) return __('Please select a Work Location.')
  if (!doc.currency) return __('Please select a Currency.')
  if (!doc.party_name) return __('Please select a Customer.')
  // More than one to choose from: the user has to say which, on the Address tab.
  if (addressChoices.billing.length > 1 && !doc.customer_address)
    return __('Please select the Customer Address on the Address tab.')
  if (addressChoices.shipping.length > 1 && !doc.shipping_address_name)
    return __('Please select the Shipping Address on the Address tab.')
  const items = doc.items.filter((r) => r.item_code)
  if (!items.length) return __('Please add at least one item.')
  const noQty = items.find((r) => !(Number(r.qty) > 0))
  if (noQty) return __('Please set a Qty for {0}.', [noQty.item_code])
  const freight = items.filter(isFreight)
  const noRate = freight.find((r) => !(Number(r.rate) > 0))
  if (noRate) return __('Please enter the rate for {0}.', [noRate.item_code])
  const lowRate = freight.find((r) => freightError(r))
  if (lowRate) return freightError(lowRate)
  const priced = items.filter((r) => !isFreight(r))
  const pending = priced.find((r) => r.priceState === 'loading' || (!r.priceState && !r.rate))
  if (pending) return __('Please wait for the rates to load.')
  // Like the Customer Portal, every line needs a rate before it can be quoted.
  const unpriced = priced.find((r) => r.priceState !== 'priced' || !(r.rate > 0))
  if (unpriced)
    return __('{0} has no rate: {1}', [
      unpriced.item_code,
      unpriced.priceMessage || __('please remove it.'),
    ])
  return ''
}

const router = useRouter()
const saving = ref(false)

async function save() {
  const error = validate()
  if (error) {
    toast.error(error)
    return
  }
  saving.value = true
  try {
    const result = await call('crm.api.quotation.create_quotation', {
      customer: doc.party_name,
      branch: doc.custom_branch,
      currency: doc.currency,
      deal: doc.custom_deal || null,
      items: doc.items
        .filter((r) => r.item_code)
        .map((r) => ({
          item_code: r.item_code,
          qty: Number(r.qty),
          no_of_packs: r.sold_in_packs ? Number(r.custom_no_of_packs) : null,
          rate: isFreight(r) ? Number(r.rate) : null,
        })),
      addresses: {
        customer_address: doc.customer_address,
        shipping_address_name: doc.shipping_address_name,
      },
    })
    if (!result?.ok) {
      toast.error(result?.message || __('Could not create the quotation.'))
      return
    }
    toast.success(__('Quotation {0} created.', [result.name]))
    router.push({ name: 'Quotation', params: { quotationId: result.name } })
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not create the quotation.'))
  } finally {
    saving.value = false
  }
}

const breadcrumbs = [
  { label: __('Quotations'), route: { name: 'Quotations' } },
  { label: __('New Quotation'), route: { name: 'New Quotation' } },
]
</script>
