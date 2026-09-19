<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Dashboards'), route: { name: 'Dashboard' } }, { label: __('CEO Dashboard'), route: { name: 'CEODashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto pa-page">
      <div class="pa-page-h">
        <h1 class="pa-h1">{{ __('CEO Dashboard') }} <span class="pa-live">{{ __('Live') }}</span></h1>
        <div class="pa-seg" role="group" :aria-label="__('Period')">
          <button
            v-for="p in periods"
            :key="p.value"
            :class="{ on: period === p.value }"
            :aria-pressed="period === p.value"
            @click="period = p.value"
          >
            {{ __(p.label) }}
          </button>
        </div>
      </div>

      <template v-if="d">
        <!-- PIPELINE -->
        <SectionLabel :label="__('Pipeline')" />
        <div class="mb-3.5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-5">
          <Tile :icon="LucideFunnel" :title="__('Total Pipeline (Open)')" :value="fmtINR(d.pipeline.total_value)"
            :sub="__('{0} open deals', [d.pipeline.open_count])" @click="drillPipeline()" />
          <Tile :icon="LucideIndianRupee" :title="revenueLabel" :value="fmtINR(d.pipeline.revenue_booked)"
            :sub="__('booked this period')" />
          <Tile :icon="trendIcon(d.pipeline.revenue_booked, d.pipeline.revenue_prev)" :title="__('vs Last Period')"
            :value="pct(d.pipeline.revenue_booked, d.pipeline.revenue_prev)"
            :sub="__('{0} last period', [fmtINR(d.pipeline.revenue_prev)])"
            :tone="tone(d.pipeline.revenue_booked, d.pipeline.revenue_prev)" />
          <Tile :icon="trendIcon(d.pipeline.revenue_booked, d.pipeline.revenue_last_year)" :title="__('vs Last Year (same period)')"
            :value="pct(d.pipeline.revenue_booked, d.pipeline.revenue_last_year)"
            :sub="__('{0} last year', [fmtINR(d.pipeline.revenue_last_year)])"
            :tone="tone(d.pipeline.revenue_booked, d.pipeline.revenue_last_year)" />
          <Tile :icon="LucideBuilding" :title="__('New Accounts')" :value="String(d.pipeline.new_accounts)"
            :sub="__('created this period')" />
        </div>

        <div class="mb-8 grid grid-cols-1 gap-3.5 lg:grid-cols-3">
          <Card :title="__('Pipeline by Stage')">
            <Bars>
              <BarRow v-for="s in d.pipeline.by_stage" :key="s.stage" :label="s.stage"
                :sub="__('{0} deals', [s.count])" :value="fmtINR(s.value)"
                :ratio="ratio(s.value, maxStageValue)" @click="drillStage(s.stage)" />
            </Bars>
            <Empty v-if="!d.pipeline.by_stage.length" />
          </Card>
          <Card :title="__('Category-wise Pipeline')">
            <div v-if="d.pipeline.by_category.length" class="pa-stacked">
              <div v-for="(c, i) in d.pipeline.by_category" :key="c.category"
                class="cursor-pointer" :class="catColor(c.category, i)"
                :style="`width: ${c.pct}%`" :title="c.category" @click="drillCategory(c.category)"></div>
            </div>
            <div class="pa-legend">
              <div v-for="(c, i) in d.pipeline.by_category" :key="c.category"
                class="pa-legend-row cursor-pointer" @click="drillCategory(c.category)">
                <span class="flex items-center"><span class="pa-dot" :class="catColor(c.category, i)"></span>{{ c.category }}</span>
                <span><b>{{ c.pct }}%</b><em>· {{ fmtINR(c.value) }}</em></span>
              </div>
            </div>
            <Empty v-if="!d.pipeline.by_category.length" :icon="LucideLayers" :text="__('No product category on deals')" />
          </Card>
          <Card :title="__('Region-wise Pipeline')">
            <Bars>
              <BarRow v-for="r in d.pipeline.by_region" :key="r.region" :label="r.region"
                :value="fmtINR(r.value)" :ratio="ratio(r.value, maxRegionValue)" @click="drillRegion(r.region)" />
            </Bars>
            <Empty v-if="!d.pipeline.by_region.length" />
          </Card>
        </div>

        <!-- ACCOUNT HEALTH -->
        <SectionLabel :label="__('Account Health')" />
        <div class="mb-3.5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
          <Tile :icon="LucideMoon" :title="__('Dormant Accounts')" :value="String(d.account_health.dormant_count)"
            :sub="__('no order in 30+ days')" tone="amber" @click="drillDormant()" />
          <Tile :icon="LucideTriangleAlert" :title="__('Accounts at Risk')" :value="String(d.account_health.at_risk_count)"
            :sub="__('ordering less frequently')" tone="red" @click="drillAtRisk()" />
          <Tile :icon="LucideRepeat" :title="__('Repeat Business')" :value="`${d.account_health.repeat_pct}%`"
            :sub="__('of total order value')" tone="green" />
          <Tile :icon="LucideWallet" :title="__('YTD Revenue')" :value="fmtINR(d.account_health.ytd_revenue)"
            :sub="__('all accounts')" @click="drillAccounts()" />
        </div>

        <div class="mb-8 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
          <Card :title="__('Top 10 Accounts by Revenue (YTD)')">
            <Bars>
              <BarRow v-for="(a, i) in d.account_health.top_accounts" :key="a.organization"
                :rank="i + 1" :label="a.organization_name" :value="fmtINR(a.value)"
                :ratio="ratio(a.value, maxAccountValue)" color="green" @click="goOrg(a.organization)" />
            </Bars>
            <Empty v-if="!d.account_health.top_accounts.length" />
          </Card>
          <div class="flex flex-col gap-3.5">
            <Card :title="__('Dormant — No Order in 30 Days')">
              <table v-if="d.account_health.dormant.length" class="w-full text-sm">
                <thead>
                  <tr class="text-xs text-ink-gray-5">
                    <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Last Order') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('Days') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="o in d.account_health.dormant" :key="o.organization"
                    class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                    @click="goOrg(o.organization)">
                    <td class="py-1.5 text-ink-gray-8">{{ o.organization_name }}</td>
                    <td class="py-1.5 text-ink-gray-6">{{ formatDate(o.last_order) }}</td>
                    <td class="py-1.5 text-right font-medium text-ink-red-3">{{ o.days }}d</td>
                  </tr>
                </tbody>
              </table>
              <Empty v-else :icon="LucideCircleCheck" :text="__('No dormant accounts')" />
            </Card>
            <Card :title="__('At Risk — Ordering Less Often')">
              <template v-if="d.account_health.accounts_at_risk.length" #right>
                <span class="pa-count bad">{{ d.account_health.accounts_at_risk.length }}</span>
              </template>
              <table v-if="d.account_health.accounts_at_risk.length" class="w-full text-sm">
                <thead>
                  <tr class="text-xs text-ink-gray-5">
                    <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('Last Qtr') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('This Qtr') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Owner') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="a in d.account_health.accounts_at_risk" :key="a.organization"
                    class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                    @click="goOrg(a.organization)">
                    <td class="py-1.5 text-ink-gray-8">{{ a.organization_name }}</td>
                    <td class="py-1.5 text-right text-ink-gray-6">{{ a.last_qtr }}</td>
                    <td class="py-1.5 text-right font-medium"
                      :class="a.this_qtr < a.last_qtr ? 'text-ink-red-3' : 'text-ink-gray-8'">{{ a.this_qtr }}</td>
                    <td class="py-1.5 text-ink-gray-6">{{ a.owner || '—' }}</td>
                  </tr>
                </tbody>
              </table>
              <Empty v-else :icon="LucideCircleCheck" :text="__('No accounts flagged at risk')" />
            </Card>
          </div>
        </div>

        <!-- WAITING TIME -->
        <SectionLabel :label="__('Waiting Time')" />
        <div class="mb-8 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
          <Card :title="__('Avg Waiting Time by Stage')">
            <Bars>
              <BarRow v-for="w in d.waiting_time" :key="w.stage" :label="w.stage"
                :value="__('{0} d', [w.avg_days])"
                :ratio="ratio(w.avg_days, maxWaitDays)"
                :color="w.avg_days === maxWaitDays ? 'red' : 'amber'" />
            </Bars>
            <Empty v-if="!d.waiting_time.length" :icon="LucideClock" />
          </Card>
          <Card :title="__('Bottlenecks — Highest Waiting Time')">
            <table v-if="bottlenecks.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">#</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Stage') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Avg Wait') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(w, i) in bottlenecks" :key="w.stage" class="border-t border-outline-gray-1">
                  <td class="py-1.5"><span class="pa-rank" :class="{ r1: i === 0 }">{{ i + 1 }}</span></td>
                  <td class="py-1.5 text-ink-gray-8" :class="{ 'font-semibold': i === 0 }">{{ w.stage }}</td>
                  <td class="py-1.5 text-right font-medium text-ink-gray-8">{{ __('{0} d', [w.avg_days]) }}</td>
                  <td class="py-1.5 text-right">
                    <Badge :theme="waitTheme(w.avg_days)" :label="waitStatus(w.avg_days)" variant="subtle" />
                  </td>
                </tr>
              </tbody>
            </table>
            <Empty v-else />
          </Card>
        </div>

        <!-- PERFORMANCE -->
        <SectionLabel :label="__('Performance')" />
        <div class="mb-3.5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
          <Tile :icon="LucideTarget" :title="__('Trial Conversion Rate')" :value="`${d.performance.trial_conversion.rate}%`"
            :sub="__('{0} of {1} trials successful', [d.performance.trial_conversion.successful, d.performance.trial_conversion.total])"
            tone="green" />
          <Tile :icon="LucideClock" :title="__('Tech Avg Response')" :value="fmtDuration(d.performance.tech_response_seconds)"
            :sub="__('across {0} deals', [d.performance.tech_response_count])" />
          <Tile :icon="LucideMegaphone" :title="__('Marketing Contribution')" :value="`${d.pipeline.marketing_pct}%`"
            :sub="__('of pipeline from mktg leads')" />
          <Tile :icon="LucideWallet" :title="__('Overdue Payments')" :value="fmtINR(d.overdue_payments.amount)"
            :sub="__('{0} accounts', [d.overdue_payments.count])" tone="red" @click="drillOverdue()" />
        </div>
        <Card v-if="d.overdue_payments.accounts.length" :title="__('Overdue Payments — Accounts')"
          class="mb-4">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Customer') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Amount') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Days Overdue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in d.overdue_payments.accounts" :key="a.customer"
                class="border-t border-outline-gray-1">
                <td class="py-1.5 text-ink-gray-8">{{ a.customer }}</td>
                <td class="py-1.5 text-right text-ink-gray-8">{{ fmtINR(a.amount) }}</td>
                <td class="py-1.5 text-right font-medium text-ink-red-3">{{ a.days }}d</td>
              </tr>
            </tbody>
          </table>
        </Card>
      </template>

      <div v-else class="py-20 text-center text-sm text-ink-gray-4">{{ __('Loading…') }}</div>
    </div>

    <!-- drill-down drawer -->
    <div v-if="drill" class="fixed inset-0 z-40">
      <div class="absolute inset-0 bg-black/30" @click="closeDrill"></div>
      <div class="absolute right-0 top-0 flex h-full w-[min(460px,92vw)] flex-col bg-surface-white shadow-2xl">
        <div class="flex items-start gap-3 border-b border-outline-gray-2 px-4 py-3">
          <div class="min-w-0 flex-1">
            <div class="text-base font-semibold text-ink-gray-9">{{ drill.title }}</div>
            <div class="mt-0.5 text-xs text-ink-gray-5">{{ drill.subtitle }}</div>
          </div>
          <button class="text-lg leading-none text-ink-gray-5 hover:text-ink-gray-9" @click="closeDrill">&times;</button>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div v-for="(r, i) in drill.rows" :key="i"
            class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-2.5"
            :class="r.to ? 'cursor-pointer hover:bg-surface-gray-1' : ''"
            @click="r.to && drillGo(r.to)">
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-medium text-ink-gray-9">{{ r.primary }}</div>
              <div class="truncate text-xs text-ink-gray-5">{{ r.secondary }}</div>
            </div>
            <Badge v-if="r.badge" :theme="r.badgeTheme" :label="r.badge" variant="subtle" />
            <div v-if="r.value" class="whitespace-nowrap text-sm font-semibold text-ink-gray-8">{{ r.value }}</div>
            <span v-if="r.to" class="text-ink-gray-4">&rarr;</span>
          </div>
          <Empty v-if="!drill.rows.length" />
        </div>
        <div v-if="drill.footer" class="border-t border-outline-gray-2 p-3">
          <Button class="w-full" variant="solid" @click="openDealsFiltered(drill.footer.filters)">
            {{ drill.footer.label }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { SectionLabel, Tile, Card, BarRow, Bars, Empty } from '@/components/Dashboard/ui'
import LucideFunnel from '~icons/lucide/funnel'
import LucideIndianRupee from '~icons/lucide/indian-rupee'
import LucideTrendingUp from '~icons/lucide/trending-up'
import LucideTrendingDown from '~icons/lucide/trending-down'
import LucideBuilding from '~icons/lucide/building'
import LucideLayers from '~icons/lucide/layers'
import LucideMoon from '~icons/lucide/moon'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import LucideRepeat from '~icons/lucide/repeat'
import LucideWallet from '~icons/lucide/wallet'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideClock from '~icons/lucide/clock'
import LucideTarget from '~icons/lucide/target'
import LucideMegaphone from '~icons/lucide/megaphone'
import { formatDate } from '@/utils'
import { Badge, Breadcrumbs, Button, call, createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'

const router = useRouter()
const goOrg = (name) => name && router.push({ name: 'Organization', params: { organizationId: name } })

// Persist the drilled filters onto the user's standard CRM Deal list view, then open it.
// This overwrites the user's saved Deal-list filter each drill (expected behaviour).
async function openDealsFiltered(filters) {
  closeDrill()
  const session = sessionStore()
  const views = viewsStore()
  try {
    const existing = await call('frappe.client.get_list', {
      doctype: 'CRM View Settings',
      filters: { dt: 'CRM Deal', type: 'list', is_standard: 1, user: session.user },
      fields: ['label', 'columns', 'rows', 'order_by', 'column_field', 'group_by_field', 'title_field'],
      limit_page_length: 1,
    })
    const v = (existing && existing[0]) || {}
    await call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.create_or_update_standard_view', {
      view: {
        doctype: 'CRM Deal',
        type: 'list',
        label: v.label,
        filters: JSON.stringify(filters || {}),
        columns: v.columns,
        rows: v.rows,
        order_by: v.order_by,
        column_field: v.column_field,
        group_by_field: v.group_by_field,
        title_field: v.title_field,
      },
    })
    await views.reload()
  } catch (e) {
    // fall through — still open the list even if persisting the filter failed
  }
  router.push({ name: 'Deals' })
}

