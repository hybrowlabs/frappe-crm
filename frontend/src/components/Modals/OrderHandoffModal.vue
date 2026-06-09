<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="green" icon="check" class="mb-3.5">
      <b>{{ __('Deal Won{0}.', [value ? ` — ${value}` : '']) }}</b>
      {{
        __(
          'CRM work complete. Handed to operations for fulfilment. The handoff chain below runs in ERPNext.',
        )
      }}
    </StageCallout>

    <div
      class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white"
    >
      <div
        class="flex items-center gap-2 border-b border-outline-gray-2 px-3.5 py-2.5"
      >
        <StageIcon name="package" class="text-ink-gray-5" />
        <span class="text-base font-medium text-ink-gray-8">
          {{ __('Order-to-Cash Handoff') }}
        </span>
      </div>
      <div
        v-for="(s, i) in steps"
        :key="i"
        class="flex items-center gap-3 px-3.5 py-3"
        :class="i < steps.length - 1 ? 'border-b border-outline-gray-1' : ''"
      >
        <div
          class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
          :class="
            s.done
              ? 'bg-surface-green-2 text-ink-green-3'
              : 'bg-surface-gray-3 text-ink-gray-5'
          "
        >
          <StageIcon :name="s.done ? 'check' : s.icon" :size="15" />
        </div>
        <div class="flex-1">
          <div class="text-base font-medium text-ink-gray-8">{{ s.what }}</div>
          <div class="text-sm text-ink-gray-5">{{ s.who }}</div>
        </div>
        <Badge
          :label="s.done ? __('Done') : __('Pending')"
          :theme="s.done ? 'green' : 'gray'"
          variant="subtle"
        />
      </div>
    </div>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import { Badge } from 'frappe-ui'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  value: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })

const steps = [
  {
    who: 'Aditi · Backend',
    what: __('Sales Order auto-created in ERPNext'),
    icon: 'package',
    done: true,
  },
  {
    who: 'Ram / Devyani',
    what: __('Invoice generated from Sales Order'),
    icon: 'fileText',
    done: true,
  },
  {
    who: 'Gharat / Roshan',
    what: __('Delivery docket logged · docs attached'),
    icon: 'arrowRight',
    done: false,
  },
  {
    who: 'Accounts (Tejal)',
    what: __('Payment tracked vs terms'),
    icon: 'rupee',
    done: false,
  },
  {
    who: 'Auto T+24h',
    what: __('NPS · CES · CSAT feedback sent'),
    icon: 'gauge',
    done: false,
  },
]
</script>
