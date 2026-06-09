<template>
  <StageFormDialog
    v-model="show"
    :title="__('Create Lab Request')"
    :subtitle="customer"
    size="xl"
  >
    <StageCallout theme="blue" icon="beaker" class="mb-3.5">
      {{
        __(
          "Sent to the lab for analysis. Results attach back to this deal's evaluation.",
        )
      }}
    </StageCallout>

    <FieldGrid :cols="2">
      <FieldText v-model="sample" :label="__('Sample / Item')" required />
      <FieldSelect
        v-model="testType"
        :label="__('Test Type')"
        required
        :options="testTypeOptions"
      />
      <FieldSelect
        v-model="priority"
        :label="__('Priority')"
        :options="priorityOptions"
      />
      <FieldText :label="__('Turnaround')" modelValue="48 hours" readonly />
    </FieldGrid>
    <FieldTextarea
      v-model="notes"
      :label="__('Notes')"
      :rows="2"
      :placeholder="__('What to investigate…')"
    />

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create Request')"
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
import { Button } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  customer: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })

const sample = ref('')
const testType = ref('Composition (XRF)')
const priority = ref('High')
const notes = ref('')

const testTypeOptions = [
  'Composition (XRF)',
  'Hardness',
  'Porosity',
  'Colour Match',
  'Density',
  'Melting Point',
]
const priorityOptions = ['Critical', 'High', 'Medium', 'Low']
</script>
