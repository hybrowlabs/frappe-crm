<template>
  <div class="mb-5">
    <div class="mb-2 text-sm text-ink-gray-5">
      {{ __('What does the customer need?') }}
    </div>
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="rounded-lg border p-3 text-left"
        :class="
          flow === option.value
            ? 'border-outline-gray-4 bg-surface-gray-2'
            : 'border-outline-gray-1 hover:bg-surface-gray-1'
        "
        @click="flow = option.value"
      >
        <div class="flex items-center gap-2">
          <span
            class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-outline-gray-4"
          >
            <span
              v-if="flow === option.value"
              class="h-2 w-2 rounded-full bg-surface-gray-7"
            />
          </span>
          <span class="text-base font-medium text-ink-gray-9">
            {{ option.label }}
          </span>
        </div>
        <div class="mt-1 pl-6 text-sm text-ink-gray-5">
          {{ option.description }}
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
// "discussion" is today's flow (the deal starts at Req. Discussion).
// "ready" marks the deal direct_quotation: the Deal page opens Create Customer
// and moves it straight to Proposal/Quotation.
const flow = defineModel({ type: String, default: 'discussion' })

const options = [
  {
    value: 'discussion',
    label: __('Needs discussion / trial'),
    description: __(
      'We first understand their need, suggest a product, and may run a trial before the quotation.',
    ),
  },
  {
    value: 'ready',
    label: __('Ready to buy – send quotation now'),
    description: __(
      'Small or medium business that already knows what it wants. Go straight to the price quote.',
    ),
  },
]
</script>
