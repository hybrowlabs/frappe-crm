<template>
  <StageFormDialog
    v-model="show"
    :title="__('Prepare for Quotation')"
    :subtitle="subtitle"
    size="2xl"
  >
    <StageSection :title="__('Customer')" icon="building">
      <StageCallout
        :theme="customerExists ? 'green' : 'amber'"
        :icon="customerExists ? 'check' : 'alert'"
        class="mb-3"
      >
        <template v-if="customerExists">
          {{ __('Customer') }} <b>{{ org }}</b>
          {{ __('already exists in ERPNext — its master will be used.') }}
        </template>
        <template v-else>
          {{ __('No ERPNext customer yet — one will be') }}
          <b>{{ __('created') }}</b>
          {{ __('from these details before the quotation.') }}
        </template>
      </StageCallout>
      <FieldGrid :cols="2">
        <FieldText
          v-model="legalName"
          :label="__('Legal / Registered Name')"
          required
        />
        <FieldText
          v-model="gst"
          :label="__('GSTIN')"
          required
          :help="__('Required to invoice')"
        />
      </FieldGrid>
      <FieldTextarea
        v-model="billing"
        :label="__('Billing Address')"
        required
        :rows="2"
      />
    </StageSection>

    <StageSection :title="__('Shipping & Freight')" icon="package">
      <FieldCheckbox
        :label="__('Shipping address same as billing')"
        :checked="sameAsBilling"
        @change="sameAsBilling = !sameAsBilling"
      />
      <FieldTextarea
        v-if="!sameAsBilling"
        v-model="shipping"
        :label="__('Shipping Address')"
        required
        :rows="2"
        :placeholder="__('Delivery location…')"
        class="mt-2"
      />
      <FieldRadioGroup
        v-model="freight"
        :label="__('Freight')"
        required
        inline
        :options="freightOptions"
        class="mt-3"
      />
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="
            customerExists
              ? __('Proceed to Quotation')
              : __('Create Customer & Proceed')
          "
          @click="show = false"
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
import FieldGrid from '@/components/StageForms/FieldGrid.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import FieldCheckbox from '@/components/StageForms/FieldCheckbox.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import { Button } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  org: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  customerExists: { type: Boolean, default: false },
})

const show = defineModel({ type: Boolean })

const legalName = ref('')
const gst = ref('')
const billing = ref('')
const sameAsBilling = ref(true)
const shipping = ref('')
const freight = ref('To Pay')

const freightOptions = [
  { label: __('To Pay (customer pays carrier)'), value: 'To Pay' },
  { label: __('Charged (added to invoice)'), value: 'Charged' },
  { label: __('Paid upfront'), value: 'Paid Upfront' },
]
</script>
