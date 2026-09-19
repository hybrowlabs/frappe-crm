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
            'No Branch / Currency is set on your Sales Person ({0}). Ask your admin to add one before making quotations.',
            [salesPerson],
          )
        }}
      </div>
      <div v-else class="text-base text-ink-gray-6">
        {{ __('Sale By') }}:
        <span class="font-medium text-ink-gray-9">{{ salesPerson }}</span>
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
            <Link
              v-model="doc.party_name"
              :label="__('Customer') + ' *'"
              doctype="Customer"
              :filters="customerFilters"
              :placeholder="__('Select {0}', [__('Customer')])"
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
            <FormControl
              v-if="branches.length > 1"
              v-model="doc.custom_branch"
              type="select"
              :label="__('Branch') + ' *'"
              :options="branches.map((b) => b.branch)"
            />
          </div>

          <!-- Items -->
          <div class="flex flex-col gap-2">
            <div class="text-lg font-medium text-ink-gray-9">
              {{ __('Items') }} *
            </div>
            <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
              <table class="w-full min-w-[48rem] text-base">
                <thead>
                  <tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
                    <th class="w-10 px-3 py-2 font-medium">#</th>
                    <th class="px-3 py-2 font-medium">{{ __('Item') }}</th>
                    <th class="w-32 px-3 py-2 font-medium">{{ __('No of Packs') }}</th>
                    <th class="w-32 px-3 py-2 font-medium">{{ __('Qty') }}</th>
                    <th class="w-20 px-3 py-2 font-medium">{{ __('UOM') }}</th>
                    <th class="w-28 px-3 py-2 text-right font-medium">{{ __('Rate') }}</th>
                    <th class="w-28 px-3 py-2 text-right font-medium">{{ __('Amount') }}</th>
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
                        v-if="row.item_name && row.item_name !== row.item_code"
                        class="mt-1 text-sm text-ink-gray-5"
                      >
                        {{ row.item_name }}
                      </div>
                      <div
                        v-if="row.priceMessage"
                        class="mt-1 text-sm"
                        :class="row.priceState === 'error' ? 'text-ink-red-4' : 'text-ink-gray-5'"
                      >
                        {{ row.priceMessage }}
                      </div>
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
                    <td class="px-3 py-2.5 text-right text-ink-gray-8">
                      {{ rateLabel(row) }}
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
                <span class="text-ink-gray-8">{{ totalQty }}</span>
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

          <section class="flex flex-col gap-3">
            <div class="text-lg font-medium text-ink-gray-9">{{ __('Company Address') }}</div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <Link
                  v-model="doc.company_address"
                  :label="__('Company Address Name')"
                  doctype="Address"
                  :filters="companyLinkFilters"
                  @update:modelValue="(v) => loadAddress(v, 'company')"
                />
                <AddressText :text="display.company" />
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
  company_address: '',
})

const display = reactive({ billing: '', shipping: '', company: '' })

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
const companyLinkFilters = computed(() => [
  ['Dynamic Link', 'link_doctype', '=', 'Company'],
  ['Dynamic Link', 'link_name', '=', doc.company || '__none__'],
])

// ---- Sale By, Branch & Currency ---------------------------------------
const salesPerson = ref('')
const salesPersonLoading = ref(true)
const branches = ref([])
const ready = computed(() => !!salesPerson.value && branches.value.length > 0)

onMounted(async () => {
  try {
    const defaults = await call('crm.api.quotation.get_quotation_defaults')
    salesPerson.value = defaults?.sales_person || ''
    branches.value = defaults?.branches || []
    doc.company = defaults?.company || ''
    if (branches.value.length) doc.custom_branch = branches.value[0].branch
    applyPrefill()
  } catch {
    salesPerson.value = ''
  } finally {
    salesPersonLoading.value = false
  }
})

// Currency always follows the chosen branch's row.
watch(
  () => doc.custom_branch,
  (branch) => {
    doc.currency = branches.value.find((b) => b.branch === branch)?.currency || ''
  },
)

