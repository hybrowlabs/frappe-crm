<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div v-if="q" class="flex-1 overflow-y-auto">
    <div class="mx-auto flex max-w-5xl flex-col gap-6 p-5">
      <!-- Header -->
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center gap-2">
            <span class="text-2xl font-semibold text-ink-gray-9">{{ q.name }}</span>
            <Badge
              :label="__(q.indicator.label)"
              :theme="indicatorTheme(q.indicator.color)"
              variant="subtle"
              size="lg"
            />
          </div>
          <div class="text-base text-ink-gray-6">
            {{ q.customer_name || q.customer }}
            <template v-if="q.quotation">
              ·
              <router-link
                :to="{ name: 'Quotation', params: { quotationId: q.quotation } }"
                class="text-ink-gray-8 underline decoration-outline-gray-3 underline-offset-2 hover:text-ink-gray-9"
              >
                {{ q.quotation }}
              </router-link>
            </template>
          </div>
        </div>
        <div class="text-right">
          <div class="text-sm text-ink-gray-5">{{ __('Grand Total') }}</div>
          <div class="text-2xl font-semibold text-ink-gray-9">
            {{ amount(q.rounded_total || q.grand_total) }}
          </div>
        </div>
      </div>

      <!-- Details -->
      <div
        class="grid grid-cols-2 gap-x-6 gap-y-4 rounded-lg border border-outline-gray-2 p-4 sm:grid-cols-4"
      >
        <div v-for="d in details" :key="d.label" class="flex flex-col gap-1">
          <span class="text-sm text-ink-gray-5">{{ d.label }}</span>
          <router-link
            v-if="d.to"
            :to="d.to"
            class="truncate text-base text-ink-gray-8 underline decoration-outline-gray-3 underline-offset-2 hover:text-ink-gray-9"
          >
            {{ d.value }}
          </router-link>
          <span v-else class="truncate text-base text-ink-gray-8">{{ d.value || '—' }}</span>
        </div>
      </div>

      <!-- Items -->
      <div class="flex flex-col gap-2">
        <div class="text-lg font-medium text-ink-gray-9">{{ __('Items') }}</div>
        <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
          <table class="w-full min-w-[40rem] text-base">
            <thead>
              <tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
                <th class="px-3 py-2 font-medium">#</th>
                <th class="px-3 py-2 font-medium">{{ __('Item') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Qty') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Delivered') }}</th>
                <th class="px-3 py-2 font-medium">{{ __('UOM') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Rate') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Amount') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, i) in q.items"
                :key="i"
                class="border-t border-outline-gray-1"
              >
                <td class="px-3 py-2.5 text-ink-gray-5">{{ i + 1 }}</td>
                <td class="px-3 py-2.5">
                  <div class="text-ink-gray-8">{{ item.item_name || item.item_code }}</div>
                  <div
                    v-if="item.item_name && item.item_name !== item.item_code"
                    class="text-sm text-ink-gray-5"
                  >
                    {{ item.item_code }}
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right">{{ item.qty }}</td>
                <td class="px-3 py-2.5 text-right">{{ item.delivered_qty || 0 }}</td>
                <td class="px-3 py-2.5 text-ink-gray-6">{{ item.uom }}</td>
                <td class="px-3 py-2.5 text-right">{{ amount(item.rate) }}</td>
                <td class="px-3 py-2.5 text-right font-medium">{{ amount(item.amount) }}</td>
              </tr>
              <tr v-if="!q.items.length">
                <td colspan="7" class="px-3 py-6 text-center text-ink-gray-5">
                  {{ __('No items') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Taxes -->
      <div v-if="q.taxes.length" class="flex flex-col gap-2">
        <div class="text-lg font-medium text-ink-gray-9">{{ __('Taxes') }}</div>
        <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
          <table class="w-full min-w-[28rem] text-base">
            <thead>
              <tr class="bg-surface-gray-2 text-left text-sm text-ink-gray-5">
                <th class="px-3 py-2 font-medium">{{ __('Description') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Rate') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Amount') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(tax, i) in q.taxes"
                :key="i"
                class="border-t border-outline-gray-1"
              >
                <td class="px-3 py-2.5 text-ink-gray-8">{{ tax.description }}</td>
                <td class="px-3 py-2.5 text-right">{{ tax.rate ? `${tax.rate}%` : '' }}</td>
                <td class="px-3 py-2.5 text-right">{{ amount(tax.tax_amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Totals -->
      <div class="flex justify-end">
        <div class="flex w-full max-w-xs flex-col gap-2 text-base">
          <div class="flex justify-between">
            <span class="text-ink-gray-5">{{ __('Net Total') }}</span>
            <span class="text-ink-gray-8">{{ amount(q.net_total) }}</span>
          </div>
          <div v-if="q.total_taxes_and_charges" class="flex justify-between">
            <span class="text-ink-gray-5">{{ __('Taxes') }}</span>
            <span class="text-ink-gray-8">{{ amount(q.total_taxes_and_charges) }}</span>
          </div>
          <div v-if="q.discount_amount" class="flex justify-between">
            <span class="text-ink-gray-5">{{ __('Discount') }}</span>
            <span class="text-ink-gray-8">− {{ amount(q.discount_amount) }}</span>
          </div>
          <div class="flex justify-between border-t border-outline-gray-2 pt-2">
            <span class="font-medium text-ink-gray-8">{{ __('Grand Total') }}</span>
            <span class="font-medium text-ink-gray-9">{{ amount(q.grand_total) }}</span>
          </div>
          <div
            v-if="q.rounded_total && q.rounded_total !== q.grand_total"
            class="flex justify-between"
          >
            <span class="text-ink-gray-5">{{ __('Rounded Total') }}</span>
            <span class="font-medium text-ink-gray-9">{{ amount(q.rounded_total) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <ErrorPage
    v-else-if="order.error"
    :errorTitle="errorTitle"
    :errorMessage="__('You may not have access to this sales order, or it does not exist.')"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import { formatDate } from '@/utils'
import { indicatorTheme, formatQuotationAmount } from '@/utils/quotation'
import { Breadcrumbs, Badge, createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  salesOrderId: { type: String, required: true },
})

const order = createResource({
  url: 'crm.api.sales_order_list.get_sales_order',
  params: { name: props.salesOrderId },
  cache: ['Sales Order', props.salesOrderId],
  auto: true,
})

const q = computed(() => order.data)

const errorTitle = computed(() =>
  order.error?.exc_type === 'DoesNotExistError'
    ? __('Sales Order not found')
    : __('Not permitted'),
)

const amount = (v) => formatQuotationAmount(v, q.value?.currency)

const details = computed(() => [
  { label: __('Date'), value: formatDate(q.value.transaction_date, '', true) },
  { label: __('Delivery Date'), value: formatDate(q.value.delivery_date, '', true) },
  { label: __('Customer'), value: q.value.customer_name || q.value.customer },
  { label: __('Company'), value: q.value.company },
  { label: __('Branch'), value: q.value.branch },
  { label: __('Sale By'), value: q.value.sale_by },
  { label: __('Delivered'), value: `${Math.round(q.value.per_delivered || 0)}%` },
  { label: __('Billed'), value: `${Math.round(q.value.per_billed || 0)}%` },
])

const breadcrumbs = computed(() => [
  { label: __('Sales Orders'), route: { name: 'Sales Orders' } },
  {
    label: props.salesOrderId,
    route: { name: 'Sales Order', params: { salesOrderId: props.salesOrderId } },
  },
])
</script>