// ---- drill-down drawer ----
const drill = ref(null)
function closeDrill() {
  drill.value = null
}
function drillGo(to) {
  closeDrill()
  router.push(to)
}

const allDeals = computed(() => d.value?.pipeline.deals || [])
function dealRows(list) {
  return list.map((dl) => ({
    primary: dl.organization || dl.name,
    secondary: [dl.name, dl.category, dl.stage].filter(Boolean).join(' · '),
    value: fmtINR(dl.value),
    to: { name: 'Deal', params: { dealId: dl.name } },
  }))
}

function drillPipeline() {
  drill.value = {
    title: __('Total Open Pipeline'),
    subtitle: __('{0} open deals', [d.value.pipeline.open_count]),
    rows: dealRows(allDeals.value),
    footer: { label: __('Open Deals list'), filters: { status: ['in', d.value.pipeline.open_statuses] } },
  }
}
function drillStage(stage) {
  drill.value = {
    title: stage,
    subtitle: __('Open opportunities in this stage'),
    rows: dealRows(allDeals.value.filter((dl) => dl.stage === stage)),
    footer: { label: __('Open Deals list'), filters: { status: stage } },
  }
}
function drillCategory(cat) {
  drill.value = {
    title: __('{0} — pipeline', [cat]),
    subtitle: __('Deals in this product category'),
    rows: dealRows(allDeals.value.filter((dl) => dl.category === cat)),
    footer: { label: __('Open Deals list'), filters: { product_category: cat } },
  }
}
function drillRegion(region) {
  drill.value = {
    title: region,
    subtitle: __('Deals in this region'),
    rows: dealRows(allDeals.value.filter((dl) => dl.region === region)),
    footer: { label: __('Open Deals list'), filters: region === 'Unassigned' ? {} : { territory: region } },
  }
}
function drillDormant() {
  drill.value = {
    title: __('Dormant Accounts'),
    subtitle: __('No order in 30+ days'),
    rows: d.value.account_health.dormant.map((a) => ({
      primary: a.organization_name,
      secondary: __('Last order {0}', [formatDate(a.last_order)]),
      badge: `${a.days}d`,
      badgeTheme: a.days > 90 ? 'red' : 'orange',
      to: { name: 'Organization', params: { organizationId: a.organization } },
    })),
  }
}
function drillAtRisk() {
  drill.value = {
    title: __('Accounts at Risk'),
    subtitle: __('Ordering less frequently this quarter'),
    rows: d.value.account_health.accounts_at_risk.map((a) => ({
      primary: a.organization_name,
      secondary: `${a.last_qtr} → ${a.this_qtr} ${__('orders')}${a.owner ? ' · ' + a.owner : ''}`,
      badge: __('Declining'),
      badgeTheme: 'red',
      to: { name: 'Organization', params: { organizationId: a.organization } },
    })),
  }
}
function drillAccounts() {
  drill.value = {
    title: __('Top Accounts by Revenue'),
    subtitle: __('Year to date'),
    rows: d.value.account_health.top_accounts.map((a) => ({
      primary: a.organization_name,
      secondary: __('YTD revenue'),
      value: fmtINR(a.value),
      to: { name: 'Organization', params: { organizationId: a.organization } },
    })),
  }
}
function drillOverdue() {
  drill.value = {
    title: __('Overdue Payments'),
    subtitle: __('{0} accounts', [d.value.overdue_payments.count]),
    rows: d.value.overdue_payments.accounts.map((a) => ({
      primary: a.customer,
      secondary: __('{0} days overdue', [a.days]),
      value: fmtINR(a.amount),
      badge: a.days > 90 ? __('Critical') : __('Overdue'),
      badgeTheme: 'red',
    })),
  }
}

