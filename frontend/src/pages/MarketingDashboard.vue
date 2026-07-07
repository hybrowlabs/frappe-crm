<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Marketing'), route: { name: 'MarketingDashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Marketing Dashboard') }}</h1>
          <span class="flex items-center gap-1 text-xs text-ink-gray-5">
            <span class="h-2 w-2 rounded-full bg-surface-green-3"></span>{{ __('Live') }}
          </span>
        </div>
      </div>

      <template v-if="d">
        <!-- LEAD VOLUME -->
        <SectionLabel :label="__('Lead Volume')" />
        <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Tile :title="__('Leads Uploaded — MTD')" :value="String(d.lead_volume.uploaded_mtd)">
            <template #foot>
              <div class="mt-1 text-xs text-ink-gray-4">
                <span :class="d.lead_volume.uploaded_mtd >= d.lead_volume.prev_month ? 'font-semibold text-ink-green-3' : 'font-semibold text-ink-red-3'">
                  {{ d.lead_volume.uploaded_mtd >= d.lead_volume.prev_month ? '▲' : '▼' }} {{ deltaPct }}%
                </span>
                {{ __('vs {0} last mo.', [d.lead_volume.prev_month]) }}
              </div>
            </template>
          </Tile>
          <Tile :title="__('This Quarter')" :value="String(d.lead_volume.this_quarter)" :sub="__('leads uploaded')" />
          <Tile :title="__('This Year')" :value="String(d.lead_volume.this_year)" :sub="__('leads uploaded')" />
          <Tile :title="__('Not Yet Contacted')" :value="String(d.lead_volume.not_contacted_7d)" :sub="__('uploaded > 7 days ago')" tone="red" />
        </div>

        <div class="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Leads by Source')">
            <div v-if="sourceTotal" class="mb-3 flex h-3 w-full overflow-hidden rounded-full bg-surface-gray-2">
              <div v-for="s in d.by_source" :key="s.label" :style="`width: ${pct(s.count, sourceTotal)}%; background: ${s.color}`" :title="s.label"></div>
            </div>
            <div v-for="s in d.by_source" :key="s.label" class="mb-1 flex items-center justify-between text-sm">
              <span class="flex items-center gap-2 text-ink-gray-7"><span class="h-2.5 w-2.5 rounded-sm" :style="`background: ${s.color}`"></span>{{ s.label }}</span>
              <span class="font-medium text-ink-gray-8">{{ pct(s.count, sourceTotal) }}% · {{ s.count }}</span>
            </div>
            <Empty v-if="!d.by_source.length" :text="__('No leads')" />
          </Card>
          <Card>
            <template #title>
              <div class="flex items-center justify-between">
                <span>{{ __('Leads by Industry') }}</span>
                <span class="text-xs font-normal text-ink-gray-5">{{ __('sub-source proxy') }}</span>
              </div>
            </template>
            <BarRow v-for="s in d.by_industry" :key="s.label" :label="s.label" :value="String(s.count)"
              :ratio="ratio(s.count, maxIndustry)" color="blue" />
            <Empty v-if="!d.by_industry.length" :text="__('No industry data on leads')" />
          </Card>
        </div>

        <!-- CONVERSION -->
        <SectionLabel :label="__('Conversion')" />
        <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Tile :title="__('Converted to Deal — MTD')" :value="String(d.conversion.converted_mtd)" :sub="__('leads → deals')" tone="green" />
          <Tile :title="__('Lead Conversion Rate')" :value="`${d.conversion.conversion_rate}%`" :sub="__('converted / uploaded')" tone="green" />
          <Tile :title="__('Avg Days to Conversion')" :value="`${d.conversion.avg_days_to_conversion} d`" :sub="__('upload → converted')" />
          <Tile :title="__('Marketing Contribution')" :value="`${d.conversion.contribution_pct}%`" :sub="__('of open pipeline')" />
        </div>

        <div class="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Conversion by Salesperson')">
            <BarRow v-for="s in d.conversion.by_salesperson" :key="s.ae" :label="aeName(s.ae)"
              :value="__('{0} converted', [s.count])" :ratio="ratio(s.count, maxSalesperson)" color="green" />
            <Empty v-if="!d.conversion.by_salesperson.length" :text="__('No converted leads yet')" />
          </Card>
          <Card>
            <template #title>
              <div class="flex items-center justify-between">
                <span>{{ __('Conversion Rate by Source') }}</span>
                <span class="text-xs font-normal text-ink-gray-5">{{ __('which channel converts best') }}</span>
              </div>
            </template>
            <BarRow v-for="s in d.conversion.conv_by_source" :key="s.label" :label="s.label"
              :value="`${s.pct}%`" :ratio="s.pct / 100" color="purple" />
            <Empty v-if="!d.conversion.conv_by_source.length" :text="__('No source data')" />
          </Card>
        </div>

        <!-- BULK STATUS VIEW -->
        <SectionLabel :label="__('Bulk Status View')" />
        <Card class="mb-6">
          <template #title>
            <div class="flex items-center justify-between">
              <span>{{ __('All Leads — Status') }}</span>
              <button
                class="flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition"
                :class="staleOnly ? 'border-outline-red-2 bg-surface-red-1 text-ink-red-3' : 'border-outline-gray-2 text-ink-gray-6'"
                @click="staleOnly = !staleOnly">
                {{ __('Not updated 14+ days · {0}', [d.bulk.stale_count]) }}
              </button>
            </div>
          </template>
          <div class="overflow-x-auto">
            <table v-if="bulkRows.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Lead') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Company') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Source') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Industry') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('AE') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Status') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Days Since Upload') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Last Activity') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="l in bulkRows" :key="l.name"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goLead(l.name)">
                  <td class="py-1.5 font-medium text-ink-gray-8">{{ l.lead_name }}</td>
                  <td class="py-1.5 text-ink-gray-5">{{ l.company }}</td>
                  <td class="py-1.5 text-ink-gray-5">{{ l.source }}</td>
                  <td class="py-1.5 text-ink-gray-5">{{ l.industry }}</td>
                  <td class="py-1.5 text-ink-gray-6">{{ aeName(l.ae) }}</td>
                  <td class="py-1.5"><Badge :theme="l.contacted ? 'blue' : 'gray'" :label="l.status" variant="subtle" /></td>
                  <td class="py-1.5 text-right">
                    <Badge v-if="l.stale" theme="red" :label="`${l.days}d`" variant="subtle" />
                    <span v-else class="text-ink-gray-5">{{ l.days }}d</span>
                  </td>
                  <td class="py-1.5 text-right text-ink-gray-5">{{ __('{0}d ago', [l.last_activity_days]) }}</td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No leads match')" />
          </div>
        </Card>

        <!-- REPEAT CONTRIBUTION -->
        <SectionLabel :label="__('Repeat Contribution')" />
        <div v-if="!d.repeat.has_orders"
          class="mb-3 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-4 py-2.5 text-sm text-ink-amber-3">
          {{ __('Order data (ERPNext Sales Orders) is not available — revenue-based repeat metrics show as zero.') }}
        </div>
        <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Tile :title="__('Revenue — Marketing-Sourced Accounts')" :value="fmtINR(d.repeat.revenue_from_mktg)" :sub="__('lifetime order value')" tone="green" />
          <Tile :title="__('Now Repeat Buyers')" :value="`${d.repeat.now_repeat_buyers} / ${d.repeat.total_mktg_accounts}`" :sub="__('marketing accounts with >1 order')">
            <template #foot>
              <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-gray-2">
                <div class="h-full rounded-full bg-green-500" :style="`width: ${pct(d.repeat.now_repeat_buyers, d.repeat.total_mktg_accounts)}%`"></div>
              </div>
              <div class="mt-1 text-xs text-ink-gray-4">{{ __('{0}% became repeat buyers', [pct(d.repeat.now_repeat_buyers, d.repeat.total_mktg_accounts)]) }}</div>
            </template>
          </Tile>
          <Tile :title="__('Contribution % to Total Revenue')" :value="`${d.repeat.contribution_pct}%`" :sub="__('marketing-sourced / total')">
            <template #foot>
              <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-gray-2">
                <div class="h-full rounded-full bg-blue-500" :style="`width: ${d.repeat.contribution_pct}%`"></div>
              </div>
            </template>
          </Tile>
        </div>
      </template>

      <div v-else class="py-20 text-center text-sm text-ink-gray-4">{{ __('Loading…') }}</div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Badge, Breadcrumbs, createResource } from 'frappe-ui'
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usersStore } from '@/stores/users'

