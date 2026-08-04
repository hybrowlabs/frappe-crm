<template>
  <div v-if="pending.data?.length" class="border-b px-5 py-3">
    <div class="mb-1 text-sm font-medium text-ink-gray-8">
      {{ __('Pending vertical deals') }}
    </div>
    <div
      v-for="v in pending.data"
      :key="v.field"
      class="flex items-center justify-between gap-2 py-1"
    >
      <div class="text-base text-ink-gray-7">
        {{ __(v.label) }}
        <span
          v-if="v.requires_documents"
          class="block text-xs text-ink-gray-5"
        >
          {{ __('Documents not shared') }}
        </span>
      </div>
      <Button
        :label="__('Create Deal')"
        :loading="creating === v.field"
        @click="create(v)"
      />
    </div>
    <CreateVerticalDealDialog
      v-model="showDialog"
      :lead="lead"
      :vertical="selected"
      @created="onCreated"
    />
  </div>
</template>

<script setup>
import CreateVerticalDealDialog from '@/components/Endovia/CreateVerticalDealDialog.vue'
import { createResource, call, toast, Button } from 'frappe-ui'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: { type: String, required: true },
})

const router = useRouter()
const creating = ref('')
const showDialog = ref(false)
const selected = ref(null)

const pending = createResource({
  url: 'endovia_finance.api.conversion.get_pending_verticals',
  params: { lead: props.lead },
  auto: true,
})

function create(v) {
  if (v.requires_documents) {
    selected.value = v
    showDialog.value = true
    return
  }
  creating.value = v.field
  call('endovia_finance.api.conversion.convert_for_vertical', {
    lead: props.lead,
    vertical_field: v.field,
  })
    .then((deal) => onCreated(deal))
    .catch((err) =>
      toast.error(err.messages?.[0] || __('Could not create the deal')),
    )
    .finally(() => (creating.value = ''))
}

function onCreated(deal) {
  showDialog.value = false
  pending.reload()
  toast.success(__('Deal {0} created', [deal]))
  router.push({ name: 'Deal', params: { dealId: deal } })
}
</script>
