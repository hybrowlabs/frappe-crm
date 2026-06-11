<template>
  <StageFormDialog v-model="show" :title="__('Quotations')" :subtitle="org" size="2xl">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[28rem] text-base">
        <thead>
          <tr class="border-b border-outline-gray-2 text-left text-ink-gray-5">
            <th class="py-2 font-medium">{{ __('Quotation No') }}</th>
            <th class="py-2 font-medium">{{ __('Date') }}</th>
            <th class="py-2 font-medium">{{ __('Amount') }}</th>
            <th class="py-2 font-medium">{{ __('Status') }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="q in quotes"
            :key="q.no"
            class="cursor-pointer border-b border-outline-gray-1 hover:bg-surface-gray-1"
            @click="openQuotation(q)"
          >
            <td class="py-2.5 font-medium text-ink-gray-8">{{ q.no }}</td>
            <td class="py-2.5 text-ink-gray-5">{{ q.date }}</td>
            <td class="py-2.5 font-medium">{{ fmtINR(q.amount) }}</td>
            <td class="py-2.5">
              <Badge :label="q.status" :theme="qTheme(q.status)" variant="subtle" />
            </td>
            <td class="py-2.5 text-right">
              <Button
                variant="ghost"
                size="sm"
                :label="__('Open')"
                @click.stop="openQuotation(q)"
              />
            </td>
          </tr>
          <tr v-if="!quotes.length">
            <td colspan="5" class="py-6 text-center text-ink-gray-5">
              {{ __('No quotations linked to this deal yet.') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import { Button, Badge, createListResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  org: { type: String, default: '' },
  dealId: { type: String, default: '' },
  value: { type: Number, default: 0 },
})

const show = defineModel({ type: Boolean })

const fmtINR = (n) => '₹' + Number(n).toLocaleString('en-IN')

// Quotations linked to this deal via the custom_deal field in ERPNext.
const quotationResource = createListResource({
  doctype: 'Quotation',
  filters: { custom_deal: props.dealId },
  fields: ['name', 'transaction_date', 'grand_total', 'status', 'valid_till'],
  orderBy: 'transaction_date desc',
  pageLength: 99,
  auto: true,
})
const quotes = computed(() =>
  (quotationResource.data || []).map((q) => ({
    no: q.name,
    date: q.transaction_date,
    amount: q.grand_total,
    status: q.status,
    validTill: q.valid_till,
  })),
)

function openQuotation(q) {
  window.open(`/app/quotation/${encodeURIComponent(q.no)}`, '_blank')
}

function qTheme(s) {
  return { Sent: 'blue', Accepted: 'green', Draft: 'gray', Superseded: 'gray' }[s] || 'gray'
}
</script>
