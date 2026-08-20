<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="amber" icon="mail" class="mb-3">
      {{
        __(
          'The technical team needs a few more details before recommending a product. Answer below and the deal goes straight back to Tech Assignment.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Questions from the Technical Team')" icon="beaker">
      <FieldGrid :cols="1">
        <FieldStatic :label="__('Asked by')" :value="askedBy" />
      </FieldGrid>
      <div
        class="mt-2 whitespace-pre-line rounded-lg bg-surface-gray-2 px-3.5 py-2.5 text-p-sm text-ink-gray-7"
      >
        {{ deal.info_questions || __('No questions were recorded.') }}
      </div>
    </StageSection>

    <StageSection :title="__('Your Answer')" icon="fileText">
      <FieldTextarea
        v-model="answer"
        :label="__('Answer for the technical team')"
        :rows="4"
        required
        :placeholder="__('Reply with the details the tech team asked for')"
        :error="attempted && !answer.trim() ? __('An answer is required') : ''"
      />
    </StageSection>

    <template #actions>
      <div class="flex w-full items-center gap-2">
        <span class="flex-1" />
        <Button
          variant="solid"
          :label="__('Send Answer')"
          :loading="working"
          @click="sendAnswer"
        >
          <template #suffix><StageIcon name="mail" class="h-4 w-4" /></template>
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

const answer = ref('')
const attempted = ref(false)
const working = ref(false)

const askedBy = computed(() => {
  const d = props.deal || {}
  return d.assigned_tech_member || d.technical_person || '—'
})

async function sendAnswer() {
  attempted.value = true
  if (!answer.value.trim()) {
    toast.error(__('Please enter your answer for the technical team'))
    return
  }
  working.value = true
  try {
    await call('crm.api.tech_team.answer_info_request', {
      deal: props.deal?.name,
      answer: answer.value,
    })
    toast.success(__('Answer sent — deal is back with the technical team'))
    emit('done')
    show.value = false
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error sending the answer'))
  } finally {
    working.value = false
  }
}
</script>
