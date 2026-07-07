<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Sales Manager'), route: { name: 'SalesManagerDashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Sales Manager Dashboard') }}</h1>
          <span class="flex items-center gap-1 text-xs text-ink-gray-5">
            <span class="h-2 w-2 rounded-full bg-surface-green-3"></span>{{ __('Live') }}
          </span>
        </div>
        <div v-if="d" class="flex items-center gap-1.5 text-sm text-ink-gray-5">
          <span>{{ d.is_fallback ? __('All teams') : __('My team') }} · {{ d.team.length }} {{ __('AEs') }}</span>
        </div>
      </div>

      <template v-if="d">
        <!-- TEAM PIPELINE -->
        <SectionLabel :label="__('Team Pipeline')" />
        <div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <Tile :title="__('Team Pipeline Value')" :value="fmtINR(d.pipeline.team_value)"
            :sub="__('{0} open deals', [d.pipeline.team_open_count])" />
          <Tile v-for="a in d.pipeline.by_ae" :key="a.ae" :title="aeLabel(a.ae)"
            :value="fmtINR(a.value)" :sub="__('{0} deals', [a.deals])" @click="drillAE(a.ae)" />
        </div>

        <div class="mb-5 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Team Pipeline by Stage')">
            <BarRow v-for="s in d.pipeline.by_stage" :key="s.stage" :label="s.stage"
              :sub="__('{0} deals', [s.count])" :value="fmtINR(s.value)"
              :ratio="ratio(s.count, maxStageCount)" @click="drillStage(s.stage)" />
            <Empty v-if="!d.pipeline.by_stage.length" />
          </Card>
          <Card :title="__('Opportunities by Category')">
            <div class="mb-3 flex h-2.5 w-full overflow-hidden rounded-full bg-surface-gray-2">
              <div v-for="(c, i) in d.pipeline.by_category" :key="c.category"
                class="cursor-pointer" :class="catColor(c.category, i)"
                :style="`width: ${c.pct}%`" :title="c.category" @click="drillCategory(c.category)"></div>
            </div>
            <div v-for="(c, i) in d.pipeline.by_category" :key="c.category"
              class="-mx-1 mb-1 flex cursor-pointer items-center justify-between rounded px-1 py-0.5 text-sm hover:bg-surface-gray-1"
              @click="drillCategory(c.category)">
              <span class="flex items-center gap-2 text-ink-gray-7">
                <span class="h-2.5 w-2.5 rounded-sm" :class="catColor(c.category, i)"></span>{{ c.category }}
              </span>
              <span class="text-ink-gray-8">
                <span class="font-medium">{{ c.pct }}%</span>
                <span class="ml-1 text-ink-gray-4">· {{ fmtINR(c.value) }}</span>
              </span>
            </div>
            <Empty v-if="!d.pipeline.by_category.length" :text="__('No product category on deals')" />
          </Card>
        </div>

        <Card :title="__('Each AE\'s Stage Distribution')" class="mb-6">
          <div v-if="d.pipeline.stage_dist.rows.length" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 pr-2 text-left font-normal">{{ __('Salesperson') }}</th>
                  <th v-for="st in d.pipeline.stage_dist.stages" :key="st"
                    class="px-1 py-1.5 text-center font-normal">{{ st }}</th>
                  <th class="py-1.5 pl-2 text-right font-normal">{{ __('Total') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in d.pipeline.stage_dist.rows" :key="row.ae"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                  @click="drillAE(row.ae)">
                  <td class="py-1.5 pr-2">
                    <span class="flex items-center gap-2">
                      <Avatar :label="aeName(row.ae)" size="sm" />
                      <span class="text-ink-gray-8">{{ aeName(row.ae) }}</span>
                    </span>
                  </td>
                  <td v-for="(n, i) in row.dist" :key="i" class="px-1 py-1.5 text-center"
                    :class="n ? 'font-medium text-ink-gray-8' : 'text-ink-gray-3'">{{ n }}</td>
                  <td class="py-1.5 pl-2 text-right font-semibold text-ink-gray-9">{{ row.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <Empty v-else />
        </Card>

        <!-- LEAD MANAGEMENT -->
        <SectionLabel :label="__('Lead Management')" />
        <div class="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Tile :title="__('Leads Assigned to Team')" :value="String(d.leads.assigned)"
            :sub="__('across team members')" />
          <Tile :title="__('Actioned')" :value="String(d.leads.actioned)"
            :sub="__('{0}% contacted', [actionedPct])" tone="green" />
          <Tile :title="__('Not Actioned')" :value="String(d.leads.not_actioned)"
            :sub="__('awaiting first contact')" tone="amber" />
          <Tile :title="__('Not Contacted 7+ Days')" :value="String(d.leads.not_contacted_7d_count)"
            :sub="__('need first contact')" tone="red" @click="drillNotContacted()" />
        </div>

        <!-- ACTIVITY -->
        <SectionLabel :label="__('Activity')" />
        <div class="mb-5 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Overdue Follow-ups by AE')">
            <BarRow v-for="a in d.activity.overdue_by_ae" :key="a.ae" :label="aeName(a.ae)"
              :value="__('{0} overdue', [a.count])" :ratio="ratio(a.count, maxOverdue)" color="red"
              @click="goTasks()" />
            <Empty v-if="!d.activity.overdue_by_ae.length" :text="__('No overdue follow-ups')" />
          </Card>
          <Card :title="__('Calls Logged — This Week')">
            <table v-if="d.activity.calls_week.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Salesperson') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Calls') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.activity.calls_week" :key="a.ae" class="border-t border-outline-gray-1">
                  <td class="py-1.5">
                    <span class="flex items-center gap-2">
                      <Avatar :label="aeName(a.ae)" size="sm" />
                      <span class="text-ink-gray-8">{{ aeName(a.ae) }}</span>
                    </span>
                  </td>
                  <td class="py-1.5 text-right font-medium text-ink-gray-8">{{ a.calls }}</td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No calls logged this week')" />
          </Card>
        </div>

        <Card :title="__('Accounts With No Activity in 30 Days')" class="mb-6">
          <table v-if="d.activity.no_activity_30d.length" class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('Owner') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Days Silent') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in d.activity.no_activity_30d" :key="a.organization"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                @click="goOrg(a.organization)">
                <td class="py-1.5 text-ink-gray-8">{{ a.organization_name }}</td>
                <td class="py-1.5 text-ink-gray-6">{{ aeName(a.owner) }}</td>
                <td class="py-1.5 text-right">
                  <Badge :theme="a.days > 40 ? 'red' : 'orange'" :label="`${a.days}d`" variant="subtle" />
                </td>
              </tr>
            </tbody>
          </table>
          <Empty v-else :text="__('All accounts have recent activity')" />
        </Card>

        <!-- TECHNICAL & TRIALS -->
        <SectionLabel :label="__('Technical & Trials')" />
        <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Tile :title="__('Tech Assignments Pending')" :value="String(d.technical.tech_pending_count)"
            :sub="__('awaiting response')" tone="amber" @click="drillTech()" />
          <Tile :title="__('Avg Technical Response')" :value="fmtDuration(d.technical.avg_response_seconds)"
            :sub="__('across {0} deals', [d.technical.avg_response_count])" />
          <Tile :title="__('Trials in Progress')" :value="String(d.technical.trials_count)"
            :sub="__('active trials')" @click="drillTrials()" />
          <Tile :title="__('Trial Conversion — Team')" :value="`${d.technical.trial_conversion.rate}%`"
            :sub="__('{0} of {1} trials', [d.technical.trial_conversion.successful, d.technical.trial_conversion.total])"
            tone="green" />
        </div>

        <Card v-if="d.technical.trials.length" :title="__('Trials in Progress')" class="mb-6">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Customer') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('Product') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('Owner') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Expected Outcome') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in d.technical.trials" :key="t.name"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                @click="goDeal(t.name)">
                <td class="py-1.5 text-ink-gray-8">{{ t.organization_name }}</td>
                <td class="py-1.5 text-ink-gray-6">{{ t.product }}</td>
                <td class="py-1.5 text-ink-gray-6">{{ aeName(t.ae) }}</td>
                <td class="py-1.5 text-right text-ink-gray-6">{{ t.expected ? formatDate(t.expected) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </Card>

        <!-- DORMANCY -->
        <SectionLabel :label="__('Dormancy — My Territory')" />
        <div class="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('At Risk — No Order 20–30 Days')">
            <table v-if="d.dormancy.at_risk.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Owner') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Days') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.dormancy.at_risk" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                  @click="goOrg(a.organization)">
                  <td class="py-1.5 text-ink-gray-8">{{ a.organization_name }}</td>
                  <td class="py-1.5 text-ink-gray-6">{{ aeName(a.owner) }}</td>
                  <td class="py-1.5 text-right">
                    <Badge theme="orange" :label="`${a.days}d`" variant="subtle" />
                  </td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No accounts in the early-warning window')" />
          </Card>
          <Card :title="__('Dormant — No Order 30+ Days')">
            <table v-if="d.dormancy.dormant.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Last Order') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Days') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.dormancy.dormant" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                  @click="goOrg(a.organization)">
                  <td class="py-1.5 text-ink-gray-8">{{ a.organization_name }}</td>
                  <td class="py-1.5 text-ink-gray-6">{{ formatDate(a.last_order) }}</td>
                  <td class="py-1.5 text-right">
                    <Badge theme="red" :label="`${a.days}d`" variant="subtle" />
                  </td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No dormant accounts')" />
          </Card>
        </div>

        <!-- WAITING TIME -->
        <SectionLabel :label="__('Waiting Time — My Team')" />
        <Card :title="__('Where Deals Get Stuck')" class="mb-4">
          <BarRow v-for="w in d.waiting_time" :key="w.stage" :label="w.stage"
            :sub="__('{0} deals', [w.count])" :value="__('{0} d', [w.avg_days])"
            :ratio="ratio(w.avg_days, maxWaitDays)"
            :color="w.avg_days === maxWaitDays ? 'red' : 'amber'" />
          <Empty v-if="!d.waiting_time.length" />
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
import { formatDate } from '@/utils'
import { Avatar, Badge, Breadcrumbs, Button, call, createResource } from 'frappe-ui'
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { viewsStore } from '@/stores/views'

const router = useRouter()
const { getUser } = usersStore()

const goOrg = (name) => name && router.push({ name: 'Organization', params: { organizationId: name } })
const goDeal = (name) => name && router.push({ name: 'Deal', params: { dealId: name } })
const goTasks = () => router.push({ name: 'Tasks' })

function aeName(email) {
  if (!email || email === 'Unassigned') return __('Unassigned')
  return getUser(email).full_name || email
}
function aeLabel(email) {
  return __('{0} · Pipeline', [aeName(email)])
}

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
    primary: dl.organization_name || dl.name,
    secondary: [dl.name, dl.category, dl.stage].filter(Boolean).join(' · '),
    value: fmtINR(dl.value),
    to: { name: 'Deal', params: { dealId: dl.name } },
  }))
}

function drillAE(ae) {
  drill.value = {
    title: __('{0} — pipeline', [aeName(ae)]),
    subtitle: __('Open deals owned by this AE'),
    rows: dealRows(allDeals.value.filter((dl) => (dl.ae || 'Unassigned') === ae)),
    footer: ae === 'Unassigned' ? null : { label: __('Open Deals list'), filters: { deal_owner: ae } },
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
    title: __('{0} — team pipeline', [cat]),
    subtitle: __('Deals in this product category'),
    rows: dealRows(allDeals.value.filter((dl) => dl.category === cat)),
    footer: { label: __('Open Deals list'), filters: { product_category: cat } },
  }
}
function drillNotContacted() {
  drill.value = {
    title: __('Leads Not Contacted — 7+ days'),
    subtitle: __('{0} leads need first contact', [d.value.leads.not_contacted_7d_count]),
    rows: d.value.leads.not_contacted_7d.map((l) => ({
      primary: l.lead_name,
      secondary: `${l.organization || __('No organization')} · ${aeName(l.ae)}`,
      badge: `${l.days}d`,
      badgeTheme: l.days > 14 ? 'red' : 'orange',
      to: { name: 'Lead', params: { leadId: l.name } },
    })),
  }
}
function drillTech() {
  drill.value = {
    title: __('Technical Assignments Pending'),
    subtitle: __('{0} awaiting response', [d.value.technical.tech_pending_count]),
    rows: d.value.technical.tech_pending.map((t) => ({
      primary: t.organization_name,
      secondary: `${t.name} · ${aeName(t.ae)}`,
      badge: `${t.days}d`,
      badgeTheme: t.days > 7 ? 'red' : 'orange',
      to: { name: 'Deal', params: { dealId: t.name } },
    })),
  }
}
function drillTrials() {
  drill.value = {
    title: __('Trials in Progress'),
    subtitle: __('{0} active trials', [d.value.technical.trials_count]),
    rows: d.value.technical.trials.map((t) => ({
      primary: t.organization_name,
      secondary: `${t.product} · ${aeName(t.ae)}`,
      to: { name: 'Deal', params: { dealId: t.name } },
    })),
  }
}

const dash = createResource({
  url: 'crm.api.sales_manager_dashboard.get_sales_manager_dashboard',
  auto: true,
})
const d = computed(() => dash.data)

const actionedPct = computed(() =>
  d.value?.leads.assigned ? Math.round((d.value.leads.actioned / d.value.leads.assigned) * 100) : 0,
)
const maxStageCount = computed(() => Math.max(1, ...(d.value?.pipeline.by_stage || []).map((s) => s.count)))
const maxOverdue = computed(() => Math.max(1, ...(d.value?.activity.overdue_by_ae || []).map((a) => a.count)))
const maxWaitDays = computed(() => Math.max(1, ...(d.value?.waiting_time || []).map((w) => w.avg_days)))

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

// ---- tiny presentational components (kept local to this dashboard) ----
const SectionLabel = (props) =>
  h('div', { class: 'mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5' }, props.label)
SectionLabel.props = ['label']

const toneClass = {
  green: 'text-ink-green-3',
  red: 'text-ink-red-3',
  amber: 'text-ink-amber-3',
}
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
    h('div', { class: 'mb-3 text-sm font-medium text-ink-gray-8' }, props.title),
    slots.default?.(),
  ])
