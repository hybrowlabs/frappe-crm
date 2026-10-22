<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Item Request'), route: { name: 'Item Request' } }]" />
    </template>
  </LayoutHeader>

  <div v-if="loading" class="flex flex-1 items-center justify-center">
    <LoadingIndicator class="size-6 text-ink-gray-5" />
  </div>

  <div
    v-else-if="!branches.length"
    class="flex flex-1 flex-col items-center justify-center gap-3 px-4 text-center"
  >
    <PackagePlusIcon class="size-7.5 text-ink-gray-5" />
    <span class="text-lg font-medium text-ink-gray-8">{{ __('No Branch Set') }}</span>
    <span class="text-p-base text-ink-gray-6">
      {{ __('No Branch & Currency is set on your Sales Person, so you cannot request items.') }}
    </span>
  </div>

  <div v-else class="flex flex-1 flex-col overflow-hidden">
    <!-- Branch, then Currency, then Customer: same order as a new quotation -->
    <div class="grid grid-cols-1 gap-3 px-4 pt-3 sm:grid-cols-2 sm:px-5 lg:grid-cols-3">
      <FormControl
        v-model="branch"
        type="select"
        :label="__('Branch')"
        :options="branchOptions"
        :placeholder="__('Select {0}', [__('Branch')])"
        :disabled="branchOptions.length <= 1"
      />
      <FormControl
        v-model="currency"
        type="select"
        :label="__('Currency (Billing)')"
        :options="currencyOptions"
        :placeholder="__('Select {0}', [__('Currency')])"
        :disabled="currencyOptions.length <= 1"
      />
      <div class="sm:col-span-2 lg:col-span-1">
        <Link
          v-model="customer"
          :label="__('Customer')"
          doctype="Customer"
          :filters="customerFilters"
          :disabled="!branch || !currency"
          :placeholder="
            branch && currency
              ? __('Select {0}', [__('Customer')])
              : __('Select Branch and Currency first')
          "
        />
        <div v-if="customerName" class="mt-1 truncate text-sm text-ink-gray-5">
          {{ customerName }}
        </div>
      </div>
    </div>

    <!-- Search and selection, shown once the customer's items are loaded -->
    <div
      v-if="customer && items.data?.length"
      class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:px-5"
    >
      <FormControl
        v-model="search"
        type="text"
        :placeholder="__('Search item code, name or group')"
        class="w-full sm:w-72"
      >
        <template #prefix>
          <SearchIcon class="size-4 text-ink-gray-5" />
        </template>
      </FormControl>
      <div class="flex items-center justify-between gap-2 sm:ml-auto sm:justify-end">
        <span class="text-sm text-ink-gray-5">
          {{ __('{0} of {1} selected', [selected.size, items.data.length]) }}
        </span>
        <div class="flex gap-2">
          <Button v-if="selected.size" variant="ghost" :label="__('Clear')" @click="clear" />
          <Button
            class="hidden sm:inline-flex"
            variant="solid"
            :label="__('Add for Quotation')"
            :loading="sending"
            @click="send"
          />
        </div>
      </div>
    </div>

    <div class="flex flex-1 flex-col overflow-hidden px-4 pb-4 sm:px-5">
      <div
        v-if="emptyMessage"
        class="flex flex-1 flex-col items-center justify-center gap-3 text-center"
      >
        <PackagePlusIcon class="size-7.5 text-ink-gray-5" />
        <span class="text-lg font-medium text-ink-gray-8">{{ emptyMessage.title }}</span>
        <span class="max-w-md text-p-base text-ink-gray-6">{{ emptyMessage.description }}</span>
      </div>

      <div v-else-if="items.loading" class="flex flex-1 items-center justify-center">
        <LoadingIndicator class="size-6 text-ink-gray-5" />
      </div>

      <div v-else-if="rows.length" class="flex-1 overflow-y-auto">
        <table class="w-full table-fixed text-base">
          <thead class="sticky top-0 z-10">
            <tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
              <th class="w-10 rounded-l-md px-3 py-2">
                <input
                  type="checkbox"
                  class="rounded border-outline-gray-2 text-ink-gray-9 focus:ring-0"
                  :checked="allShownSelected"
                  :aria-label="__('Select all')"
                  @change="toggleAllShown"
                />
              </th>
              <th class="px-3 py-2 font-normal sm:w-1/4">{{ __('Item Code') }}</th>
              <th class="hidden px-3 py-2 font-normal sm:table-cell">{{ __('Item Name') }}</th>
              <th class="hidden w-1/4 rounded-r-md px-3 py-2 font-normal md:table-cell">
                {{ __('Item Group') }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.item_code"
              class="cursor-pointer border-b border-outline-gray-1 text-ink-gray-8 hover:bg-surface-gray-1"
              :class="{ 'bg-surface-gray-1': selected.has(row.item_code) }"
              @click="toggle(row.item_code)"
            >
              <td class="px-3 py-2.5 align-top">
                <input
                  type="checkbox"
                  class="rounded border-outline-gray-2 text-ink-gray-9 focus:ring-0"
                  :checked="selected.has(row.item_code)"
                  @click.stop
                  @change="toggle(row.item_code)"
                />
              </td>
              <td class="break-words px-3 py-2.5">
                <div class="font-medium">{{ row.item_code }}</div>
                <!-- Phones have no Item Name / Item Group columns: show them here -->
                <div class="text-sm text-ink-gray-6 sm:hidden">{{ row.item_name }}</div>
                <div class="text-sm text-ink-gray-5 md:hidden">{{ row.item_group }}</div>
              </td>
              <td class="hidden break-words px-3 py-2.5 text-ink-gray-7 sm:table-cell">
                {{ row.item_name }}
              </td>
              <td class="hidden break-words px-3 py-2.5 text-ink-gray-7 md:table-cell">
                {{ row.item_group }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Phones: the button stays at the bottom so it is always in reach -->
    <div
      v-if="customer && items.data?.length"
      class="border-t border-outline-gray-1 bg-surface-white px-4 py-3 sm:hidden"
    >
      <Button
        class="w-full"
        variant="solid"
        :label="
          selected.size
            ? __('Add for Quotation ({0})', [selected.size])
            : __('Add for Quotation')
        "
        :loading="sending"
        @click="send"
      />
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import PackagePlusIcon from '~icons/lucide/package-plus'
import SearchIcon from '~icons/lucide/search'
import { usersStore } from '@/stores/users'
import {
  Breadcrumbs,
  Button,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'

// Sales Person and its Branch & Currency rows, as on a new quotation.
const loading = ref(true)
const salesPerson = ref('')
const branches = ref([])

const branch = ref('')
const currency = ref('')
const customer = ref('')
const customerName = ref('')
const search = ref('')
const selected = reactive(new Set())
const sending = ref(false)

onMounted(async () => {
  try {
    const defaults = await call('crm.api.quotation.get_quotation_defaults')
    salesPerson.value = defaults?.sales_person || ''
    branches.value = defaults?.branches || []
    if (branchOptions.value.length === 1) branch.value = branchOptions.value[0]
  } finally {
    loading.value = false
  }
})

// A field with a single choice is filled in and locked.
const branchOptions = computed(() => [...new Set(branches.value.map((b) => b.branch))])
const currencyOptions = computed(() =>
  branches.value.filter((b) => b.branch === branch.value).map((b) => b.currency),
)
watch(branch, () => {
  const choices = currencyOptions.value
  if (choices.includes(currency.value) && choices.length > 1) return
  currency.value = choices.length === 1 ? choices[0] : ''
})
// The customer was picked for the old Branch / Currency.
watch([branch, currency], () => (customer.value = ''))

// Only customers with the Branch in their Branch Details, the Currency as their
// Billing Currency and (for non-admins) the user's Sales Person on their Sales Team.
const { isAdmin } = usersStore()
const customerFilters = computed(() => [
  ['Branch CT', 'branch', '=', branch.value || '__none__'],
  ['Customer', 'default_currency', '=', currency.value || '__none__'],
  ...(isAdmin() ? [] : [['Sales Team', 'sales_person', '=', salesPerson.value || '__none__']]),
])

// Stock items the customer cannot be quoted yet.
const items = createResource({ url: 'crm.api.item_request.get_request_items' })

watch(customer, async (value) => {
  selected.clear()
  search.value = ''
  customerName.value = ''
  items.reset()
  if (!value) return
  items.submit({ customer: value, branch: branch.value, currency: currency.value })
  const row = await call('frappe.client.get_value', {
    doctype: 'Customer',
    filters: { name: value },
    fieldname: 'customer_name',
  }).catch(() => null)
  if (value === customer.value) customerName.value = row?.customer_name || ''
})

const rows = computed(() => {
  const list = items.data || []
  const text = search.value.trim().toLowerCase()
  if (!text) return list
  return list.filter((row) =>
    [row.item_code, row.item_name, row.item_group].some((v) =>
      (v || '').toLowerCase().includes(text),
    ),
  )
})

function toggle(code) {
  selected.has(code) ? selected.delete(code) : selected.add(code)
}

function clear() {
  selected.clear()
}

// The header checkbox works on the rows the search shows.
const allShownSelected = computed(
  () => rows.value.length > 0 && rows.value.every((row) => selected.has(row.item_code)),
)
function toggleAllShown() {
  const select = !allShownSelected.value
  for (const row of rows.value) select ? selected.add(row.item_code) : selected.delete(row.item_code)
}

const emptyMessage = computed(() => {
  if (!branch.value || !currency.value || !customer.value)
    return {
      title: __('Select a Customer'),
      description: __('Pick the Branch, Currency and Customer to see the items you can request.'),
    }
  if (items.error)
    return {
      title: __('Could Not Load Items'),
      description: items.error.messages?.[0] || items.error.message,
    }
  if (!items.data || items.loading) return null
  if (!items.data.length)
    return {
      title: __('Nothing to Request'),
      description: __('{0} can already be quoted for every stock item.', [
        customerName.value || customer.value,
      ]),
    }
  if (!rows.value.length)
    return {
      title: __('No Matching Items'),
      description: __('No item matches "{0}".', [search.value]),
    }
  return null
})

async function send() {
  if (!selected.size) {
    toast.error(__('Select at least one item.'))
    return
  }
  sending.value = true
  try {
    await call('crm.api.item_request.send_item_request', {
      customer: customer.value,
      branch: branch.value,
      currency: currency.value,
      items: [...selected],
    })
    toast.success(__('Request sent.'))
    selected.clear()
  } catch (e) {
    toast.error(e.messages?.[0] || e.message || __('Could not send the request.'))
  } finally {
    sending.value = false
  }
}
</script>
