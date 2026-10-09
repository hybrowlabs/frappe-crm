<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Available Stock'), route: { name: 'Available Stock' } }]" />
    </template>
  </LayoutHeader>

  <div
    v-if="branches.fetched && !branches.data?.length"
    class="flex flex-1 flex-col items-center justify-center gap-3 px-4 text-center"
  >
    <WarehouseIcon class="size-7.5 text-ink-gray-5" />
    <span class="text-lg font-medium text-ink-gray-8">{{ __('No Branch Set') }}</span>
    <span class="text-p-base text-ink-gray-6">
      {{ __('No branch is set on your Sales Person, so there is no stock to show.') }}
    </span>
  </div>

  <template v-else-if="branches.data?.length">
    <!-- Filter bar, laid out like the CRM list views -->
    <div class="flex flex-wrap items-center gap-2 px-4 py-3 sm:px-5">
      <FormControl
        v-model="branch"
        type="select"
        :options="branches.data"
        :disabled="branches.data.length < 2"
        class="w-full sm:w-44"
      />
      <FormControl
        v-model="search"
        type="text"
        :placeholder="__('Search item code or name')"
        class="w-full sm:w-64"
      >
        <template #prefix>
          <SearchIcon class="size-4 text-ink-gray-5" />
        </template>
      </FormControl>
      <div class="ml-auto flex items-center gap-2">
        <span v-if="stock.data?.items?.length" class="text-sm text-ink-gray-5">
          {{ __('{0} items', [rows.length]) }}
        </span>
        <Button :loading="stock.loading" @click="reload">
          <template #icon>
            <RefreshIcon class="size-4" />
          </template>
        </Button>
      </div>
    </div>

    <div class="flex flex-1 flex-col overflow-hidden px-4 pb-4 sm:px-5">
      <div
        v-if="emptyMessage"
        class="flex flex-1 flex-col items-center justify-center gap-3 text-center"
      >
        <WarehouseIcon class="size-7.5 text-ink-gray-5" />
        <span class="text-lg font-medium text-ink-gray-8">{{ emptyMessage.title }}</span>
        <span class="text-p-base text-ink-gray-6">{{ emptyMessage.description }}</span>
      </div>

      <div v-else-if="rows.length" class="flex-1 overflow-y-auto">
        <table class="w-full table-fixed text-base">
          <thead class="sticky top-0 z-10">
            <tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
              <th class="w-1/3 rounded-l-md px-3 py-2 font-normal">{{ __('Item Code') }}</th>
              <th class="px-3 py-2 font-normal">{{ __('Item Name') }}</th>
              <th class="w-32 rounded-r-md px-3 py-2 text-right font-normal">
                {{ __('Available Qty') }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.item_code"
              class="border-b border-outline-gray-1 text-ink-gray-8 hover:bg-surface-gray-1"
            >
              <td class="break-words px-3 py-2.5 font-medium">{{ row.item_code }}</td>
              <td class="break-words px-3 py-2.5 text-ink-gray-7">{{ row.item_name }}</td>
              <td class="px-3 py-2.5 text-right">
                <span class="font-semibold">{{ formatQty(row.qty) }}</span>
                <span class="ml-1 text-sm text-ink-gray-5">{{ row.stock_uom }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import WarehouseIcon from '~icons/lucide/warehouse'
import SearchIcon from '~icons/lucide/search'
import RefreshIcon from '~icons/lucide/refresh-cw'
import { formatQty } from '@/utils/qty'
import { Breadcrumbs, Button, FormControl, createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const branch = ref('')
const search = ref('')

const branches = createResource({
  url: 'crm.api.stock.get_stock_branches',
  auto: true,
  onSuccess(data) {
    if (data?.length) branch.value = data[0]
  },
})

const stock = createResource({ url: 'crm.api.stock.get_available_stock' })

function reload() {
  if (branch.value) stock.submit({ branch: branch.value })
}

watch(branch, reload)

const rows = computed(() => {
  const items = stock.data?.items || []
  const text = search.value.trim().toLowerCase()
  if (!text) return items
  return items.filter((row) =>
    [row.item_code, row.item_name].some((v) => (v || '').toLowerCase().includes(text)),
  )
})

const emptyMessage = computed(() => {
  if (!stock.data || stock.loading) return null
  if (!stock.data.warehouses.length)
    return {
      title: __('No Warehouses Set'),
      description: __('No warehouses are set for {0} in CRM Custom Settings.', [branch.value]),
    }
  if (!stock.data.items.length)
    return {
      title: __('No Stock Found'),
      description: __('The warehouses of {0} hold no stock right now.', [branch.value]),
    }
  if (!rows.value.length)
    return {
      title: __('No Matching Items'),
      description: __('No item matches "{0}".', [search.value]),
    }
  return null
})
</script>
