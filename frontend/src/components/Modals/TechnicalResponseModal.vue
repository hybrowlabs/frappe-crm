<template>
  <StageFormDialog v-model="show" :statusLabel="statusLabel" :subtitle="subtitle">
    <StageCallout theme="amber" icon="clock" class="mb-3">
      {{
        __(
          'Technical team response. The waiting-time clock is running until you recommend a product, request more info, or mark the enquiry not suitable.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Assignment')" icon="checkSquare">
      <FieldGrid :cols="2">
        <FieldStatic :label="__('Assigned to')" :value="assignedTo" />
        <FieldStatic :label="__('Product context')" :value="productSummary || '—'" />
      </FieldGrid>
    </StageSection>

    <StageSection
      :title="__('Decision Point — Technical team response?')"
      icon="flag"
    >
      <div class="grid gap-2">
        <button
          v-for="o in respOptions"
          :key="o.key"
          type="button"
          class="flex items-start gap-3 rounded-lg border px-3.5 py-3 text-left transition-colors"
          :class="
            response === o.key
              ? 'border-outline-gray-3 bg-surface-gray-2'
              : 'border-outline-gray-2 bg-surface-white hover:bg-surface-gray-1'
          "
          @click="response = o.key"
        >
          <span
            class="grid h-7 w-7 flex-shrink-0 place-items-center rounded"
            :class="o.badgeClass"
          >
            <StageIcon :name="o.icon" class="h-4 w-4" />
          </span>
          <span class="flex-1">
            <span class="block text-base font-medium text-ink-gray-8">
              {{ o.title }}
            </span>
            <span class="mt-0.5 block text-p-sm text-ink-gray-5">
              {{ o.desc }}
            </span>
          </span>
          <StageIcon
            v-if="response === o.key"
            name="check"
            class="mt-1 h-4 w-4 flex-shrink-0 text-ink-gray-7"
          />
        </button>
      </div>
      <div v-if="errors.response" class="mt-1.5 text-xs text-ink-red-3">
        {{ errors.response }}
      </div>
    </StageSection>

    <!-- Recommend & Approve -->
    <StageSection
      v-if="response === 'recommend'"
      :title="__('Product Suggestions')"
      icon="beaker"
    >
      <div class="overflow-hidden rounded border border-outline-gray-2">
        <div
          class="grid grid-cols-[minmax(0,1fr)_120px_36px] items-center gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2 text-xs font-medium text-ink-gray-5"
        >
          <div>
            {{ __('Item') }}
            <span class="text-ink-red-3">*</span>
          </div>
          <div>
            {{ __('Quantity') }}
            <span class="text-ink-red-3">*</span>
          </div>
          <div />
        </div>
        <div
          v-for="(suggestion, index) in productSuggestions"
          :key="suggestion.key"
          class="grid grid-cols-[minmax(0,1fr)_120px_36px] items-center gap-2 border-b border-outline-gray-1 px-3 py-2 last:border-b-0"
        >
          <Link
            class="form-control"
            :value="suggestion.item"
            doctype="Item"
            :placeholder="__('Select item')"
            @change="(v) => (suggestion.item = v)"
          />
          <input
            v-model.number="suggestion.quantity"
            min="0.000001"
            step="any"
            type="number"
            class="form-input h-8 rounded border border-outline-gray-2 bg-surface-white px-2 text-base text-ink-gray-8 focus:border-outline-gray-4 focus:outline-none"
          />
          <Button
            :tooltip="__('Remove')"
            icon="trash-2"
            :disabled="productSuggestions.length === 1"
            @click="removeSuggestion(index)"
          />
        </div>
      </div>
      <div v-if="errors.productSuggestions" class="mt-1 text-xs text-ink-red-3">
        {{ errors.productSuggestions }}
      </div>
      <div v-else-if="productSummary" class="mt-1 text-xs text-ink-gray-4">
        {{ __('For {0}', [productSummary]) }}
      </div>
      <Button class="mt-2" :label="__('Add Product')" iconLeft="plus" @click="addSuggestion" />
      <FieldTextarea
        v-model="appNotes"
        :label="__('Application Notes')"
        required
        :rows="2"
        :placeholder="
          __('e.g. Casting temp 950°C, degassing recommended, expected yield 97%+')
        "
        :error="errors.appNotes"
      />
      <StageCallout theme="green" icon="arrowRight" class="mt-1">
        <template v-if="trialRequired">
          <b>{{ __('Recommend & Approve.') }}</b>
          {{ __('Product code confirmed → deal proceeds to Technical Evaluation (Trial).') }}
        </template>
        <template v-else>
          <b>{{ __('Product confirmed — no trial.') }}</b>
          {{ __('Recommendation approved → deal proceeds straight to the quotation flow.') }}
        </template>
      </StageCallout>
    </StageSection>

    <!-- Request More Info -->
    <StageSection
      v-if="response === 'info'"
      :title="__('Request More Info')"
      icon="mail"
    >
      <FieldTextarea
        v-model="questions"
        :label="__('Questions for salesperson')"
        required
        :rows="3"
        :placeholder="
          __('e.g. Confirm current alloy ratio; share sample casting photos; expected monthly volume?')
        "
        :error="errors.questions"
      />
      <StageCallout theme="amber" icon="mail" class="mt-1">
        {{
          __(
            'Questions are emailed to the salesperson. The waiting-time clock pauses until they reply — the deal stays in this stage.',
          )
        }}
      </StageCallout>
    </StageSection>

    <!-- Not Suitable -->
    <StageSection
      v-if="response === 'unsuitable'"
      :title="__('Not Suitable — escalate to Sales Manager')"
      icon="alert"
    >
      <FieldSelect
        v-model="unsuitReason"
        :label="__('Reason')"
        required
        :options="unsuitReasonOptions"
        :placeholder="__('Select a reason')"
        :error="errors.unsuitReason"
      />
      <FieldTextarea
        v-model="unsuitNotes"
        :label="__('Comments for Sales Manager')"
        required
        :rows="2"
        :placeholder="__('Explain why unsuitable and suggest alternative / redirection.')"
        :error="errors.unsuitNotes"
      />
      <StageCallout theme="red" icon="alert" class="mt-1">
        {{
          __(
            'On confirm, the deal is flagged for the Sales Manager (the salesperson\'s manager) with these comments, and stays in this stage for their review.',
          )
        }}
      </StageCallout>
    </StageSection>

    <template #actions>
      <div class="flex w-full items-center gap-2">
        <Button :label="__('Save Draft')" @click="saveDraft" />
        <span class="flex-1" />
        <Button
          v-if="response === 'recommend'"
          variant="solid"
          :label="trialRequired ? __('Approve → Trial') : __('Approve → Quotation')"
          @click="recommendAndApprove"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else-if="response === 'info'"
          variant="solid"
          :label="__('Send questions → pause clock')"
          :loading="sending"
          @click="sendQuestions"
        >
          <template #suffix><StageIcon name="mail" class="h-4 w-4" /></template>
        </Button>
        <Button
          v-else-if="response === 'unsuitable'"
          variant="solid"
          theme="red"
          :label="__('Mark Not Suitable → notify Sales Manager')"
          :loading="escalating"
          @click="markNotSuitable"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
        <Button v-else variant="solid" disabled :label="__('Select a response above')" />
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
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldTextarea from '@/components/StageForms/FieldTextarea.vue'
import FieldStatic from '@/components/StageForms/FieldStatic.vue'
import Link from '@/components/Controls/Link.vue'
import { Button, call, toast } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  statusLabel: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  deal: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['save', 'done'])

const response = ref(null) // null | 'recommend' | 'info' | 'unsuitable'
let suggestionKey = 0
const productSuggestions = ref([newSuggestion()])
const appNotes = ref('')
const questions = ref('')
const unsuitReason = ref('')
const unsuitNotes = ref('')
const sending = ref(false)
const escalating = ref(false)

const trialRequired = computed(() => props.deal?.trial_required !== 0)

const respOptions = [
  {
    key: 'recommend',
    icon: 'check',
    title: __('Recommend & Approve'),
    desc: __('Confirm product code + application notes → proceed to Trial or Quotation'),
    badgeClass: 'bg-surface-green-2 text-ink-green-3',
  },
  {
    key: 'info',
    icon: 'mail',
    title: __('Request More Info'),
    desc: __('Email specific questions to the salesperson → waiting-time pauses until they respond'),
    badgeClass: 'bg-surface-amber-2 text-ink-amber-3',
  },
  {
    key: 'unsuitable',
    icon: 'alert',
    title: __('Not Suitable'),
    desc: __('Sales Manager notified → deal reviewed for closure or alternative product'),
    badgeClass: 'bg-surface-red-2 text-ink-red-3',
  },
]

const unsuitReasonOptions = [
  'No matching product for required spec',
  'Spec outside our range',
  'Volume too low to serve',
  'Better served by alternative product',
  'Technically not feasible',
]

const assignedTo = computed(() => {
  const d = props.deal || {}
  return d.technical_person || d.assigned_tech_member || '—'
})

const productSummary = computed(() => {
  const d = props.deal || {}
  return [d.product_category, d.product_sub_category, d.product_variant]
    .filter(Boolean)
    .join(' → ')
})

function newSuggestion(row = {}) {
  return {
    key: row.name || `suggestion-${suggestionKey++}`,
    item: row.item || '',
    quantity: row.quantity ?? null,
  }
}

function addSuggestion() {
  productSuggestions.value.push(newSuggestion())
}

function removeSuggestion(index) {
  if (productSuggestions.value.length === 1) return
  productSuggestions.value.splice(index, 1)
}

function cleanSuggestions() {
  return productSuggestions.value
    .filter((row) => row.item || row.quantity)
    .map((row) => ({
      item: row.item || null,
      quantity: row.quantity || 0,
    }))
}

onMounted(() => {
  const d = props.deal || {}
  productSuggestions.value = (d.product_suggestions || []).length
    ? d.product_suggestions.map((row) => newSuggestion(row))
    : [newSuggestion()]
  appNotes.value = d.application_notes || ''
  questions.value = d.info_questions || ''
  unsuitReason.value = d.not_suitable_reason || ''
  unsuitNotes.value = d.not_suitable_notes || ''
  const map = {
    'Recommend & Approve': 'recommend',
    'Request More Info': 'info',
    'Not Suitable': 'unsuitable',
  }
  response.value = map[d.technical_response] || null
})

// validation — errors surface only after an attempt, then clear live
const attempted = ref(false)
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  if (!response.value) e.response = __('Select a response')
  if (response.value === 'recommend') {
    const suggestions = cleanSuggestions()
    if (!suggestions.length) e.productSuggestions = __('Add at least one product suggestion')
    else if (suggestions.some((row) => !row.item || !row.quantity))
      e.productSuggestions = __('Each suggestion needs an item and quantity')
    if (!appNotes.value) e.appNotes = __('Required')
  } else if (response.value === 'info') {
    if (!questions.value) e.questions = __('Required')
  } else if (response.value === 'unsuitable') {
    if (!unsuitReason.value) e.unsuitReason = __('Required')
    if (!unsuitNotes.value) e.unsuitNotes = __('Required')
  }
  return e
})

