<template>
  <div class="flex flex-col py-4">
    <div class="mb-3 flex items-center justify-between px-1">
      <div class="text-sm font-medium text-ink-gray-8">
        {{ __('Ordered Items') }}
        <span class="text-ink-gray-4">
          {{ __('{0} items', [orderedItems.data?.count || 0]) }}
        </span>
      </div>
      <Button
        v-if="selected.length"
        variant="solid"
        :label="__('Create Quotation')"
        iconLeft="file-text"
        :loading="creating"
        @click="createQuotation"
      />
    </div>

    <div class="overflow-x-auto">
      <table class="w-full min-w-[760px] text-sm">
        <thead>
          <tr class="border-b border-outline-gray-1 text-xs text-ink-gray-5">
            <th class="w-8 py-2 pr-2">
              <input
                type="checkbox"
                :checked="allSelected"
                class="h-4 w-4 cursor-pointer rounded-sm border-outline-gray-3 accent-blue-500"
                @change="toggleAll($event.target.checked)"
              />
            </th>
            <th class="py-2 pr-3 text-left font-normal">{{ __('Item') }}</th>
            <th class="px-3 py-2 text-right font-normal">{{ __('Monthly Vol.') }}</th>
            <th class="px-3 py-2 text-right font-normal">{{ __('Quarterly Vol.') }}</th>
            <th class="px-3 py-2 text-left font-normal">{{ __('Last Purchase') }}</th>
            <th class="px-3 py-2 text-right font-normal">{{ __('Total Purchase') }}</th>
            <th class="py-2 pl-3 text-right font-normal">{{ __('Total Qty') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="it in orderedItems.data?.items || []"
            :key="it.item_code"
            class="border-b border-outline-gray-1"
          >
            <td class="pr-2">
              <input
                type="checkbox"
                :checked="selected.includes(it.item_code)"
                class="h-4 w-4 cursor-pointer rounded-sm border-outline-gray-3 accent-blue-500"
                @change="setItemSelected(it.item_code, $event.target.checked)"
              />
            </td>
            <td class="py-2.5 pr-3">
              <div class="text-ink-gray-8">{{ it.item_name }}</div>
              <div class="text-xs text-ink-gray-4">{{ it.item_code }}</div>
            </td>
            <td class="px-3 text-right text-ink-gray-7">
              {{ vol(it.monthly_vol, it.uom) }}
            </td>
            <td class="px-3 text-right text-ink-gray-7">
              {{ vol(it.quarterly_vol, it.uom) }}
            </td>
            <td class="px-3 text-ink-gray-7">
              <template v-if="it.last_purchase">
                <div>{{ formatDate(it.last_purchase) }}</div>
                <div class="text-xs text-ink-gray-4">
                  {{ __(timeAgo(it.last_purchase)) }}
                </div>
              </template>
              <span v-else>—</span>
            </td>
            <td class="px-3 text-right text-ink-gray-8">
              {{ fmtCurrency(it.total_purchase) }}
            </td>
            <td class="pl-3 text-right text-ink-gray-7">
              {{ vol(it.total_qty, it.uom) }}
            </td>
          </tr>
          <tr v-if="orderedItems.data?.items?.length" class="font-medium">
            <td class="pr-2"></td>
            <td class="py-2.5 pr-3 text-ink-gray-8">{{ __('Total') }}</td>
            <td class="px-3 text-right text-ink-gray-4">—</td>
            <td class="px-3 text-right text-ink-gray-4">—</td>
            <td class="px-3 text-ink-gray-4">—</td>
            <td class="px-3 text-right text-ink-gray-8">
              {{ fmtCurrency(orderedItems.data.total_purchase) }}
            </td>
            <td class="pl-3 text-right text-ink-gray-4">—</td>
          </tr>
        </tbody>
      </table>
      <div
        v-if="orderedItems.data && !orderedItems.data.items.length"
        class="py-10 text-center text-sm text-ink-gray-4"
      >
        {{ __('No ordered items') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatDate, timeAgo } from '@/utils'
import { Button, createResource, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  organization: { type: String, required: true },
})

const orderedItems = createResource({
  url: 'crm.api.organization.get_ordered_items',
  params: { organization: props.organization },
  auto: true,
})

// Item codes the user has ticked to include in the quotation.
const selected = ref([])

const allSelected = computed(() => {
  const items = orderedItems.data?.items || []
  return items.length > 0 && selected.value.length === items.length
})

function setItemSelected(itemCode, checked) {
  const i = selected.value.indexOf(itemCode)
  if (checked && i === -1) selected.value.push(itemCode)
  else if (!checked && i !== -1) selected.value.splice(i, 1)
}

function toggleAll(checked) {
  selected.value = checked
    ? (orderedItems.data?.items || []).map((it) => it.item_code)
    : []
}

const creating = ref(false)

function createQuotation() {
  creating.value = true
  createResource({
    url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_repeat_order_quotation_url',
    params: {
      organization: props.organization,
      items: JSON.stringify(selected.value),
    },
    auto: true,
    onSuccess(url) {
      creating.value = false
      if (url) window.open(url, '_blank')
    },
    onError(err) {
      creating.value = false
      toast.error(err.messages?.[0] || __('Error creating quotation'))
    },
  })
}

function fmtCurrency(v) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(v || 0)
}

function vol(v, uom) {
  const n = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(
    v || 0,
  )
  return `${n} ${uom || ''}`.trim()
}
</script>