const periods = [
  { label: 'This Month', value: 'month' },
  { label: 'This Quarter', value: 'quarter' },
  { label: 'Year to Date', value: 'ytd' },
]
const period = ref('month')

const dash = createResource({
  url: 'crm.api.ceo_dashboard.get_ceo_dashboard',
  params: { period: period.value },
  auto: true,
})
watch(period, (p) => dash.reload({ period: p }))

const d = computed(() => dash.data)

const revenueLabel = computed(
  () =>
    ({ month: __('Revenue Booked — MTD'), quarter: __('Revenue Booked — QTD'), ytd: __('Revenue Booked — YTD') })[
      period.value
    ],
)

const maxStageValue = computed(() => Math.max(1, ...(d.value?.pipeline.by_stage || []).map((s) => s.value)))
const maxRegionValue = computed(() => Math.max(1, ...(d.value?.pipeline.by_region || []).map((r) => r.value)))
const maxAccountValue = computed(() => Math.max(1, ...(d.value?.account_health.top_accounts || []).map((a) => a.value)))
const maxWaitDays = computed(() => Math.max(1, ...(d.value?.waiting_time || []).map((w) => w.avg_days)))
const bottlenecks = computed(() => (d.value?.waiting_time || []).slice(0, 3))

function waitStatus(days) {
  return days > 8 ? __('Critical') : days > 4 ? __('Watch') : __('OK')
}
function waitTheme(days) {
  return days > 8 ? 'red' : days > 4 ? 'orange' : 'green'
}

