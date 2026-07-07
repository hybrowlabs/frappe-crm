<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Repeat Business'), route: { name: 'RepeatBusinessDashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Repeat Business Dashboard') }}</h1>
          <Badge theme="green" variant="subtle" :label="__('80% of revenue')" />
        </div>
        <div v-if="d" class="flex items-center gap-1.5 text-sm text-ink-gray-5">
          <span>{{ __('{0} accounts', [d.total_accounts]) }}</span>
        </div>
      </div>

      <template v-if="d">
        <div v-if="!d.has_orders"
          class="mb-5 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-4 py-2.5 text-sm text-ink-amber-3">
          {{ __('Order data (ERPNext Sales Orders) is not available on this site — order-frequency and revenue metrics show as zero. Dormancy uses the last-order signal on the account.') }}
        </div>

        <!-- ORDER FREQUENCY -->
        <SectionLabel :label="__('Order Frequency')" :hint="__('the core repeat-revenue view')" />
        <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Tile :title="__('Ordering 3+ Times This Month')" :value="String(d.order_frequency.order_3plus_count)"
            :sub="__('special-offer trigger')" tone="green" @click="drillAccounts(__('Ordering 3+ This Month'), __('Loyalty / special-offer candidates'), d.order_frequency.rows.filter((a) => a.this_month >= 3), (a) => __('{0} orders · {1}', [a.this_month, aeName(a.ae)]))" />
          <Tile :title="__('Avg Order Frequency')" :value="String(d.order_frequency.avg_freq)" :sub="__('orders / account / month')" />
          <Tile :title="__('Healthy Accounts')" :value="String(d.order_frequency.healthy_count)"
            :sub="__('of {0} accounts', [d.total_accounts])" tone="green" />
          <Tile :title="__('Dormant (30+ Days)')" :value="String(d.order_frequency.dormant_30_count)"
            :sub="__('no order in 30 days')" tone="red" @click="drillAccounts(__('Dormant Accounts'), __('No order in 30+ days'), d.dormant.rows, (a) => __('{0}d · AE {1}', [a.days, aeName(a.ae)]))" />
        </div>

        <Card class="mb-6">
          <template #title>
            <div class="flex items-center justify-between">
              <span>{{ __('Account Order Frequency') }}</span>
              <span class="flex items-center gap-3 text-xs font-normal text-ink-gray-5">
                <span class="flex items-center gap-1"><Dot color="green" />{{ __('Healthy') }}</span>
                <span class="flex items-center gap-1"><Dot color="amber" />{{ __('Declining') }}</span>
                <span class="flex items-center gap-1"><Dot color="red" />{{ __('Dormant') }}</span>
                <span class="flex items-center gap-1"><Dot color="gray" />{{ __('No Data') }}</span>
              </span>
            </div>
          </template>
          <table v-if="d.order_frequency.rows.length" class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('AE') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('This Month') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('Last Month') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('This Qtr') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('YTD') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in d.order_frequency.rows" :key="a.organization"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                <td class="py-1.5">
                  <span class="flex items-center gap-2">
                    <span class="h-5 w-1 rounded-sm" :class="statusBar(a.status)"></span>
                    <Avatar :label="a.organization_name" size="sm" />
                    <span class="font-medium text-ink-gray-8">{{ a.organization_name }}</span>
                  </span>
                </td>
                <td class="py-1.5 text-ink-gray-6">{{ aeName(a.ae) }}</td>
                <td class="py-1.5 text-center font-semibold text-ink-gray-9">{{ a.this_month }}</td>
                <td class="py-1.5 text-center text-ink-gray-5">{{ a.last_month }}</td>
                <td class="py-1.5 text-center text-ink-gray-5">{{ a.this_qtr }}</td>
                <td class="py-1.5 text-center text-ink-gray-5">{{ a.ytd_orders }}</td>
                <td class="py-1.5 text-right">
                  <Badge :theme="statusTheme(a.status)" :label="a.status" variant="subtle" />
                </td>
              </tr>
            </tbody>
          </table>
          <Empty v-else :text="__('No accounts')" />
        </Card>

        <!-- EARLY WARNING -->
        <SectionLabel :label="__('Early Warning')" :hint="__('catch accounts before they go dormant')" />
        <div class="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Tile :title="__('Ordering Below Their Average')" :value="String(d.early_warning.below_avg_count)"
            :sub="__('< 3-month rolling avg')" tone="amber" />
          <Tile :title="__('Declining Order Value')" :value="String(d.early_warning.declining_value_count)"
            :sub="__('AOV this qtr < last qtr')" tone="amber" />
          <Tile :title="__('No Order 20–29 Days')" :value="String(d.early_warning.no_order_2029_count)"
            :sub="__('pre-dormancy alert')" tone="amber" />
        </div>

        <div class="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Ordering Below Average')">
            <table v-if="d.early_warning.below_avg.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                  <th class="py-1.5 text-center font-normal">{{ __('This Month') }}</th>
                  <th class="py-1.5 text-center font-normal">{{ __('3-mo Avg') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('AE') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.early_warning.below_avg" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                  <td class="py-1.5 text-center font-semibold text-ink-red-3">{{ a.this_month }}</td>
                  <td class="py-1.5 text-center text-ink-gray-5">{{ a.avg3mo }}</td>
                  <td class="py-1.5 text-ink-gray-6">{{ aeName(a.ae) }}</td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No accounts below their average')" />
          </Card>
          <Card :title="__('Declining Order Value')">
            <table v-if="d.early_warning.declining_value.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('AOV This Qtr') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Last Qtr') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.early_warning.declining_value" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                  <td class="py-1.5 text-right font-semibold text-ink-red-3">{{ fmtINR(a.aov_q) }}</td>
                  <td class="py-1.5 text-right text-ink-gray-5">{{ fmtINR(a.aov_lastq) }}</td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No accounts with declining order value')" />
          </Card>
        </div>

        <!-- DORMANT ACCOUNTS -->
        <SectionLabel :label="__('Dormant Accounts')" />
        <div class="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Tile :title="__('No Order 30+ Days')" :value="String(d.dormant.d30_count)" :sub="__('needs action')" tone="amber" />
          <Tile :title="__('No Order 60+ Days')" :value="String(d.dormant.d60_count)" :sub="__('escalation required')" tone="red" />
          <Tile :title="__('Win-Back (90+ Days)')" :value="String(d.dormant.winback_count)" :sub="__('re-engagement campaign')" tone="red"
            @click="drillAccounts(__('Win-Back Candidates'), __('No order in 90+ days'), d.dormant.winback, (a) => __('{0}d · AE {1}', [a.days, aeName(a.ae)]))" />
        </div>

        <Card :title="__('Dormant Accounts — Escalation View')" class="mb-6">
          <table v-if="d.dormant.rows.length" class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('AE') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('Last Order') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('Days Since') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('Last Interaction') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Tier') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in d.dormant.rows" :key="a.organization"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                <td class="py-1.5 text-ink-gray-6">{{ aeName(a.ae) }}</td>
                <td class="py-1.5 text-ink-gray-5">{{ a.last_order ? formatDate(a.last_order) : '—' }}</td>
                <td class="py-1.5 text-center font-semibold text-ink-red-3">{{ a.days }}d</td>
                <td class="py-1.5 text-ink-gray-5">{{ __('{0}d ago', [a.last_interaction_days]) }}</td>
                <td class="py-1.5 text-right">
                  <Badge :theme="a.days >= 60 ? 'red' : 'orange'"
                    :label="a.days >= 90 ? __('Win-back') : a.days > 60 ? __('60+ escalate') : __('30+ act')" variant="subtle" />
                </td>
              </tr>
            </tbody>
          </table>
          <Empty v-else :text="__('No dormant accounts')" />
        </Card>

        <!-- REVENUE TREND -->
        <SectionLabel :label="__('Revenue Trend')" />
        <div class="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Revenue per Account — This Year vs Last')">
            <table v-if="d.revenue_trend.rows.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('This Year') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Last Year') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Trend') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.revenue_trend.rows" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                  <td class="py-1.5 text-right font-medium text-ink-gray-8">{{ fmtINR(a.rev_ytd) }}</td>
                  <td class="py-1.5 text-right text-ink-gray-5">{{ fmtINR(a.rev_last_year) }}</td>
                  <td class="py-1.5 text-right"><Badge :theme="trend(a).theme" :label="trend(a).label" variant="subtle" /></td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No revenue recorded')" />
          </Card>
          <div class="flex flex-col gap-3">
            <Card :title="__('Top Accounts by Order Frequency')">
              <BarRow v-for="(a, i) in d.revenue_trend.top_by_freq" :key="a.organization"
                :label="`${i + 1}. ${a.organization_name}`" :value="__('{0} orders', [a.ytd_orders])"
                :ratio="ratio(a.ytd_orders, maxFreq)" color="green" @click="goOrg(a.organization)" />
              <Empty v-if="!d.revenue_trend.top_by_freq.length" :text="__('No orders recorded')" />
            </Card>
            <Card :title="__('Revenue Concentration')">
              <div class="mb-3 flex h-3 w-full overflow-hidden rounded-full">
                <div class="bg-blue-500" :style="`width: ${d.revenue_trend.concentration.top_pct}%`"></div>
                <div class="bg-surface-gray-3" :style="`width: ${100 - d.revenue_trend.concentration.top_pct}%`"></div>
              </div>
              <div class="mb-1 flex items-center justify-between text-sm">
                <span class="flex items-center gap-2 text-ink-gray-7"><span class="h-2.5 w-2.5 rounded-sm bg-blue-500"></span>{{ __('Top {0} accounts', [d.revenue_trend.concentration.top_n]) }}</span>
                <span class="font-medium text-ink-gray-8">{{ d.revenue_trend.concentration.top_pct }}% · {{ fmtINR(d.revenue_trend.concentration.top_value) }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="flex items-center gap-2 text-ink-gray-7"><span class="h-2.5 w-2.5 rounded-sm bg-surface-gray-3"></span>{{ __('Rest of accounts') }}</span>
                <span class="font-medium text-ink-gray-8">{{ 100 - d.revenue_trend.concentration.top_pct }}% · {{ fmtINR(d.revenue_trend.concentration.rest_value) }}</span>
              </div>
              <div v-if="d.revenue_trend.concentration.top_pct > 55"
                class="mt-3 rounded-md bg-surface-amber-1 px-3 py-2 text-xs text-ink-amber-3">
                {{ __('High concentration — {0}% of revenue from {1} accounts. Diversify to reduce risk.', [d.revenue_trend.concentration.top_pct, d.revenue_trend.concentration.top_n]) }}
              </div>
            </Card>
          </div>
        </div>

        <!-- CROSS-SELL -->
        <SectionLabel :label="__('Cross-Sell')" :hint="__('grow wallet share')" />
        <div class="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Tile :title="__('Buying Only One Category')" :value="String(d.cross_sell.one_cat_count)"
            :sub="__('cross-sell opportunity')" tone="amber"
            @click="drillAccounts(__('Buying Only One Category'), __('Never bought other categories'), d.cross_sell.one_cat, (a) => __('Buys {0} · missing {1}', [a.cats.join(', '), d.cross_sell.categories.filter((c) => !a.cats.includes(c)).join(', ')]))" />
          <Tile :title="__('Special-Offer Candidates')" :value="String(d.cross_sell.order_3plus_count)"
            :sub="__('3+ orders this month')" tone="green"
            @click="drillAccounts(__('Special-Offer Conversation'), __('3+ orders this month — loyalty'), d.order_frequency.rows.filter((a) => a.this_month >= 3), (a) => __('{0} orders · AE {1}', [a.this_month, aeName(a.ae)]))" />
        </div>

        <Card :title="__('Cross-Sell Gap Analysis')" class="mb-6">
          <template #title>
            <div class="flex items-center justify-between">
              <span>{{ __('Cross-Sell Gap Analysis') }}</span>
              <span class="text-xs font-normal text-ink-gray-5">{{ __('● buys  ○ gap') }}</span>
            </div>
          </template>
          <table v-if="d.cross_sell.gap_rows.length" class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                <th v-for="c in d.cross_sell.categories" :key="c" class="py-1.5 text-center font-normal">{{ c }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Gaps') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in d.cross_sell.gap_rows" :key="a.organization"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                <td v-for="(c, i) in d.cross_sell.categories" :key="c" class="py-1.5 text-center">
                  <span v-if="a.cats.includes(c)" class="inline-block h-3 w-3 rounded-full" :class="catColor(c, i)"></span>
                  <span v-else class="inline-block h-3 w-3 rounded-full border-[1.5px] border-outline-gray-3"></span>
                </td>
                <td class="py-1.5 text-right">
                  <Badge v-if="gaps(a).length" theme="orange" :label="__('{0} gap', [gaps(a).length])" variant="subtle" />
                  <Badge v-else theme="green" :label="__('Full')" variant="subtle" />
                </td>
              </tr>
            </tbody>
          </table>
          <Empty v-else :text="__('No purchase-category data on accounts')" />
        </Card>

        <!-- MARKETING REPEAT -->
        <SectionLabel :label="__('Marketing Repeat')" />
        <Card :title="__('Marketing-Sourced Accounts Now on Repeat Cycle')" class="mb-4">
          <table v-if="d.marketing_repeat.length" class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('Orders YTD') }}</th>
                <th class="py-1.5 text-center font-normal">{{ __('This Month') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Revenue YTD') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in d.marketing_repeat" :key="a.organization"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                <td class="py-1.5 text-center font-semibold text-ink-gray-9">{{ a.ytd_orders }}</td>
                <td class="py-1.5 text-center text-ink-gray-5">{{ a.this_month }}</td>
                <td class="py-1.5 text-right font-medium text-ink-gray-8">{{ fmtINR(a.rev_ytd) }}</td>
              </tr>
            </tbody>
          </table>
          <Empty v-else :text="__('No marketing-sourced accounts on a repeat cycle yet')" />
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
            class="flex cursor-pointer items-center gap-3 border-b border-outline-gray-1 px-4 py-2.5 hover:bg-surface-gray-1"
            @click="drillGo(r.to)">
            <Avatar :label="r.primary" size="md" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-medium text-ink-gray-9">{{ r.primary }}</div>
              <div class="truncate text-xs text-ink-gray-5">{{ r.secondary }}</div>
            </div>
            <span class="text-ink-gray-4">&rarr;</span>
          </div>
          <Empty v-if="!drill.rows.length" :text="__('No records')" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { formatDate } from '@/utils'
import { Avatar, Badge, Breadcrumbs, createResource } from 'frappe-ui'
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usersStore } from '@/stores/users'

const router = useRouter()
const { getUser } = usersStore()

const goOrg = (name) => name && router.push({ name: 'Organization', params: { organizationId: name } })

function aeName(email) {
  if (!email || email === 'Unassigned') return __('Unassigned')
  return getUser(email).full_name || email
}

const dash = createResource({
  url: 'crm.api.repeat_business_dashboard.get_repeat_business_dashboard',
  auto: true,
})
const d = computed(() => dash.data)

const maxFreq = computed(() => Math.max(1, ...(d.value?.revenue_trend.top_by_freq || []).map((a) => a.ytd_orders)))

function trend(a) {
  if (a.rev_ytd > a.rev_last_year * 1.05) return { theme: 'green', label: __('Growing') }
  if (a.rev_ytd < a.rev_last_year * 0.95) return { theme: 'red', label: __('Declining') }
  return { theme: 'gray', label: __('Flat') }
}
function gaps(a) {
  return (d.value?.cross_sell.categories || []).filter((c) => !a.cats.includes(c))
}

const statusTheme = (s) => ({ Healthy: 'green', Declining: 'orange', Dormant: 'red', 'No Data': 'gray' })[s] || 'gray'
const statusBar = (s) => ({ Healthy: 'bg-green-500', Declining: 'bg-amber-500', Dormant: 'bg-red-500' })[s] || 'bg-surface-gray-3'

// ---- drill-down drawer ----
const drill = ref(null)
function closeDrill() {
  drill.value = null
}
function drillGo(to) {
  closeDrill()
  router.push(to)
}
function drillAccounts(title, subtitle, list, metaFn) {
  drill.value = {
    title,
    subtitle,
    rows: list.map((a) => ({
      primary: a.organization_name,
      secondary: metaFn(a),
      to: { name: 'Organization', params: { organizationId: a.organization } },
    })),
  }
}

const catColors = { Alloys: 'bg-blue-500', Plating: 'bg-purple-500', Machines: 'bg-amber-500' }
const catPalette = ['bg-blue-500', 'bg-purple-500', 'bg-amber-500', 'bg-green-500']
function catColor(cat, i) {
  return catColors[cat] || catPalette[i % catPalette.length]
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

// ---- tiny presentational components (kept local to this dashboard) ----
const SectionLabel = (props) =>
  h('div', { class: 'mb-2 flex items-baseline gap-2' }, [
    h('span', { class: 'text-xs font-medium uppercase tracking-wide text-ink-gray-5' }, props.label),
    props.hint ? h('span', { class: 'text-xs text-ink-gray-4' }, props.hint) : null,
  ])
SectionLabel.props = ['label', 'hint']

const Dot = (props) =>
  h('span', { class: `inline-block h-2 w-2 rounded-full ${{ green: 'bg-green-500', amber: 'bg-amber-500', red: 'bg-red-500' }[props.color] || 'bg-surface-gray-4'}` })
Dot.props = ['color']

const toneClass = { green: 'text-ink-green-3', red: 'text-ink-red-3', amber: 'text-ink-amber-3' }
const Tile = (props, { attrs }) =>
  h(
    'div',
    {
      ...attrs,
      class:
        'rounded-lg border border-outline-gray-1 bg-surface-white p-4' +
        (attrs.onClick ? ' cursor-pointer transition hover:border-outline-gray-3' : ''),
    },
    [
      h('div', { class: 'mb-1 flex items-center justify-between text-xs text-ink-gray-5' }, [
        props.title,
        attrs.onClick ? h('span', { class: 'text-ink-gray-4' }, '→') : null,
      ]),
      h('div', { class: `text-2xl font-semibold ${toneClass[props.tone] || 'text-ink-gray-9'}` }, props.value),
      h('div', { class: 'mt-0.5 text-xs text-ink-gray-4' }, props.sub),
    ],
  )
Tile.props = ['title', 'value', 'sub', 'tone']
Tile.inheritAttrs = false

const Card = (props, { slots }) =>
  h('div', { class: 'rounded-lg border border-outline-gray-1 bg-surface-white p-4' }, [
    h('div', { class: 'mb-3 text-sm font-medium text-ink-gray-8' }, slots.title ? slots.title() : props.title),
    slots.default?.(),
  ])
Card.props = ['title']

const barColor = { blue: 'bg-blue-500', green: 'bg-green-500', amber: 'bg-amber-500', red: 'bg-red-500' }
const Bar = (props) =>
  h('div', { class: 'h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2' }, [
    h('div', { class: `h-full rounded-full ${barColor[props.color] || barColor.blue}`, style: `width: ${Math.round(props.ratio * 100)}%` }),
  ])
Bar.props = ['ratio', 'color']

const BarRow = (props, { attrs }) =>
  h('div', { ...attrs, class: 'mb-2.5 last:mb-0' + (attrs.onClick ? ' cursor-pointer' : '') }, [
    h('div', { class: 'mb-1 flex items-center justify-between text-sm' }, [
      h('span', { class: 'text-ink-gray-8' }, props.label),
      h('span', { class: 'font-medium text-ink-gray-8' }, props.value),
    ]),
    h(Bar, { ratio: props.ratio, color: props.color }),
  ])
BarRow.props = ['label', 'value', 'ratio', 'color']
BarRow.inheritAttrs = false

const Empty = (props) =>
  h('div', { class: 'py-6 text-center text-sm text-ink-gray-4' }, props.text || __('No data'))
Empty.props = ['text']
</script>