function recommendValues() {
  return {
    technical_response: 'Recommend & Approve',
    product_suggestions: cleanSuggestions(),
    application_notes: appNotes.value || '',
  }
}

function saveDraft() {
  // Persist whatever is filled without advancing the stage.
  const values = { technical_response: null }
  if (response.value === 'recommend') Object.assign(values, recommendValues())
  else if (response.value === 'info')
    Object.assign(values, {
      technical_response: 'Request More Info',
      info_questions: questions.value || '',
    })
  else if (response.value === 'unsuitable')
    Object.assign(values, {
      not_suitable_reason: unsuitReason.value || null,
      not_suitable_notes: unsuitNotes.value || '',
    })
  emit('save', { values, advance: false })
  show.value = false
}

function recommendAndApprove() {
  attempted.value = true
  if (errors.value.productSuggestions || errors.value.appNotes) {
    toast.error(__('Please add product suggestions and application notes.'))
    return
  }
  // Trial required → Technical Evaluation (Demo/Making). No trial → skip the
  // trial/retrial stages straight to Evaluation Completed (the quotation flow).
  // Emit the explicit target so the advance never depends on the cached status order.
  emit('save', {
    values: recommendValues(),
    advance: true,
    status: trialRequired.value ? 'Demo/Making' : 'Evaluation Completed',
  })
  show.value = false
}

async function sendQuestions() {
  attempted.value = true
  if (!questions.value) {
    toast.error(__('Please enter the questions for the salesperson.'))
    return
  }
  sending.value = true
  try {
    await call('crm.api.tech_team.request_more_info', {
      deal: props.deal?.name,
      questions: questions.value,
    })
    toast.success(__('Questions sent to the salesperson — clock paused'))
    emit('done')
    show.value = false
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error sending questions'))
  } finally {
    sending.value = false
  }
}

async function markNotSuitable() {
  attempted.value = true
  if (!unsuitReason.value || !unsuitNotes.value) {
    toast.error(__('Please select a reason and add comments.'))
    return
  }
  escalating.value = true
  try {
    await call('crm.api.tech_team.flag_not_suitable', {
      deal: props.deal?.name,
      reason: unsuitReason.value,
      notes: unsuitNotes.value,
    })
    toast.success(__('Marked Not Suitable — Sales Manager notified'))
    emit('done')
    show.value = false
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error escalating deal'))
  } finally {
    escalating.value = false
  }
}
</script>
