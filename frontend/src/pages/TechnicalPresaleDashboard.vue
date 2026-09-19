<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Dashboards'), route: { name: 'Dashboard' } }, { label: __('Technical Pre-Sale'), route: { name: 'TechnicalPresaleDashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto pa-page">
      <div class="pa-page-h">
        <h1 class="pa-h1">{{ __('Technical Pre-Sale Dashboard') }} <span class="pa-tag">{{ __('CRM Pipeline phase') }}</span></h1>
        <div v-if="canSeeTeam" class="pa-seg" role="group" :aria-label="__('Scope')">
          <button v-for="opt in views" :key="opt.value"
            :class="{ on: view === opt.value }" :aria-pressed="view === opt.value"
            @click="setView(opt.value)">{{ opt.label }}</button>
        </div>
      </div>

      <template v-if="d">
        <!-- RESPONSE TIME -->
        <SectionLabel :label="__('Response Time')" :hint="__('SLA bands · deals with a recorded response')" />
        <div class="mb-3.5 grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-6">
          <div v-for="b in d.response.bands" :key="b.label" class="pa-kpi sla" :style="`--c: ${bandColor(b.theme)}`">
            <div class="pa-body">
              <div class="pa-l"><Dot :color="b.theme" class="!mr-0" />{{ b.label }}</div>
              <div class="pa-v">{{ b.count }}</div>
              <div class="pa-s">{{ b.tag }}</div>
            </div>
          </div>
        </div>

        <div class="mb-8 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
          <Card :title="__('Response Time Distribution')">
            <div class="pa-stacked">
              <div v-for="b in d.response.bands" :key="b.label" :class="bandBg(b.theme)"
                :style="`width: ${pct(b.count, d.response.total)}%`" :title="`${b.label}: ${b.count}`"></div>
            </div>
            <div v-for="b in d.response.bands" :key="b.label" class="pa-legend-row">
              <span class="flex items-center gap-2 text-ink-gray-7"><Dot :color="b.theme" />{{ b.label }} · {{ b.tag }}</span>
              <span class="font-medium text-ink-gray-8">{{ b.count }} · {{ pct(b.count, d.response.total) }}%</span>
            </div>
            <Empty v-if="!d.response.total" :text="__('No responses recorded yet')" />
          </Card>
          <div class="flex flex-col gap-3.5">
            <Tile :icon="LucideClock" :title="__('Average Response — {0}', [view === 'my' ? __('Mine') : __('Team')])"
              :value="fmtDuration(d.response.avg_seconds)" :sub="__('assignment → recommendation')" tone="green" />
            <Card :title="__('SLA Escalation Ladder')">
              <div class="flex items-center justify-between border-b border-outline-gray-1 py-1.5 text-sm">
                <span class="flex items-center gap-2"><Dot color="green" />{{ __('< 2h Excellent') }}</span><span class="text-ink-gray-5">{{ __('Technical person') }}</span>
              </div>
              <div class="flex items-center justify-between border-b border-outline-gray-1 py-1.5 text-sm">
                <span class="flex items-center gap-2"><Dot color="amber" />{{ __('4–8h Amber') }}</span><span class="text-ink-gray-5">{{ __('Head notified') }}</span>
              </div>
              <div class="flex items-center justify-between border-b border-outline-gray-1 py-1.5 text-sm">
                <span class="flex items-center gap-2"><Dot color="red" />{{ __('24–48h Breach') }}</span><span class="text-ink-gray-5">{{ __('Sales Manager') }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 text-sm">
                <span class="flex items-center gap-2"><Dot color="red" />{{ __('> 48h Critical') }}</span><span class="text-ink-gray-5">{{ __('Auto-escalate') }}</span>
              </div>
            </Card>
          </div>
        </div>

        <!-- MY VIEW -->
        <template v-if="view === 'my'">
          <SectionLabel :label="__('Open Assignments')" />
          <div class="mb-3.5 grid grid-cols-2 gap-3.5">
            <Tile :icon="LucideInbox" :title="__('My Open Assignments')" :value="String(d.open_assignments.open_count)" :sub="__('awaiting my response')" />
            <Tile :icon="LucideTriangleAlert" :title="__('Overdue — Past 4h')" :value="String(d.open_assignments.overdue_count)" :sub="__('needs immediate action')" tone="red" />
          </div>

          <Card :title="__('My Open Assignments Right Now')" class="mb-8">
            <div v-if="d.open_assignments.open.length" class="overflow-x-auto">
              <table class="w-full min-w-[860px] text-sm">
                <thead>
                  <tr class="text-xs text-ink-gray-5">
                    <th class="py-1.5 text-left font-normal">{{ __('Deal') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Customer') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Product') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Started') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Communication') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Escalation') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('Waiting / SLA') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('Action') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="o in d.open_assignments.open" :key="o.name"
                    class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goDeal(o.name)">
                    <td class="py-2 pr-3 font-medium text-ink-gray-8">{{ o.name }}</td>
                    <td class="py-2 pr-3">
                      <span class="flex items-center gap-2">
                        <Avatar :label="o.organization_name" size="sm" />
                        <span class="text-ink-gray-8">{{ o.organization_name }}</span>
                      </span>
                    </td>
                    <td class="py-2 pr-3 text-ink-gray-5">{{ o.product }}</td>
                    <td class="py-2 pr-3 text-ink-gray-5">{{ fmtDate(o.evaluation_start) }}</td>
                    <td class="py-2 pr-3 text-ink-gray-5">{{ o.communication_status }}</td>
                    <td class="py-2 pr-3 text-ink-gray-7">{{ escalationLabel(o.elapsed_hours) }}</td>
                    <td class="py-2 pr-3 text-right">
                      <Badge :theme="slaTheme(o.elapsed_hours)" :label="`${fmtElapsed(o.elapsed_hours)} · ${slaLabel(o.elapsed_hours)}`" variant="subtle" />
                    </td>
                    <td class="py-2 text-right text-ink-blue-3">{{ __('Open deal') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <Empty v-else :text="__('No open assignments')" />
          </Card>

          <SectionLabel :label="__('Trial Performance')" :hint="__('my trials')" />
          <div class="mb-3.5 grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-6">
            <Tile :icon="LucideFlaskConical" :title="__('Trials I Managed')" :value="String(d.trials.total)" :sub="__('recorded outcome')" />
            <Tile :icon="LucideCircleCheck" :title="__('Successful')" :value="String(d.trials.first_attempt)" :sub="__('first attempt')" tone="green" />
            <Tile :icon="LucideContrast" :title="__('Partially Successful')" :value="String(d.trials.partial)" :sub="__('review recommended')" tone="amber" />
            <Tile :icon="LucideCircleX" :title="__('Unsuccessful')" :value="String(d.trials.unsuccessful)" :sub="__('root-cause analysis')" tone="red" />
            <Tile :icon="LucidePercent" :title="__('My Trial Conversion')" :value="`${d.trials.conversion_rate}%`" :sub="__('{0} of {1} → success', [d.trials.first_attempt, d.trials.total])" tone="green" />
            <Tile :icon="LucideCalendar" :title="__('Avg Trial Duration')" :value="`${d.trials.avg_duration_days} d`" :sub="__('start → outcome')" />
          </div>

          <Card :title="__('Trial Outcome Breakdown')" class="mb-4">
            <div class="pa-stacked">
              <div class="bg-green-500" :style="`width: ${pct(d.trials.first_attempt, d.trials.total)}%`"></div>
              <div class="bg-amber-500" :style="`width: ${pct(d.trials.partial, d.trials.total)}%`"></div>
              <div class="bg-red-500" :style="`width: ${pct(d.trials.unsuccessful, d.trials.total)}%`"></div>
            </div>
            <div class="pa-legend-row"><span class="flex items-center gap-2 text-ink-gray-7"><Dot color="green" />{{ __('Successful (first attempt)') }}</span><span class="font-medium text-ink-gray-8">{{ d.trials.first_attempt }}</span></div>
            <div class="pa-legend-row"><span class="flex items-center gap-2 text-ink-gray-7"><Dot color="amber" />{{ __('Partially successful') }}</span><span class="font-medium text-ink-gray-8">{{ d.trials.partial }}</span></div>
            <div class="pa-legend-row"><span class="flex items-center gap-2 text-ink-gray-7"><Dot color="red" />{{ __('Unsuccessful') }}</span><span class="font-medium text-ink-gray-8">{{ d.trials.unsuccessful }}</span></div>
            <Empty v-if="!d.trials.total" :text="__('No trials with a recorded outcome')" />
          </Card>
        </template>

        <!-- TEAM VIEW -->
        <template v-else-if="d.team">
          <SectionLabel :label="__('Team View')" :hint="__('head-only visibility')" />

          <div class="mb-3.5 grid grid-cols-2 gap-3.5">
            <Tile :icon="LucideInbox" :title="__('Team Open Assignments')" :value="String(d.open_assignments.open_count)" :sub="__('pending on technical person')" />
            <Tile :icon="LucideTriangleAlert" :title="__('Overdue — Past 4h')" :value="String(d.open_assignments.overdue_count)" :sub="__('needs immediate action')" tone="red" />
          </div>

          <Card :title="__('All Open Technical Assignments')" class="mb-8">
            <div v-if="d.open_assignments.open.length" class="overflow-x-auto">
              <table class="w-full min-w-[980px] text-sm">
                <thead>
                  <tr class="text-xs text-ink-gray-5">
                    <th class="py-1.5 text-left font-normal">{{ __('Deal') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Customer') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Product') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Technical Person') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Started') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Communication') }}</th>
                    <th class="py-1.5 text-left font-normal">{{ __('Escalation') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('Waiting / SLA') }}</th>
                    <th class="py-1.5 text-right font-normal">{{ __('Action') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="o in d.open_assignments.open" :key="o.name"
                    class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goDeal(o.name)">
                    <td class="py-2 pr-3 font-medium text-ink-gray-8">{{ o.name }}</td>
                    <td class="py-2 pr-3">
                      <span class="flex items-center gap-2">
                        <Avatar :label="o.organization_name" size="sm" />
                        <span class="text-ink-gray-8">{{ o.organization_name }}</span>
                      </span>
                    </td>
                    <td class="py-2 pr-3 text-ink-gray-5">{{ o.product }}</td>
                    <td class="py-2 pr-3 text-ink-gray-7">{{ engName(o.tech_member) }}</td>
                    <td class="py-2 pr-3 text-ink-gray-5">{{ fmtDate(o.evaluation_start) }}</td>
                    <td class="py-2 pr-3 text-ink-gray-5">{{ o.communication_status }}</td>
                    <td class="py-2 pr-3 text-ink-gray-7">{{ escalationLabel(o.elapsed_hours) }}</td>
                    <td class="py-2 pr-3 text-right">
                      <Badge :theme="slaTheme(o.elapsed_hours)" :label="`${fmtElapsed(o.elapsed_hours)} · ${slaLabel(o.elapsed_hours)}`" variant="subtle" />
                    </td>
                    <td class="py-2 text-right text-ink-blue-3">{{ __('Open deal') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <Empty v-else :text="__('No open technical assignments')" />
          </Card>

          <Card :title="__('Team Response Time Distribution')" class="mb-8">
            <table v-if="d.team.team_response.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Engineer') }}</th>
                  <th class="py-1.5 text-center font-normal">{{ __('< 2h') }}</th>
                  <th class="py-1.5 text-center font-normal">{{ __('2–8h') }}</th>
                  <th class="py-1.5 text-center font-normal">{{ __('> 8h') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Avg') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in d.team.team_response" :key="e.engineer" class="border-t border-outline-gray-1">
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="engName(e.engineer)" size="sm" /><span class="text-ink-gray-8">{{ engName(e.engineer) }}</span></span></td>
                  <td class="py-1.5 text-center font-semibold text-ink-green-3">{{ e.fast }}</td>
                  <td class="py-1.5 text-center text-ink-gray-5">{{ e.mid }}</td>
                  <td class="py-1.5 text-center" :class="e.slow ? 'font-semibold text-ink-red-3' : 'text-ink-gray-5'">{{ e.slow }}</td>
                  <td class="py-1.5 text-right"><Badge :theme="slaTheme(e.avg_seconds / 3600)" :label="fmtDuration(e.avg_seconds)" variant="subtle" /></td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No team response data')" />
          </Card>

          <div class="mb-4 grid grid-cols-1 gap-3.5 lg:grid-cols-2">
            <Card :title="__('Assignments by Sub-Category')">
              <Bars>
                <BarRow v-for="s in d.team.by_sub_category" :key="s.label" :label="s.label"
                  :value="String(s.count)" :ratio="ratio(s.count, maxSub)" color="blue" />
              </Bars>
              <Empty v-if="!d.team.by_sub_category.length" :text="__('No sub-category data')" />
            </Card>
            <div class="flex flex-col gap-3.5">
              <Card :title="__('Trial Conversion — Ranked')">
                <table v-if="d.team.conv_by_engineer.length" class="w-full text-sm">
                  <tbody>
                    <tr v-for="(e, i) in d.team.conv_by_engineer" :key="e.engineer" class="border-t border-outline-gray-1 first:border-0">
                      <td class="py-1.5 pr-2 text-ink-gray-4">{{ i + 1 }}</td>
                      <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="engName(e.engineer)" size="sm" /><span class="text-ink-gray-8">{{ engName(e.engineer) }}</span></span></td>
                      <td class="py-1.5 text-right"><Badge :theme="e.rate >= 65 ? 'green' : e.rate >= 50 ? 'orange' : 'red'" :label="`${e.rate}%`" variant="subtle" /></td>
                    </tr>
                  </tbody>
                </table>
                <Empty v-else :text="__('No trial data')" />
              </Card>
              <Card :title="__('Avg Response Time — Ranked')">
                <table v-if="d.team.resp_by_engineer.length" class="w-full text-sm">
                  <tbody>
                    <tr v-for="(e, i) in d.team.resp_by_engineer" :key="e.engineer" class="border-t border-outline-gray-1 first:border-0">
                      <td class="py-1.5 pr-2 text-ink-gray-4">{{ i + 1 }}</td>
                      <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="engName(e.engineer)" size="sm" /><span class="text-ink-gray-8">{{ engName(e.engineer) }}</span></span></td>
                      <td class="py-1.5 text-right"><Badge :theme="slaTheme(e.avg_seconds / 3600)" :label="fmtDuration(e.avg_seconds)" variant="subtle" /></td>
                    </tr>
                  </tbody>
                </table>
                <Empty v-else :text="__('No response data')" />
              </Card>
            </div>
          </div>
        </template>
      </template>

      <div v-else class="py-20 text-center text-sm text-ink-gray-4">{{ __('Loading…') }}</div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { SectionLabel, Tile, Card, BarRow, Bars, Empty, Dot } from '@/components/Dashboard/ui'
import LucideCalendar from '~icons/lucide/calendar'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideCircleX from '~icons/lucide/circle-x'
import LucideClock from '~icons/lucide/clock'
import LucideContrast from '~icons/lucide/contrast'
import LucideFlaskConical from '~icons/lucide/flask-conical'
import LucideInbox from '~icons/lucide/inbox'
import LucidePercent from '~icons/lucide/percent'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import { Avatar, Badge, Breadcrumbs, createResource } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usersStore } from '@/stores/users'

const router = useRouter()
const { getUser, isTechnicalHead } = usersStore()

const goDeal = (name) => name && router.push({ name: 'Deal', params: { dealId: name } })

// The Team (Head) view is head-only per spec — only a Technical Head (or admin)
// sees the toggle; everyone else is locked to My View.
const canSeeTeam = computed(() => isTechnicalHead())
const views = [
  { value: 'my', label: __('My View') },
  { value: 'team', label: __('Team (Head)') },
]
const view = ref('my')
function setView(v) {
  if (v === view.value) return
  if (v === 'team' && !canSeeTeam.value) return
  view.value = v
  dash.reload({ view: v })
}

function engName(email) {
  if (!email) return __('Unassigned')
  return getUser(email).full_name || email
}

const dash = createResource({
  url: 'crm.api.technical_presale_dashboard.get_technical_presale_dashboard',
  params: { view: view.value },
  auto: true,
})
const d = computed(() => dash.data)

const maxSub = computed(() => Math.max(1, ...(d.value?.team?.by_sub_category || []).map((s) => s.count)))

function pct(v, total) {
  return total ? Math.round((v / total) * 100) : 0
}
function ratio(v, max) {
  return Math.max(0.02, (v || 0) / max)
}
const slaTheme = (h) => (h < 2 ? 'green' : h < 4 ? 'blue' : h < 24 ? 'orange' : 'red')
const slaLabel = (h) => (h < 2 ? __('Excellent') : h < 4 ? __('Acceptable') : h < 8 ? __('Amber') : h < 24 ? __('Amber/Red') : h < 48 ? __('Breach') : __('Critical'))
const escalationLabel = (h) => (h < 4 ? __('Technical person') : h < 24 ? __('Head') : h < 48 ? __('Sales Manager') : __('Auto-escalate'))
function fmtElapsed(h) {
  return h < 1 ? `${Math.round(h * 60)}m` : `${h.toFixed(1)}h`
}
function fmtDuration(seconds) {
  const s = seconds || 0
  if (!s) return '—'
  const hours = s / 3600
  if (hours >= 1) return `${hours.toFixed(1)} h`
  return `${Math.round(s / 60)} m`
}
function fmtDate(value) {
  if (!value) return '—'
  return String(value).slice(0, 10)
}

const bandColor = (theme) => ({ green: 'var(--ink-green-3)', blue: 'var(--ink-blue-3)', amber: 'var(--ink-amber-3)', red: 'var(--ink-red-3)' })[theme] || 'var(--outline-gray-3)'
const bandBg = (theme) => ({ green: 'bg-green-500', blue: 'bg-blue-500', amber: 'bg-amber-500', red: 'bg-red-500' })[theme] || 'bg-surface-gray-4'
</script>