const router = useRouter()
const { getUser } = usersStore()

const goLead = (name) => name && router.push({ name: 'Lead', params: { leadId: name } })

function aeName(email) {
  if (!email || email === 'Unassigned') return __('Unassigned')
  return getUser(email).full_name || email
}

const dash = createResource({
  url: 'crm.api.marketing_dashboard.get_marketing_dashboard',
  auto: true,
})
const d = computed(() => dash.data)

const staleOnly = ref(false)
const bulkRows = computed(() => {
  const rows = d.value?.bulk.rows || []
  return staleOnly.value ? rows.filter((r) => r.stale) : rows
})
const sourceTotal = computed(() => (d.value?.by_source || []).reduce((s, x) => s + x.count, 0))
const maxIndustry = computed(() => Math.max(1, ...(d.value?.by_industry || []).map((s) => s.count)))
const maxSalesperson = computed(() => Math.max(1, ...(d.value?.conversion.by_salesperson || []).map((s) => s.count)))
const deltaPct = computed(() => {
  const v = d.value?.lead_volume
  if (!v || !v.prev_month) return 0
  return Math.abs(Math.round(((v.uploaded_mtd - v.prev_month) / v.prev_month) * 100))
})

function pct(v, total) {
  return total ? Math.round((v / total) * 100) : 0
}
function ratio(v, max) {
  return Math.max(0.02, (v || 0) / max)
}
function fmtINR(v) {
  const n = Math.abs(v || 0)
  if (n >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`
  if (n >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v || 0)
}

// ---- tiny presentational components ----
const SectionLabel = (props) =>
  h('div', { class: 'mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5' }, props.label)
SectionLabel.props = ['label']

const toneClass = { green: 'text-ink-green-3', red: 'text-ink-red-3', amber: 'text-ink-amber-3' }
const Tile = (props, { slots }) =>
  h('div', { class: 'rounded-lg border border-outline-gray-1 bg-surface-white p-4' }, [
    h('div', { class: 'mb-1 text-xs text-ink-gray-5' }, props.title),
    h('div', { class: `text-2xl font-semibold ${toneClass[props.tone] || 'text-ink-gray-9'}` }, props.value),
    props.sub ? h('div', { class: 'mt-0.5 text-xs text-ink-gray-4' }, props.sub) : null,
    slots.foot?.(),
  ])
Tile.props = ['title', 'value', 'sub', 'tone']

const Card = (props, { slots }) =>
  h('div', { class: 'rounded-lg border border-outline-gray-1 bg-surface-white p-4' }, [
    h('div', { class: 'mb-3 text-sm font-medium text-ink-gray-8' }, slots.title ? slots.title() : props.title),
    slots.default?.(),
  ])
Card.props = ['title']

const barColor = { blue: 'bg-blue-500', green: 'bg-green-500', amber: 'bg-amber-500', red: 'bg-red-500', purple: 'bg-purple-500' }
const Bar = (props) =>
  h('div', { class: 'h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2' }, [
    h('div', { class: `h-full rounded-full ${barColor[props.color] || barColor.blue}`, style: `width: ${Math.round(props.ratio * 100)}%` }),
  ])
Bar.props = ['ratio', 'color']

const BarRow = (props) =>
  h('div', { class: 'mb-2.5 last:mb-0' }, [
    h('div', { class: 'mb-1 flex items-center justify-between text-sm' }, [
      h('span', { class: 'truncate text-ink-gray-8' }, props.label),
      h('span', { class: 'ml-2 shrink-0 font-medium text-ink-gray-8' }, props.value),
    ]),
    h(Bar, { ratio: props.ratio, color: props.color }),
  ])
BarRow.props = ['label', 'value', 'ratio', 'color']

const Empty = (props) =>
  h('div', { class: 'py-6 text-center text-sm text-ink-gray-4' }, props.text || __('No data'))
Empty.props = ['text']
</script>
