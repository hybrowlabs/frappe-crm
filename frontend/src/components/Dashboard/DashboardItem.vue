<template>
  <div class="h-full w-full">
    <div
      v-if="item.type == 'number_chart'"
      class="pa-kpi h-full w-full cursor-pointer !items-center overflow-hidden"
    >
      <span
        class="pa-ico"
        :style="{ background: `var(--pa-t${(index % 4) + 1})`, color: index % 4 === 3 ? '#173c2a' : '#fff' }"
      >
        <component :is="numberIcon(item.data?.title)" />
      </span>
      <Tooltip :text="__(item.data.tooltip)">
        <NumberChart
          v-if="item.data"
          :key="index"
          class="pa-body !max-h-none !bg-transparent !p-0"
          :config="item.data"
        >
          <template #title>
            <span class="pa-l truncate">{{ item.data.title }}</span>
          </template>
          <template #subtitle="{ formatValue }">
            <div class="pa-v flex items-center gap-0.5 truncate">
              <div v-if="item.data.prefix" v-html="item.data.prefix" class="table" />
              {{ formatValue(item.data.value, 1, true) }}{{ item.data.suffix }}
            </div>
          </template>
        </NumberChart>
      </Tooltip>
    </div>
    <div
      v-else-if="item.type == 'spacer'"
      class="rounded h-full overflow-hidden text-ink-gray-5 flex items-center justify-center"
      :class="editing ? 'border border-dashed border-outline-gray-2' : ''"
    >
      {{ editing ? __('Spacer') : '' }}
    </div>
    <div
      v-else-if="item.type == 'axis_chart'"
      class="pa-chart-card h-full w-full overflow-hidden"
    >
      <AxisChart v-if="item.data" :config="item.data" />
    </div>
    <div
      v-else-if="item.type == 'donut_chart'"
      class="pa-chart-card h-full w-full overflow-hidden"
    >
      <DonutChart v-if="item.data" :config="item.data" />
    </div>
  </div>
</template>
<script setup>
import { AxisChart, DonutChart, NumberChart, Tooltip } from 'frappe-ui'
import LucideUsers from '~icons/lucide/users'
import LucideClock from '~icons/lucide/clock'
import LucideRocket from '~icons/lucide/rocket'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideIndianRupee from '~icons/lucide/indian-rupee'
import LucideCoins from '~icons/lucide/coins'
import LucideSparkles from '~icons/lucide/sparkles'

defineProps({
  index: { type: Number, required: true },
  item: { type: Object, required: true },
  editing: { type: Boolean, default: false },
})

// Icon tile for each number card, picked from the chart title (Total leads, Won deals, …).
function numberIcon(title = '') {
  const t = String(title).toLowerCase()
  if (t.includes('time')) return LucideClock
  if (t.includes('lead')) return LucideUsers
  if (t.includes('won') && t.includes('value')) return LucideIndianRupee
  if (t.includes('won')) return LucideCircleCheck
  if (t.includes('value')) return LucideCoins
  if (t.includes('ongoing') || t.includes('deal')) return LucideRocket
  return LucideSparkles
}
</script>