// Only customers whose Sales Team includes the user's Sales Person;
// System Managers (and Administrator) can pick any customer.
const { isAdmin } = usersStore()
const customerFilters = computed(() =>
  isAdmin()
    ? []
    : [['Sales Team', 'sales_person', '=', salesPerson.value || '__none__']],
)

// ---- Party -------------------------------------------------------------
function clearPartyDetails() {
  for (const f of ['customer_address', 'shipping_address_name']) doc[f] = ''
  display.billing = display.shipping = ''
}

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
// that customer, then add the ticked items that are set up for it.
const route = useRoute()
let prefillItems = String(route.query.items || '')
  .split(',')
  .filter(Boolean)

function applyPrefill() {
  if (route.query.deal) doc.custom_deal = String(route.query.deal)
  if (route.query.customer && !doc.party_name) doc.party_name = String(route.query.customer)
}

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
const fmtQty = (n) => Number(n || 0).toLocaleString('en-IN')

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
  Object.assign(row, { item_name: '', uom: '', rate: 0, custom_base_qty: 0, sold_in_packs: false })
  if (!row.item_code) {
    row.custom_no_of_packs = null
    return
  }
  const item = await call('frappe.client.get_value', {
    doctype: 'Item',
    filters: { name: row.item_code },
    fieldname: [
      'item_name',
      'stock_uom',
      'custom_sell_only_as_a_multiple_of_base_qty',
      'custom_base_qty',
    ],
  }).catch(() => null)
  if (!item) return
  row.item_name = item.item_name
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
    clearPrice(row)
    const error = row.item_code ? qtyError(row) : ''
    if (error) Object.assign(row, { priceState: 'error', priceMessage: error })
  }
  priceTimer = setTimeout(fetchPrices, 400)
})

async function fetchPrices() {
  const rows = doc.items.filter(
    (r) => r.item_code && Number(r.qty) > 0 && r.priceState !== 'error',
  )
  if (!rows.length || !doc.party_name || !doc.custom_branch) return
  const request = ++priceRequest
  const asked = rows.map((r) => ({ item_code: r.item_code, qty: Number(r.qty) }))
  rows.forEach((r) => (r.priceState = 'loading'))

  let result = null
  let failure = ''
  try {
    result = await call('crm.api.quotation.get_items_price', {
      customer: doc.party_name,
      branch: doc.custom_branch,
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
// Plain numbers, no currency symbol.
const amount = (v) =>
  new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(
    v || 0,
  )

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
  if (!doc.custom_branch || !doc.currency) return __('No Branch / Currency is set on your Sales Person.')
  if (!doc.party_name) return __('Please select a Customer.')
  const items = doc.items.filter((r) => r.item_code)
  if (!items.length) return __('Please add at least one item.')
  const noQty = items.find((r) => !(Number(r.qty) > 0))
  if (noQty) return __('Please set a Qty for {0}.', [noQty.item_code])
  const pending = items.find((r) => r.priceState === 'loading' || (!r.priceState && !r.rate))
  if (pending) return __('Please wait for the rates to load.')
  // Like the Customer Portal, every line needs a rate before it can be quoted.
  const unpriced = items.find((r) => r.priceState !== 'priced' || !(r.rate > 0))
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
      deal: doc.custom_deal || null,
      items: doc.items
        .filter((r) => r.item_code)
        .map((r) => ({
          item_code: r.item_code,
          qty: Number(r.qty),
          no_of_packs: r.sold_in_packs ? Number(r.custom_no_of_packs) : null,
        })),
      addresses: {
        customer_address: doc.customer_address,
        shipping_address_name: doc.shipping_address_name,
        company_address: doc.company_address,
      },
    })
    // All or nothing: the quotation is kept only with its Sales Order.
    if (!result?.ok) {
      toast.error(result?.message || __('Could not create the quotation.'))
      return
    }
    toast.success(
      __('Quotation {0} and Sales Order {1} created.', [result.name, result.sales_order]),
    )
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