Card.props = ['title']

const barColor = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
}
const Bar = (props) =>
  h('div', { class: 'h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2' }, [
    h('div', {
      class: `h-full rounded-full ${barColor[props.color] || barColor.blue}`,
      style: `width: ${Math.round(props.ratio * 100)}%`,
    }),
  ])
Bar.props = ['ratio', 'color']

const BarRow = (props, { attrs }) =>
  h(
    'div',
    { ...attrs, class: 'mb-2.5 last:mb-0' + (attrs.onClick ? ' cursor-pointer' : '') },
    [
      h('div', { class: 'mb-1 flex items-center justify-between text-sm' }, [
        h('span', { class: 'text-ink-gray-8' }, props.label),
        h('span', { class: 'text-ink-gray-6' }, [
          props.sub ? h('span', { class: 'mr-2 text-ink-gray-4' }, props.sub) : null,
          h('span', { class: 'font-medium text-ink-gray-8' }, props.value),
        ]),
      ]),
      h(Bar, { ratio: props.ratio, color: props.color }),
    ],
  )
BarRow.props = ['label', 'sub', 'value', 'ratio', 'color']
BarRow.inheritAttrs = false

const Empty = (props) =>
  h('div', { class: 'py-6 text-center text-sm text-ink-gray-4' }, props.text || __('No data'))
Empty.props = ['text']
</script>
