<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="amber" icon="clock" class="mb-3">
      <b>{{ __('Waiting on technical team.') }}</b>
      {{
        __(
          'A CRM Task was auto-routed to the regional tech team. Waiting-time clock is running. SLA: <2h Excellent · 4–8h Amber (Head notified) · 24–48h → Sales Mgr · >48h Critical → Vicky.',
        )
      }}
    </StageCallout>

    <StageCard
      :title="__('Assignment Task — TECH-ASSIGN-0234')"
      icon="checkSquare"
    >
      <template #header-right>
        <Badge :label="__('Awaiting Response')" theme="orange" variant="subtle" />
      </template>

      <FieldStatic :label="__('Assigned to')" value="Suraj (Alloys · Maharashtra)" />
      <FieldStatic :label="__('Elapsed')" value="1h 22m" />
      <FieldStatic :label="__('SLA Status')">
        <Badge :label="__('Excellent (<2h)')" theme="green" variant="subtle" />
      </FieldStatic>
      <FieldStatic
        :label="__('Response options')"
        value="Recommend & Approve · Request More Info · Not Suitable"
        :bordered="false"
      />

      <div class="mt-3.5 flex items-center gap-2">
        <Button :label="__('Open Tech Task')">
          <template #prefix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <span class="flex-1" />
        <Button
          variant="solid"
          :label="__('Simulate: Tech Recommended →')"
          @click="show = false"
        />
      </div>
    </StageCard>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageCard from '@/components/StageForms/StageCard.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import { Button, Badge } from 'frappe-ui'

defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
</script>
