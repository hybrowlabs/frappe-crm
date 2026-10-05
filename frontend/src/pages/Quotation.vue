<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Button
          v-if="canOrder"
          :label="__('Create Sales Order')"
          variant="solid"
          iconLeft="shopping-cart"
          :loading="ordering"
          @click="createSalesOrder"
        />
        <Button :label="__('Print')" iconLeft="printer" @click="printDoc" />
      </div>
    </template>
  </LayoutHeader>
  <div v-if="q" class="flex-1 overflow-y-auto">
    <div class="mx-auto flex max-w-5xl flex-col gap-6 p-5">
      <!-- Header -->
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div class="flex min-w-0 flex-1 flex-col gap-1.5">
          <div class="flex items-center gap-2">
            <span class="text-2xl font-semibold text-ink-gray-9">
              {{ q.customer_name || q.party_name }}
            </span>
            <Badge
              :label="__(q.indicator.label)"
              :theme="indicatorTheme(q.indicator.color)"
              variant="subtle"
              size="lg"
            />
          </div>
          <div
            v-if="q.billing_address"
            class="mt-1 flex max-w-2xl flex-col gap-1"
          >
            <span class="text-sm text-ink-gray-5">{{ __('Billing Address') }}</span>
            <span v-if="address.street" class="text-base leading-relaxed text-ink-gray-8">
              {{ address.street }}
            </span>
            <span v-if="address.place" class="text-base text-ink-gray-8">{{ address.place }}</span>
            <div v-if="address.gstin" class="mt-2 flex items-baseline gap-2">
              <span class="text-sm text-ink-gray-5">{{ __('GSTIN') }}</span>
              <span class="text-base text-ink-gray-8">{{ address.gstin }}</span>
            </div>
          </div>
          <div v-if="q.deal" class="text-sm text-ink-gray-6">
            <router-link
              :to="{ name: 'Deal', params: { dealId: q.deal } }"
              class="text-ink-gray-8 underline decoration-outline-gray-3 underline-offset-2 hover:text-ink-gray-9"
            >
              {{ q.deal }}
            </router-link>
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
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, i) in q.items"
                :key="i"
                class="border-t border-outline-gray-1 align-top"
              >
                <td class="px-3 py-2.5 text-ink-gray-5">{{ i + 1 }}</td>
                <td class="px-3 py-2.5">
                  <div class="text-ink-gray-8">{{ item.item_code }}</div>
                </td>
                <td class="whitespace-pre-line px-3 py-2.5 text-sm text-ink-gray-6">
                  {{ item.description || '—' }}
                </td>
                <td class="px-3 py-2.5 text-ink-gray-6">{{ item.gst_hsn_code || '—' }}</td>
                <td class="px-3 py-2.5 text-right text-ink-gray-6">
                  {{ item.gst_rate == null ? '—' : `${item.gst_rate}%` }}
                </td>
                <td class="px-3 py-2.5 text-ink-gray-8">
                  {{ item.custom_no_of_packs || '—' }}
                  <div v-if="item.custom_no_of_packs" class="mt-1 text-sm text-ink-gray-5">
                    {{ __('{0} per pack', [item.custom_base_qty]) }}
                  </div>
                </td>
                <td class="px-3 py-2.5 text-ink-gray-8">{{ formatQty(item.qty) }}</td>
                <td class="px-3 py-2.5 text-ink-gray-6">{{ item.uom || '—' }}</td>
                <td class="px-3 py-2.5 text-right text-ink-gray-8">
                  {{ item.rate ? amount(item.rate) : '—' }}
                </td>
                <td class="px-3 py-2.5 text-right text-ink-gray-8">
                  {{ item.rate ? amount(item.amount) : '—' }}
                </td>
              </tr>
              <tr v-if="!q.items.length">
                <td colspan="10" class="px-3 py-6 text-center text-ink-gray-5">
                  {{ __('No items') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Totals: every line always shown, ₹0.00 when absent -->
      <div class="flex justify-end">
        <div class="flex w-full max-w-sm flex-col gap-2 rounded-lg border border-outline-gray-2 p-4 text-base">
          <div class="flex justify-between">
            <span class="text-ink-gray-5">{{ __('Taxable Amount') }}</span>
            <span class="text-ink-gray-8">{{ amount(q.net_total) }}</span>
          </div>
          <div v-if="q.discount_amount" class="flex justify-between">
            <span class="text-ink-gray-5">{{ __('Discount') }}</span>
            <span class="text-ink-gray-8">− {{ amount(q.discount_amount) }}</span>
          </div>
          <div v-for="line in totals" :key="line.label" class="flex justify-between">
            <span class="text-ink-gray-5">{{ __(line.label) }}</span>
            <span class="text-ink-gray-8">{{ amount(line.value) }}</span>
          </div>
          <div class="flex justify-between border-t border-outline-gray-2 pt-2">
            <span class="font-medium text-ink-gray-8">{{ __('Grand Total') }}</span>
            <span class="font-medium text-ink-gray-9">{{ amount(q.rounded_total || q.grand_total) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <ErrorPage
    v-else-if="quotation.error"
    :errorTitle="errorTitle"
    :errorMessage="__('You may not have access to this quotation, or it does not exist.')"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import { formatDate } from '@/utils'
import { addressParts, indicatorTheme, totalsLines, useCurrencyFormat } from '@/utils/quotation'
import { formatQty } from '@/utils/qty'
import { Breadcrumbs, Badge, Button, call, createResource, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  quotationId: { type: String, required: true },
})

const quotation = createResource({
  url: 'crm.api.quotation.get_quotation',
  params: { name: props.quotationId },
  cache: ['Quotation', props.quotationId],
  auto: true,
})

const q = computed(() => quotation.data)

const errorTitle = computed(() =>
  quotation.error?.exc_type === 'DoesNotExistError'
    ? __('Quotation not found')
    : __('Not permitted'),
)

// Tax lines with no amount (e.g. IGST on an intra-state sale) are left out.
const totals = computed(() => totalsLines(q.value))
const address = computed(() => addressParts(q.value?.billing_address))
const amount = useCurrencyFormat(() => q.value?.currency)

// The branch's print format from CRM Custom Settings; with none set, no `format`
// param goes out and Frappe uses the doctype's default.
const printDoc = () => {
  const format = q.value?.print_format
  window.open(
    `/printview?doctype=Quotation&name=${encodeURIComponent(props.quotationId)}` +
      (format ? `&format=${encodeURIComponent(format)}` : '') +
      '&trigger_print=1',
    '_blank',
  )
}

// A submitted quotation can be ordered once, while it has not expired; the
// button goes once a Sales Order stands against it. Valid Till is checked too,
// since ERPNext only marks a quotation Expired in its nightly job.
const today = new Date().toLocaleDateString('en-CA')
const expired = computed(
  () => q.value?.status === 'Expired' || (!!q.value?.valid_till && q.value.valid_till < today),
)
const canOrder = computed(
  () => q.value?.docstatus === 1 && !expired.value && !q.value?.sales_orders?.length,
)
const ordering = ref(false)

async function createSalesOrder() {
  ordering.value = true
  try {
    const result = await call('crm.api.quotation.create_sales_order', {
      quotation: props.quotationId,
    })
    if (!result?.ok) {
      toast.error(result?.message || __('Could not create the Sales Order.'))
    } else if (result.reason === 'pending_approval') {
      toast.warning(result.message)
    } else {
      toast.success(__('Sales Order {0} created.', [result.sales_order]))
    }
    // Either way the quotation now shows whichever Sales Order stands against it.
    quotation.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not create the Sales Order.'))
  } finally {
    ordering.value = false
  }
}

const details = computed(() => [
  { label: __('Date'), value: formatDate(q.value.transaction_date, '', true) },
  { label: __('Valid Till'), value: formatDate(q.value.valid_till, '', true) },
  { label: __('Customer'), value: q.value.customer_name || q.value.party_name },
  { label: __('Company'), value: q.value.company },
  { label: __('Order Type'), value: q.value.order_type },
  { label: __('Sale By'), value: q.value.sale_by },
  ...(q.value.sales_orders || []).map((name) => ({
    label: __('Sales Order'),
    value: q.value.sales_order_states?.[name]
      ? `${name} · ${__(q.value.sales_order_states[name].label)}`
      : name,
    to: { name: 'Sales Order', params: { salesOrderId: name } },
  })),
  { label: __('Payment Terms'), value: q.value.payment_terms_template },
])

const breadcrumbs = computed(() => [
  { label: __('Quotations'), route: { name: 'Quotations' } },
  {
    label: props.quotationId,
    route: { name: 'Quotation', params: { quotationId: props.quotationId } },
  },
])
</script>
