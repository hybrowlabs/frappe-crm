<template>
  <!-- Mobile: one card per row, since the full table needs ~62rem -->
  <div v-if="isMobileView" class="flex flex-col gap-3">
    <div
      v-for="(item, i) in items"
      :key="i"
      class="flex flex-col gap-2 rounded-lg border border-blue-500 p-3 text-base"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="text-sm text-ink-gray-5">#{{ i + 1 }}</div>
          <div class="break-words font-medium text-ink-gray-9">{{ item.item_code }}</div>
        </div>
        <div class="shrink-0 text-right">
          <div class="text-sm text-ink-gray-5">{{ __('Amount') }}</div>
          <div class="font-medium text-ink-gray-9">
            {{ item.rate ? amount(item.amount) : '—' }}
          </div>
        </div>
      </div>
      <div
        v-if="item.description"
        class="whitespace-pre-line break-words text-sm text-ink-gray-6"
      >
        {{ item.description }}
      </div>
      <div class="grid grid-cols-3 gap-x-3 gap-y-2 border-t border-outline-gray-2 pt-2 text-sm">
        <div v-for="f in fields(item)" :key="f.label" class="flex min-w-0 flex-col">
          <span class="text-ink-gray-5">{{ f.label }}</span>
          <span class="break-words text-ink-gray-8">{{ f.value }}</span>
        </div>
      </div>
    </div>
    <div
      v-if="!items.length"
      class="rounded-lg border border-blue-500 px-3 py-6 text-center text-base text-ink-gray-5"
    >
      {{ __('No items') }}
    </div>
  </div>

  <div v-else class="overflow-x-auto rounded-lg border border-blue-500">
    <table class="w-full min-w-[62rem] text-base">
      <thead>
        <tr class="border-b border-blue-500 bg-surface-gray-2 text-left text-sm text-ink-gray-5">
          <th class="w-10 px-3 py-2 font-medium">SR No.</th>
          <th class="min-w-[8rem] px-3 py-2 font-medium">{{ __('Item') }}</th>
          <th class="min-w-[12rem] px-3 py-2 font-medium">{{ __('Description') }}</th>
          <th class="w-24 px-3 py-2 font-medium">{{ __('HSN') }}</th>
          <th class="w-16 px-3 py-2 text-right font-medium">{{ __('GST') }}</th>
          <th class="w-16 px-3 py-2 font-medium">{{ __('UOM') }}</th>
          <th class="w-28 whitespace-nowrap px-3 py-2 font-medium">{{ __('No of Packs') }}</th>
          <th class="w-24 px-3 py-2 font-medium">{{ __('Qty') }}</th>
          <th v-if="showDelivered" class="w-24 px-3 py-2 font-medium">{{ __('Delivered') }}</th>
          <th class="w-24 px-3 py-2 text-right font-medium">{{ __('Rate') }}</th>
          <th class="w-24 px-3 py-2 text-right font-medium">{{ __('Amount') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, i) in items" :key="i" class="border-t border-blue-500 align-top">
          <td class="px-3 py-2.5 text-ink-gray-5">{{ i + 1 }}</td>
          <td class="px-3 py-2.5 text-ink-gray-8">{{ item.item_code }}</td>
          <td class="whitespace-pre-line px-3 py-2.5 text-sm text-ink-gray-6">
            {{ item.description || '—' }}
          </td>
          <td class="px-3 py-2.5 text-ink-gray-6">{{ item.gst_hsn_code || '—' }}</td>
          <td class="px-3 py-2.5 text-right text-ink-gray-6">{{ gst(item) }}</td>
          <td class="px-3 py-2.5 text-ink-gray-6">{{ item.uom || '—' }}</td>
          <td class="px-3 py-2.5 text-ink-gray-8">{{ item.custom_no_of_packs || '—' }}</td>
          <td class="px-3 py-2.5 text-ink-gray-8">{{ formatQty(item.qty) }}</td>
          <td v-if="showDelivered" class="px-3 py-2.5 text-ink-gray-8">
            {{ formatQty(item.delivered_qty || 0) }}
          </td>
          <td class="px-3 py-2.5 text-right text-ink-gray-8">
            {{ item.rate ? amount(item.rate) : '—' }}
          </td>
          <td class="px-3 py-2.5 text-right text-ink-gray-8">
            {{ item.rate ? amount(item.amount) : '—' }}
          </td>
        </tr>
        <tr v-if="!items.length">
          <td :colspan="showDelivered ? 11 : 10" class="px-3 py-6 text-center text-ink-gray-5">
            {{ __('No items') }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { isMobileView } from '@/composables/settings'
import { formatQty } from '@/utils/qty'

const props = defineProps({
  items: { type: Array, default: () => [] },
  // Formats a value in the document's currency.
  amount: { type: Function, required: true },
  showDelivered: { type: Boolean, default: false },
})

const gst = (item) => (item.gst_rate == null ? '—' : `${item.gst_rate}%`)

const fields = (item) => [
  { label: __('Qty'), value: formatQty(item.qty) },
  ...(props.showDelivered
    ? [{ label: __('Delivered'), value: formatQty(item.delivered_qty || 0) }]
    : []),
  { label: __('Rate'), value: item.rate ? props.amount(item.rate) : '—' },
  { label: __('UOM'), value: item.uom || '—' },
  { label: __('No of Packs'), value: item.custom_no_of_packs || '—' },
  { label: __('HSN'), value: item.gst_hsn_code || '—' },
  { label: __('GST'), value: gst(item) },
]
</script>
