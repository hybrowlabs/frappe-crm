<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          {
            label: __('Pending Conversions'),
            route: { name: 'PendingConversions' },
          },
        ]"
      />
    </template>
    <template #right-header>
      <Button :label="__('Refresh')" icon-left="refresh-cw" @click="leads.reload()" />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto p-5">
    <div
      v-if="!rows.length && !leads.loading"
      class="flex h-full flex-col items-center justify-center gap-2 text-ink-gray-4"
    >
      <ConvertIcon class="h-8 w-8" />
      <span class="text-lg">{{ __('No pending conversions') }}</span>
    </div>

    <table v-else class="w-full border-separate border-spacing-0 text-base">
      <thead>
        <tr class="text-left text-sm text-ink-gray-5">
          <th class="border-b px-3 py-2 font-medium">{{ __('Lead') }}</th>
          <th class="border-b px-3 py-2 font-medium">{{ __('Vertical') }}</th>
          <th class="border-b px-3 py-2 font-medium">{{ __('Documents') }}</th>
          <th class="border-b px-3 py-2 font-medium">
            {{ __('Relationship Manager') }}
          </th>
          <th class="border-b px-3 py-2 font-medium">{{ __('Mobile') }}</th>
          <th class="border-b px-3 py-2 font-medium">
            {{ __('Last Modified') }}
          </th>
          <th class="border-b px-3 py-2"></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.lead + row.vertical"
          class="text-ink-gray-8"
        >
          <td class="border-b px-3 py-2">
            <router-link
              class="font-medium text-ink-gray-9 hover:underline"
              :to="{ name: 'Lead', params: { leadId: row.lead } }"
            >
              {{ row.lead_name || row.lead }}
            </router-link>
          </td>
          <td class="border-b px-3 py-2">{{ __(row.vertical) }}</td>
          <td class="border-b px-3 py-2">
            <Badge
              v-if="row.requiresDocuments"
              :label="__('Not shared')"
              theme="orange"
              variant="subtle"
            />
            <Badge
              v-else
              :label="__('Ready')"
              theme="green"
              variant="subtle"
            />
          </td>
          <td class="border-b px-3 py-2">{{ row.lead_owner }}</td>
          <td class="border-b px-3 py-2">{{ row.mobile_no }}</td>
          <td class="border-b px-3 py-2 text-ink-gray-5">
            {{ timeAgo(row.modified) }}
          </td>
          <td class="border-b px-3 py-2 text-right">
            <Button
              :label="__('Create Deal')"
              :loading="creating === row.lead + row.vertical"
              @click="create(row)"
            />
          </td>
        </tr>
      </tbody>
    </table>

    <CreateVerticalDealDialog
      v-model="showDialog"
      :lead="selected?.lead || ''"
      :vertical="selectedVertical"
      @created="onCreated"
    />
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ConvertIcon from '@/components/Icons/ConvertIcon.vue'
import CreateVerticalDealDialog from '@/components/Endovia/CreateVerticalDealDialog.vue'
import { timeAgo } from '@/utils'
import {
  Breadcrumbs,
  Badge,
  Button,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const VERTICAL_FIELD = {
  'Wealth Management': 'wealth_management',
  Quant: 'quant',
  Vault: 'vault',
  Books: 'books',
}

const creating = ref('')
const showDialog = ref(false)
const selected = ref(null)

const leads = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Lead',
    filters: { pending_verticals: ['is', 'set'] },
    fields: [
      'name',
      'lead_name',
      'pending_verticals',
      'lead_owner',
      'mobile_no',
      'vault_documents_shared',
      'modified',
    ],
    order_by: 'modified desc',
    limit_page_length: 0,
  },
  auto: true,
})

// one row per (lead, pending vertical)
const rows = computed(() =>
  (leads.data || []).flatMap((lead) =>
    (lead.pending_verticals || '')
      .split(',')
      .map((v) => v.trim())
      .filter(Boolean)
      .map((vertical) => ({
        lead: lead.name,
        lead_name: lead.lead_name,
        lead_owner: lead.lead_owner,
        mobile_no: lead.mobile_no,
        modified: lead.modified,
        vertical,
        requiresDocuments: vertical === 'Vault' && !lead.vault_documents_shared,
      })),
  ),
)

const selectedVertical = computed(() =>
  selected.value
    ? {
        field: VERTICAL_FIELD[selected.value.vertical],
        label: selected.value.vertical,
      }
    : null,
)

function create(row) {
  if (row.requiresDocuments) {
    selected.value = row
    showDialog.value = true
    return
  }
  creating.value = row.lead + row.vertical
  call('endovia_finance.api.conversion.convert_for_vertical', {
    lead: row.lead,
    vertical_field: VERTICAL_FIELD[row.vertical],
  })
    .then((deal) => onCreated(deal))
    .catch((err) =>
      toast.error(err.messages?.[0] || __('Could not create the deal')),
    )
    .finally(() => (creating.value = ''))
}

function onCreated(deal) {
  showDialog.value = false
  toast.success(__('Deal {0} created', [deal]))
  leads.reload()
}
</script>
