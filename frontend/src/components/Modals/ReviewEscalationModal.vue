<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="red" icon="alert" class="mb-3">
      {{
        __(
          'The technical team marked this enquiry Not Suitable. Review their reasoning, then redirect the deal for re-qualification or close it as Lost.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Technical Team Feedback')" icon="beaker">
      <FieldGrid :cols="2">
        <FieldStatic :label="__('Reason')" :value="deal.not_suitable_reason || '—'" />
        <FieldStatic :label="__('Raised by (Tech Person)')" :value="assignedTo" />
      </FieldGrid>
      <div class="mt-2 rounded-lg bg-surface-gray-2 px-3.5 py-2.5 text-p-sm text-ink-gray-7">
        {{ deal.not_suitable_notes || __('No additional comments.') }}
      </div>
    </StageSection>

    <StageSection :title="__('Decision Point — how to resolve?')" icon="flag">
      <div class="grid gap-2">
        <button
          v-for="o in decisionOptions"
          :key="o.key"
          type="button"
          class="flex items-start gap-3 rounded-lg border px-3.5 py-3 text-left transition-colors"
          :class="
            decision === o.key
              ? 'border-outline-gray-3 bg-surface-gray-2'
              : 'border-outline-gray-2 bg-surface-white hover:bg-surface-gray-1'
          "
          @click="decision = o.key"
        >
          <span
            class="grid h-7 w-7 flex-shrink-0 place-items-center rounded"
            :class="o.badgeClass"
          >
            <StageIcon :name="o.icon" class="h-4 w-4" />
          </span>
          <span class="flex-1">
            <span class="block text-base font-medium text-ink-gray-8">{{ o.title }}</span>
            <span class="mt-0.5 block text-p-sm text-ink-gray-5">{{ o.desc }}</span>
          </span>
          <StageIcon
            v-if="decision === o.key"
            name="check"
            class="mt-1 h-4 w-4 flex-shrink-0 text-ink-gray-7"
          />
        </button>
      </div>
    </StageSection>

    <StageSection
      v-if="decision"
      :title="__('Review Notes')"
      icon="fileText"
    >
      <FieldTextarea
        v-model="notes"
        :label="
          decision === 'redirect'
            ? __('What should the salesperson revisit?')
            : __('Reason for closing as Lost')
        "
        :rows="2"
        :placeholder="__('Add a note for the record (optional)')"
      />
    </StageSection>

    <template #actions>
      <div class="flex w-full items-center gap-2">
        <span class="flex-1" />
        <Button
          v-if="decision === 'redirect'"
          variant="solid"
          :label="__('Redirect → Req. Discussion')"
          :loading="working"
          @click="resolve('redirect')"
        >
          <template #suffix><StageIcon name="refresh" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else-if="decision === 'lost'"
          variant="solid"
          theme="red"
          :label="__('Mark Deal as Lost')"
          :loading="working"
          @click="resolve('lost')"
        >
          <template #suffix><StageIcon name="x" class="h-4 w-4" /></template>
        </Button>
        <Button v-else variant="solid" disabled :label="__('Choose an option above')" />
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
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import { Button, call, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['done'])

const decision = ref(null) // null | 'redirect' | 'lost'
const notes = ref('')
const working = ref(false)

const decisionOptions = [
  {
    key: 'redirect',
    icon: 'refresh',
    title: __('Redirect for Re-Qualification'),
    desc: __('Send the deal back to Req. Discussion so the salesperson can re-scope it'),
    badgeClass: 'bg-surface-blue-2 text-ink-blue-3',
  },
  {
    key: 'lost',
    icon: 'x',
    title: __('Close as Lost'),
    desc: __('No viable product or fit — close the deal'),
    badgeClass: 'bg-surface-red-2 text-ink-red-3',
  },
]

const assignedTo = computed(() => {
  const d = props.deal || {}
  return d.technical_person || d.assigned_tech_member || '—'
})

async function resolve(action) {
  working.value = true
  try {
    await call('crm.api.tech_team.resolve_escalation', {
      deal: props.deal?.name,
      action,
      notes: notes.value || undefined,
    })
    toast.success(
      action === 'redirect'
        ? __('Deal redirected to Req. Discussion')
        : __('Deal closed as Lost'),
    )
    emit('done')
    show.value = false
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error resolving escalation'))
  } finally {
    working.value = false
  }
}
</script>