const catColors = { Alloys: 'bg-blue-500', Plating: 'bg-purple-500', Machines: 'bg-amber-500' }
const catPalette = ['bg-blue-500', 'bg-purple-500', 'bg-amber-500', 'bg-green-500']
function catColor(cat, i) {
  return catColors[cat] || catPalette[i % catPalette.length]
}

function ratio(v, max) {
  return Math.max(0.02, (v || 0) / max)
}

function fmtDuration(seconds) {
  const s = seconds || 0
  if (!s) return '—'
  const days = s / 86400
  if (days >= 1) return `${days.toFixed(days >= 10 ? 0 : 1)} d`
  const hours = s / 3600
  if (hours >= 1) return `${hours.toFixed(1)} h`
  return `${Math.round(s / 60)} m`
}

function fmtINR(v) {
  const n = Math.abs(v || 0)
  if (n >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`
  if (n >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v || 0)
}

function pct(now, base) {
  if (!base) return now ? '+100%' : '0%'
  const p = Math.round(((now - base) / base) * 100)
  return `${p >= 0 ? '+' : ''}${p}%`
}

function tone(now, base) {
  return now >= base ? 'green' : 'red'
}
const trendIcon = (now, base) => (now >= base ? LucideTrendingUp : LucideTrendingDown)
</script>
