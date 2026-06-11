<template>
  <StageFormDialog
    v-model="show"
    :title="preview ? `${__('Quotation')} · ${preview.no}` : __('Quotations')"
    :subtitle="org"
    :size="preview ? '3xl' : '2xl'"
  >
    <!-- list -->
    <div v-if="!preview" class="overflow-x-auto">
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
          @click="preview = q"
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
              :label="__('View PDF')"
              @click.stop="preview = q"
            />
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <!-- PDF preview -->
    <div
      v-else
      class="rounded-lg border border-outline-gray-2 bg-surface-white p-5 text-base"
    >
      <div class="flex items-start justify-between border-b border-outline-gray-2 pb-4">
        <div>
          <div class="text-lg font-bold tracking-wide text-ink-gray-9">
            PRECIOUS ALLOYS
          </div>
          <div class="text-sm text-ink-gray-5">
            Precious Alloys Pvt Ltd · Zaveri Bazaar, Mumbai 400004 · GSTIN
            27AABCP1234E1Z5
          </div>
        </div>
        <div class="text-right">
          <div class="text-lg font-bold text-ink-gray-9">QUOTATION</div>
          <div class="text-sm text-ink-gray-6">{{ preview.no }}</div>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3 py-4 text-sm sm:grid-cols-4">
        <div><div class="text-ink-gray-5">{{ __('Buyer') }}</div><div class="font-medium text-ink-gray-8">{{ org }}</div></div>
        <div><div class="text-ink-gray-5">{{ __('Date') }}</div><div class="font-medium text-ink-gray-8">{{ preview.date }}</div></div>
        <div><div class="text-ink-gray-5">{{ __('Valid Till') }}</div><div class="font-medium text-ink-gray-8">{{ preview.validTill }}</div></div>
        <div><div class="text-ink-gray-5">{{ __('Account Type') }}</div><div class="font-medium text-ink-gray-8">Customer</div></div>
      </div>
      <table class="w-full border-collapse text-sm">
        <thead>
          <tr class="border-y border-outline-gray-2 text-left text-ink-gray-5">
            <th class="py-2">#</th><th class="py-2">{{ __('Item') }}</th>
            <th class="py-2">HSN</th><th class="py-2">{{ __('Qty') }}</th>
            <th class="py-2">{{ __('Rate') }}</th><th class="py-2">{{ __('Amount') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-b border-outline-gray-1">
            <td class="py-2">1</td>
            <td class="py-2">Alloys · Yellow Gold</td>
            <td class="py-2">7113</td>
            <td class="py-2">12 KG</td>
            <td class="py-2">{{ fmtINR(rate) }}</td>
            <td class="py-2">{{ fmtINR(preview.amount) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="ml-auto mt-4 w-56 text-sm">
        <div class="flex justify-between py-1"><span class="text-ink-gray-5">{{ __('Subtotal') }}</span><span>{{ fmtINR(preview.amount) }}</span></div>
        <div class="flex justify-between py-1"><span class="text-ink-gray-5">{{ __('GST @ 3%') }}</span><span>{{ fmtINR(gst) }}</span></div>
        <div class="flex justify-between border-t border-outline-gray-2 py-1 font-semibold text-ink-gray-9"><span>{{ __('Total') }}</span><span>{{ fmtINR(preview.amount + gst) }}</span></div>
      </div>
    </div>

    <template #actions>
      <div v-if="preview" class="flex items-center gap-2">
        <Button :label="__('Back')" @click="preview = null" />
        <span class="flex-1" />
        <Button :label="__('Download PDF')">
          <template #prefix><StageIcon name="upload" class="h-4 w-4" /></template>
        </Button>
        <Button variant="solid" :label="__('Email')">
          <template #prefix><StageIcon name="mail" class="h-4 w-4" /></template>
        </Button>
      </div>
      <div v-else class="flex items-center">
        <span class="flex-1" />
        <Button :label="__('Create in Desk')">
          <template #prefix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
      </div>
    </template>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import { Button, Badge } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  org: { type: String, default: '' },
  dealId: { type: String, default: 'CRM-DEAL-2026-0034' },
  value: { type: Number, default: 130000 },
})

const show = defineModel({ type: Boolean })
const preview = ref(null)

const fmtINR = (n) => '₹' + Number(n).toLocaleString('en-IN')

const qno = computed(() => (props.dealId || 'CRM-DEAL-2026-0034').replace('DEAL', 'QTN'))
const quotes = computed(() => [
  { no: qno.value, date: '12 Apr 2025', amount: props.value, status: 'Sent', validTill: '12 May 2025' },
  {
    no: qno.value.replace(/(\d+)$/, (m) => String(+m - 7).padStart(4, '0')),
    date: '28 Mar 2025',
    amount: Math.round(props.value * 0.94),
    status: 'Superseded',
    validTill: '28 Apr 2025',
  },
])

const rate = computed(() => Math.round((preview.value?.amount || 0) / 12))
const gst = computed(() => Math.round((preview.value?.amount || 0) * 0.03))

function qTheme(s) {
  return { Sent: 'blue', Accepted: 'green', Draft: 'gray', Superseded: 'gray' }[s] || 'gray'
}
</script>
