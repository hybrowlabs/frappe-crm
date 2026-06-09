<template>
  <StageFormDialog
    v-model="show"
    :title="__('Create Service Ticket')"
    :subtitle="customer"
    size="xl"
  >
    <StageCallout theme="blue" icon="headphones" class="mb-3.5">
      {{ __('Routes to the Service module. Engineer is auto-assigned by') }}
      <b>{{ __('Skill × Region × Workload') }}</b>;
      {{ __('SLA clock starts on creation.') }}
    </StageCallout>

    <FieldGrid :cols="2">
      <FieldText :label="__('Customer')" :modelValue="customer" readonly />
      <FieldSelect
        v-model="issueType"
        :label="__('Issue Type')"
        required
        :options="issueTypeOptions"
      />
      <FieldSelect
        v-model="category"
        :label="__('Category')"
        required
        :options="categoryOptions"
      />
      <FieldSelect
        v-model="priority"
        :label="__('Priority')"
        required
        :options="priorityOptions"
      />
      <FieldSelect
        v-model="source"
        :label="__('Source')"
        :options="sourceOptions"
      />
      <FieldSelect
        v-model="amc"
        :label="__('AMC Status')"
        :options="amcOptions"
      />
    </FieldGrid>
    <FieldTextarea
      v-model="description"
      :label="__('Issue Description')"
      required
      :rows="3"
    />
    <FieldStatic :label="__('Auto-assigned Engineer')">
      {{ engineer }} · {{ category }}
    </FieldStatic>
    <FieldStatic :label="__('Chargeable')" :bordered="false">
      <Badge
        :label="amc === 'Under AMC' ? __('Non-Chargeable') : __('Chargeable')"
        :theme="amc === 'Under AMC' ? 'green' : 'orange'"
        variant="subtle"
      />
    </FieldStatic>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create Ticket')"
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
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import FieldGrid from '@/components/StageForms/FieldGrid.vue'
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import { Button, Badge } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  customer: { type: String, default: '' },
  dealId: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })

const issueType = ref('Product Complaint')
const category = ref('Alloys')
const priority = ref('High')
const source = ref('Internal')
const amc = ref('Under AMC')
const description = ref(
  props.dealId
    ? `Follow-up from ${props.dealId} — retrial / quality check required.`
    : '',
)

const issueTypeOptions = [
  'Product Complaint',
  'Retrial',
  'Machine — Hardware',
  'Machine — Process',
  'AMC Visit',
  'Spare Parts Request',
]
const categoryOptions = ['Alloys', 'Plating', 'Machines']
const priorityOptions = ['Critical', 'High', 'Medium', 'Low']
const sourceOptions = ['Internal', 'WhatsApp', 'Phone', 'Email', 'Portal']
const amcOptions = ['Under AMC', 'Out of AMC']

const ENGINEER = { Alloys: 'Suraj', Plating: 'Akshay', Machines: 'Manoj Team' }
const engineer = computed(() => ENGINEER[category.value] || 'Suraj')
</script>
