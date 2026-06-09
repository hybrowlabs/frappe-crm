<template>
  <StageFormDialog
    v-model="show"
    :statusLabel="statusLabel"
    :subtitle="subtitle"
    size="2xl"
  >
    <StageCallout theme="red">
      <template #icon><XIcon /></template>
      {{
        __(
          'This deal is marked Lost. Reopen by changing Status in the panel.',
        )
      }}
    </StageCallout>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import XIcon from '@/components/StageForms/icons/XIcon.vue'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
</script>
