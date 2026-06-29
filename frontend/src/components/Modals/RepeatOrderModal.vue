<template>
  <StageFormDialog
    v-model="show"
    :title="__('Repeat Order')"
    :subtitle="subtitle"
    size="xl"
  >
    <StageCallout theme="green" icon="zap" class="mb-3">
      {{
        __(
          'Opens the create-quote page prefilled from this organization — its ERPNext customer, previously-ordered items, and the Created-from-CRM flag. No deal is attached.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Items to repeat')" icon="package">
      <p v-if="!preview.customer" class="text-p-sm text-ink-gray-5">
        {{
          __(
            'No ERPNext customer is linked to this organization yet. Create the customer from a deal first.',
          )
        }}
      </p>
      <p v-else-if="!preview.items?.length" class="text-p-sm text-ink-gray-5">
        {{ __('No previously-ordered items found for this organization.') }}
      </p>
      <div v-else class="text-p-sm text-ink-gray-7">
        <p class="mb-2">
          {{ __('Customer') }}:
          <span class="font-medium">{{ preview.customer }}</span>
        </p>
        <ul class="list-disc pl-5">
          <li v-for="it in preview.items" :key="it.item_code">
            {{ it.item_code }} × {{ it.quantity || 1 }}
          </li>
        </ul>
      </div>
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create Quotation')"
          :loading="creating"
          @click="createQuotation"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
      </div>
    </template>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageSection from '@/components/StageForms/StageSection.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import { Button, createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  org: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })

// ---- preview of what the repeat order will prefill ----
const preview = ref({})
createResource({
  url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_repeat_order_preview',
  params: { organization: props.org },
  auto: true,
  onSuccess: (d) => (preview.value = d || {}),
})

const creating = ref(false)

function createQuotation() {
  creating.value = true
  createResource({
    url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_repeat_order_quotation_url',
    params: { organization: props.org },
    auto: true,
    onSuccess(url) {
      creating.value = false
      show.value = false
      if (url) window.open(url, '_blank')
    },
    onError(err) {
      creating.value = false
      toast.error(err.messages?.[0] || __('Error creating quotation'))
    },
  })
}
</script>
