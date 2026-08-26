<template>
  <div class="flex items-center overflow-hidden rounded border divide-x">
    <button
      v-for="(stage, i) in stages"
      :key="stage.name"
      class="flex items-center gap-1.5 whitespace-nowrap px-2.5 py-1.5 text-sm transition-colors"
      :class="
        stage.name === current
          ? 'bg-surface-gray-3 font-medium text-ink-gray-9'
          : i < currentIndex
            ? 'text-ink-gray-8 hover:bg-surface-gray-2'
            : 'text-ink-gray-5 hover:bg-surface-gray-2'
      "
      @click="$emit('change', stage.name)"
    >
      <FeatherIcon v-if="i < currentIndex" name="check" class="size-3" />
      <IndicatorIcon v-else :class="stage.color" />
      {{ label(stage.name) }}
    </button>
    <Dropdown v-if="exits.length" :options="exitOptions" placement="right">
      <button
        class="flex items-center gap-1.5 whitespace-nowrap px-2.5 py-1.5 text-sm"
        :class="
          currentExit
            ? 'bg-surface-gray-3 font-medium text-ink-gray-9'
            : 'text-ink-gray-5 hover:bg-surface-gray-2'
        "
      >
        <IndicatorIcon v-if="currentExit" :class="currentExit.color" />
        {{ currentExit ? label(currentExit.name) : __('More') }}
        <FeatherIcon name="chevron-down" class="size-3.5" />
      </button>
    </Dropdown>
  </div>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { isTranslatable } from '@/utils'
import { Dropdown, FeatherIcon } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  statuses: { type: Array, required: true },
  current: { type: String, required: true },
  statusDoctype: { type: String, default: 'CRM Lead Status' },
})

const emit = defineEmits(['change'])

const sorted = computed(() =>
  [...props.statuses].sort((a, b) => a.position - b.position),
)
const stages = computed(() => sorted.value.filter((s) => s.type !== 'Lost'))
const exits = computed(() => sorted.value.filter((s) => s.type === 'Lost'))

const currentIndex = computed(() =>
  stages.value.findIndex((s) => s.name === props.current),
)
const currentExit = computed(() =>
  exits.value.find((s) => s.name === props.current),
)

const exitOptions = computed(() =>
  exits.value.map((status) => ({
    label: label(status.name),
    icon: () => h(IndicatorIcon, { class: status.color }),
    onClick: () => emit('change', status.name),
  })),
)

function label(name) {
  return isTranslatable(props.statusDoctype) ? __(name) : name
}
</script>
