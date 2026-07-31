<template>
  <Dialog v-model="show" :options="{ title: dialogTitle, size }">
    <template #body-content>
      <div v-if="subtitle" class="-mt-2 mb-4 text-base text-ink-gray-5">
        {{ subtitle }}
      </div>

      <!-- multi-step progress header -->
      <div v-if="isMultiStep" class="mb-5 flex items-center gap-2">
        <template v-for="(s, i) in steps" :key="i">
          <div
            class="flex items-center gap-2"
            :class="i <= current ? 'opacity-100' : 'opacity-60'"
          >
            <span
              class="flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold"
              :class="
                i < current
                  ? 'bg-surface-green-3 text-ink-white'
                  : i === current
                    ? 'bg-surface-gray-7 text-ink-white'
                    : 'bg-surface-gray-3 text-ink-gray-6'
              "
            >
              <StageIcon v-if="i < current" name="check" :size="13" />
              <template v-else>{{ i + 1 }}</template>
            </span>
            <span
              class="whitespace-nowrap text-[13px]"
              :class="
                i === current
                  ? 'font-semibold text-ink-gray-9'
                  : 'font-medium text-ink-gray-7'
              "
            >
              {{ s.label }}
            </span>
          </div>
          <div
            v-if="i < steps.length - 1"
            class="h-0.5 min-w-[24px] flex-1 bg-surface-gray-3"
          />
        </template>
      </div>

      <slot :step="current" />
    </template>
    <template v-if="$slots.actions" #actions>
      <slot
        name="actions"
        :step="current"
        :next="next"
        :back="back"
        :isFirst="current === 0"
        :isLast="isLast"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'
import StageIcon from './StageIcon.vue'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  // The deal status label, e.g. "Req. Discussion" → title "Req. Discussion — stage form".
  statusLabel: { type: String, default: '' },
  // Explicit title; when set it overrides the "<statusLabel> — stage form" pattern.
  title: { type: String, default: '' },
  // Secondary line under the title, e.g. "Mehta Jewellers · CRM-DEAL-2026-0034".
  subtitle: { type: String, default: '' },
  // frappe-ui Dialog size token (xs … 7xl). 3xl ≈ 760px (prototype width).
  size: { type: String, default: '3xl' },
  // Optional wizard steps: [{ label }]. When 2+ entries, the dialog renders a
  // step header and exposes `step`/`next`/`back` slot props. Empty → single-step.
  steps: { type: Array, default: () => [] },
  // Step to open on. Lets a restored draft reopen the wizard where it was left,
  // instead of always returning to the first step.
  initialStep: { type: Number, default: 0 },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['update:step'])

const current = ref(props.initialStep)
const isMultiStep = computed(() => props.steps.length > 1)
const isLast = computed(() => current.value >= props.steps.length - 1)

// restart the wizard each time the dialog opens
watch(show, (open) => {
  if (open) current.value = props.initialStep
})

// keep the parent in sync so the current step can be cached with the draft
watch(current, (step) => emit('update:step', step), { immediate: true })

function next() {
  if (current.value < props.steps.length - 1) current.value++
}
function back() {
  if (current.value > 0) current.value--
}

const dialogTitle = computed(
  () => props.title || `${props.statusLabel} — ${__('stage form')}`,
)
</script>
