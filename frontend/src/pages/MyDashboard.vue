<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Dashboards'), route: { name: 'Dashboard' } }, { label: __('My Dashboard'), route: { name: 'MyDashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto pa-page">
      <div class="pa-page-h">
        <h1 class="pa-h1">{{ __('My Dashboard') }} <span class="pa-live">{{ __('Live') }}</span></h1>
        <div v-if="d" class="pa-meta">
          <Avatar :label="meName" size="sm" /><span>{{ meName }}</span>
        </div>
      </div>

      <template v-if="d">
        <!-- MY PIPELINE -->
        <SectionLabel :label="__('My Pipeline')" :hint="__('click a stage to see the deals')" />
        <div class="mb-3.5 grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-6">
          <Tile v-for="st in d.pipeline.by_stage" :key="st.stage" :icon="LucideFunnel" :title="st.stage" :value="String(st.count)"
            :sub="fmtINR(st.value)" @click="drillStage(st.stage)" />
          <Tile :icon="LucideIndianRupee" :title="__('Total Pipeline Value')" :value="fmtINR(d.pipeline.total_value)"
            :sub="__('{0} open deals', [d.pipeline.total_count])" tone="green" />
        </div>

        <Card :title="__('Pipeline by Stage')" class="mb-8">
          <Bars>
            <BarRow v-for="st in d.pipeline.by_stage" :key="st.stage" :label="st.stage"
              :value="__('{0} deals · {1}', [st.count, fmtINR(st.value)])"
              :ratio="ratio(st.count, maxStage)" color="blue" @click="drillStage(st.stage)" />
          </Bars>
          <Empty v-if="!d.pipeline.by_stage.length" />
        </Card>

        <!-- MY TASKS -->
        <SectionLabel :label="__('My Tasks')" />
        <div class="mb-3.5 grid grid-cols-1 gap-3.5 sm:grid-cols-3">
          <Tile :icon="LucideCircleCheck" :title="__('Today\'s Tasks')" :value="String(d.tasks.today_count)" :sub="__('due today')" />
          <Tile :icon="LucideTriangleAlert" :title="__('Overdue Actions')" :value="String(d.tasks.overdue_count)" :sub="__('past due date')" tone="red" />
          <Tile :icon="LucideClock" :title="__('Pending Tech Responses')" :value="String(d.tasks.pending_tech_count)" :sub="__('waiting on tech team')" tone="amber" />
        </div>

        <div class="mb-8 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
          <Card :title="__('Today\'s Tasks & Follow-ups')">
            <table v-if="d.tasks.today.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Task') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Reference') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Priority') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in d.tasks.today" :key="t.name"
                  class="border-t border-outline-gray-1" :class="t.reference_docname ? 'cursor-pointer hover:bg-surface-gray-1' : ''"
                  @click="goRef(t)">
                  <td class="py-1.5 font-medium text-ink-gray-8">{{ t.title }}</td>
                  <td class="py-1.5 text-ink-gray-5">{{ t.reference_docname || '—' }}</td>
                  <td class="py-1.5 text-right"><Badge v-if="t.priority" :theme="t.priority === 'High' ? 'red' : t.priority === 'Medium' ? 'orange' : 'gray'" :label="t.priority" variant="subtle" /></td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No tasks due today')" />
          </Card>
          <Card>
            <template #title>
              <div class="flex items-center justify-between">
                <span>{{ __('Overdue Actions') }}</span>
                <Badge v-if="d.tasks.overdue_count" theme="red" :label="String(d.tasks.overdue_count)" variant="subtle" />
              </div>
            </template>
            <table v-if="d.tasks.overdue.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Task') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Due') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Overdue') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in d.tasks.overdue" :key="t.name"
                  class="border-t border-outline-gray-1" :class="t.reference_docname ? 'cursor-pointer hover:bg-surface-gray-1' : ''"
                  @click="goRef(t)">
                  <td class="py-1.5 font-medium text-ink-gray-8">{{ t.title }}</td>
                  <td class="py-1.5 text-ink-gray-5">{{ t.due_date ? formatDate(t.due_date) : '—' }}</td>
                  <td class="py-1.5 text-right"><Badge theme="red" :label="`${t.days}d`" variant="subtle" /></td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('Nothing overdue')" />
          </Card>
        </div>

        <Card class="mb-8">
          <template #title>
            <div class="flex items-center justify-between">
              <span>{{ __('Pending Technical Team Responses') }}</span>
              <Badge v-if="d.tasks.pending_tech_count" theme="orange" :label="String(d.tasks.pending_tech_count)" variant="subtle" />
            </div>
          </template>
          <table v-if="d.tasks.pending_tech.length" class="w-full text-sm">
            <thead>
              <tr class="text-xs text-ink-gray-5">
                <th class="py-1.5 text-left font-normal">{{ __('Assignment') }}</th>
                <th class="py-1.5 text-left font-normal">{{ __('Account') }}</th>
                <th class="py-1.5 text-right font-normal">{{ __('Elapsed / SLA') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in d.tasks.pending_tech" :key="t.name"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goDeal(t.name)">
                <td class="py-1.5 font-medium text-ink-gray-8">{{ t.name }}</td>
                <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="t.organization_name" size="sm" /><span class="text-ink-gray-8">{{ t.organization_name }}</span></span></td>
                <td class="py-1.5 text-right"><Badge :theme="slaTheme(t.elapsed_hours)" :label="`${fmtElapsed(t.elapsed_hours)} · ${slaLabel(t.elapsed_hours)}`" variant="subtle" /></td>
              </tr>
            </tbody>
          </table>
          <Empty v-else :text="__('No pending technical responses')" />
        </Card>

        <!-- MY ACCOUNTS -->
        <SectionLabel :label="__('My Accounts')" />
        <div class="mb-8 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
          <Card :title="__('My Accounts — Last Contact')">
            <table v-if="d.accounts.last_contact.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Last Contact') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.accounts.last_contact" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                  <td class="py-1.5 text-right">
                    <Badge v-if="a.contact_days > 30" theme="red" :label="__('{0}d ago', [a.contact_days])" variant="subtle" />
                    <Badge v-else-if="a.contact_days > 14" theme="orange" :label="__('{0}d ago', [a.contact_days])" variant="subtle" />
                    <span v-else class="text-ink-gray-5">{{ __('{0}d ago', [a.contact_days]) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No accounts assigned to you')" />
          </Card>
          <Card>
            <template #title>
              <div class="flex items-center justify-between">
                <span>{{ __('Dormant — No Order 30+ Days') }}</span>
                <Badge v-if="d.accounts.dormant30_count" theme="red" :label="String(d.accounts.dormant30_count)" variant="subtle" />
              </div>
            </template>
            <table v-if="d.accounts.dormant30.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Organization') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Last Order') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Days') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in d.accounts.dormant30" :key="a.organization"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goOrg(a.organization)">
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="a.organization_name" size="sm" /><span class="text-ink-gray-8">{{ a.organization_name }}</span></span></td>
                  <td class="py-1.5 text-ink-gray-5">{{ formatDate(a.last_order) }}</td>
                  <td class="py-1.5 text-right"><Badge theme="red" :label="`${a.days}d`" variant="subtle" /></td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No dormant accounts')" />
          </Card>
        </div>

        <!-- MY PERFORMANCE -->
        <SectionLabel :label="__('My Performance')" />
        <div class="mb-4 grid grid-cols-1 gap-3.5 sm:grid-cols-3">
          <Tile :icon="LucideIndianRupee" :title="__('Orders This Month')" :value="d.performance.has_orders ? fmtINR(d.performance.orders_this_month) : '—'"
            :sub="d.performance.has_orders ? __('booked to my accounts') : __('order data unavailable')" tone="green" />
          <Tile :icon="LucideArrowLeftRight" :title="__('Lead Conversion Rate')" :value="`${d.performance.lead_conversion_rate}%`"
            :sub="__('{0} of {1} leads', [d.performance.leads_converted, d.performance.leads_assigned])" tone="green" />
          <Tile :icon="LucideTarget" :title="__('Trial Conversion Rate')" :value="`${d.performance.trial_conversion_rate}%`"
            :sub="__('{0} of {1} trials', [d.performance.trials_won, d.performance.trials_total])" tone="green" />
        </div>
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
            <div v-if="r.value" class="whitespace-nowrap text-sm font-semibold text-ink-gray-8">{{ r.value }}</div>
            <span class="text-ink-gray-4">&rarr;</span>
          </div>
          <Empty v-if="!drill.rows.length" :text="__('No records')" />
        </div>
        <div v-if="drill.footer" class="border-t border-outline-gray-2 p-3">
          <Button class="w-full" variant="solid" @click="openDealsFiltered(drill.footer.filters)">{{ drill.footer.label }}</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { SectionLabel, Tile, Card, BarRow, Bars, Empty } from '@/components/Dashboard/ui'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideClock from '~icons/lucide/clock'
import LucideFunnel from '~icons/lucide/funnel'
import LucideIndianRupee from '~icons/lucide/indian-rupee'
import LucideTarget from '~icons/lucide/target'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import { formatDate } from '@/utils'
import { Avatar, Badge, Breadcrumbs, Button, call, createResource } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { viewsStore } from '@/stores/views'

const router = useRouter()
const { getUser } = usersStore()

const goOrg = (name) => name && router.push({ name: 'Organization', params: { organizationId: name } })
const goDeal = (name) => name && router.push({ name: 'Deal', params: { dealId: name } })
function goRef(t) {
  if (t.reference_doctype === 'CRM Deal' && t.reference_docname) goDeal(t.reference_docname)
  else if (t.reference_doctype === 'CRM Lead' && t.reference_docname) router.push({ name: 'Lead', params: { leadId: t.reference_docname } })
}

const dash = createResource({
  url: 'crm.api.ae_dashboard.get_ae_dashboard',
  auto: true,
})
const d = computed(() => dash.data)
const meName = computed(() => (d.value ? getUser(d.value.user).full_name || d.value.user : ''))
const maxStage = computed(() => Math.max(1, ...(d.value?.pipeline.by_stage || []).map((s) => s.count)))

function ratio(v, max) {
  return Math.max(0.02, (v || 0) / max)
}
const slaTheme = (h) => (h < 2 ? 'green' : h < 4 ? 'blue' : h < 24 ? 'orange' : 'red')
const slaLabel = (h) => (h < 2 ? __('Excellent') : h < 8 ? __('Amber') : __('Breach'))
function fmtElapsed(h) {
  return h < 1 ? `${Math.round(h * 60)}m` : `${h.toFixed(1)}h`
}
function fmtINR(v) {
  const n = Math.abs(v || 0)
  if (n >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`
  if (n >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v || 0)
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
function drillStage(stage) {
  drill.value = {
    title: stage,
    subtitle: __('My open deals at this stage'),
    rows: (d.value?.pipeline.deals || [])
      .filter((dl) => dl.stage === stage)
      .map((dl) => ({
        primary: dl.organization_name,
        secondary: [dl.name, dl.category].filter(Boolean).join(' · '),
        value: fmtINR(dl.value),
        to: { name: 'Deal', params: { dealId: dl.name } },
      })),
    footer: { label: __('Open My Deals list'), filters: { deal_owner: d.value.user, status: stage } },
  }
}

// Persist the drilled filters onto the user's standard CRM Deal list view, then open it.
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
    // still open the list even if persisting the filter failed
  }
  router.push({ name: 'Deals' })
}
</script>
