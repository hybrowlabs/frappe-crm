<template>
  <div class="flex flex-col gap-4 py-4">
    <!-- KPI tiles -->
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
      <div
        v-for="tile in tiles"
        :key="tile.label"
        class="rounded-lg border border-outline-gray-1 p-3"
      >
        <div class="text-xs text-ink-gray-5">{{ tile.label }}</div>
        <div class="mt-1 text-xl font-semibold text-ink-gray-9">
          {{ tile.value }}
        </div>
        <div class="text-xs text-ink-gray-4">{{ tile.sub }}</div>
      </div>
    </div>

    <!-- Trade Volume week on week -->
    <div class="rounded-lg border border-outline-gray-1 p-4">
      <div class="mb-2 flex items-center justify-between">
        <div class="text-sm font-medium text-ink-gray-8">
          {{ __('Trade Volume — Week on Week') }}
        </div>
        <div class="text-xs text-ink-gray-4">
          {{ kpis.uom }} · {{ __('last 12 weeks') }}
        </div>
      </div>
      <svg
        v-if="chart"
        :viewBox="`0 0 ${chart.w} ${chart.h}`"
        class="h-56 w-full"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="tvfill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.35" />
            <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
          </linearGradient>
        </defs>
        <path :d="chart.area" fill="url(#tvfill)" />
        <path
          :d="chart.line"
          fill="none"
          stroke="#3b82f6"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
        />
        <circle
          v-for="(p, i) in chart.pts"
          :key="i"
          :cx="p[0]"
          :cy="p[1]"
          r="3"
          fill="#fff"
          stroke="#3b82f6"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
        />
      </svg>
      <div v-if="chart" class="mt-1 flex justify-between text-[10px] text-ink-gray-4">
        <span v-for="(l, i) in chart.labels" :key="i">{{ l }}</span>
      </div>
      <div v-else class="py-10 text-center text-sm text-ink-gray-4">
        {{ __('No order data') }}
      </div>
    </div>

    <!-- Top items + Spend by category -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div class="rounded-lg border border-outline-gray-1 p-4">
        <div class="mb-3 flex items-center justify-between">
          <div class="text-sm font-medium text-ink-gray-8">
            {{ __('Top Items Purchased') }}
          </div>
          <div class="text-xs text-ink-gray-4">{{ __('by value') }}</div>
        </div>
        <div class="flex flex-col gap-3">
          <div v-for="(it, i) in analytics.data?.top_items || []" :key="i">
            <div class="flex items-center justify-between text-sm">
              <span class="truncate text-ink-gray-7">{{ it.item }}</span>
              <span class="whitespace-nowrap text-ink-gray-5">
                {{ fmtCurrency(it.value) }} · {{ fmtNum(it.qty) }} {{ it.uom }}
              </span>
            </div>
            <div class="mt-1 h-1.5 rounded bg-surface-gray-2">
              <div
                class="h-1.5 rounded"
                :style="{
                  width: barWidth(it.value) + '%',
                  background: color(i),
                }"
              />
            </div>
          </div>
          <div
            v-if="!(analytics.data?.top_items || []).length"
            class="py-6 text-center text-sm text-ink-gray-4"
          >
            {{ __('No items') }}
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-outline-gray-1 p-4">
        <div class="mb-3 text-sm font-medium text-ink-gray-8">
          {{ __('Spend by Category') }}
        </div>
        <div class="flex h-3 w-full overflow-hidden rounded">
          <div
            v-for="(c, i) in analytics.data?.spend_by_category || []"
            :key="i"
            :style="{ width: c.pct + '%', background: color(i) }"
          />
        </div>
        <div class="mt-3 flex flex-col gap-2">
          <div
            v-for="(c, i) in analytics.data?.spend_by_category || []"
            :key="i"
            class="flex items-center justify-between text-sm"
          >
            <span class="flex items-center gap-2 text-ink-gray-7">
              <span
                class="h-2.5 w-2.5 rounded-sm"
                :style="{ background: color(i) }"
              />
              {{ c.category }}
            </span>
            <span class="text-ink-gray-5">
              {{ c.pct }}% · {{ fmtCurrency(c.value) }}
            </span>
          </div>
        </div>
        <div class="mt-3 border-t border-outline-gray-1 pt-3 text-sm">
          <div class="flex justify-between">
            <span class="text-ink-gray-5">{{ __('Last Order') }}</span>
            <span class="text-ink-gray-8">
              {{ analytics.data?.last_order ? formatDate(analytics.data.last_order) : '—' }}
            </span>
          </div>
          <div class="mt-1 flex justify-between">
            <span class="text-ink-gray-5">{{ __('Credit Terms') }}</span>
            <span class="text-ink-gray-8">
              {{ analytics.data?.credit_terms || '—' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatDate } from '@/utils'
import { createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  organization: { type: String, required: true },
})

const analytics = createResource({
  url: 'crm.api.organization.get_analytics',
  params: { organization: props.organization },
  auto: true,
})

const kpis = computed(() => analytics.data?.kpis || {})

const palette = ['#3b82f6', '#a855f7', '#f59e0b', '#10b981', '#ef4444', '#06b6d4']
const color = (i) => palette[i % palette.length]

function fmtCurrency(v) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(v || 0)
}

function fmtNum(v) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(
    v || 0,
  )
}

const tiles = computed(() => {
  const k = kpis.value
  const sign = (k.wow || 0) > 0 ? '+' : ''
  return [
    { label: __('Total Purchases'), value: fmtCurrency(k.total_purchases), sub: __('lifetime') },
    { label: __('Total Quantity'), value: `${fmtNum(k.total_qty)} ${k.uom || ''}`, sub: __('across items') },
    { label: __('Avg Weekly Volume'), value: `${fmtNum(k.avg_weekly)} ${k.uom || ''}`, sub: __('last 12 weeks') },
    { label: __('Week-on-Week'), value: `${sign}${fmtNum(k.wow)}%`, sub: __('vs last week') },
    { label: __('Repeat Revenue'), value: `${fmtNum(k.repeat_revenue)}%`, sub: __('of account revenue') },
    { label: __('Health Score'), value: `${k.health_score || 0}`, sub: __('out of 10') },
  ]
})

function barWidth(value) {
  const max = Math.max(...(analytics.data?.top_items || []).map((i) => i.value), 1)
  return Math.round((value / max) * 100)
}

const chart = computed(() => {
  const data = analytics.data?.weekly_volume || []
  if (!data.length) return null
  const w = 900
  const h = 240
  const pad = 16
  const max = Math.max(...data, 1)
  const stepX = (w - pad * 2) / (data.length - 1 || 1)
  const pts = data.map((v, i) => [
    pad + i * stepX,
    h - pad - (v / max) * (h - pad * 2),
  ])
  const line = pts
    .map((p, i) => `${i ? 'L' : 'M'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`)
    .join(' ')
  const area = `${line} L ${pts[pts.length - 1][0].toFixed(1)} ${h - pad} L ${pts[0][0].toFixed(1)} ${h - pad} Z`
  return { w, h, pts, line, area, labels: data.map((_, i) => 'W' + (i + 1)) }
})
</script>
