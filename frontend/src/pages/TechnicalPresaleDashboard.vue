<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Technical Pre-Sale'), route: { name: 'TechnicalPresaleDashboard' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Technical Pre-Sale Dashboard') }}</h1>
          <Badge theme="gray" variant="subtle" :label="__('CRM Pipeline phase')" />
        </div>
        <div v-if="canSeeTeam" class="flex rounded-lg border border-outline-gray-2 p-0.5 text-sm">
          <button v-for="opt in views" :key="opt.value"
            class="rounded-md px-3 py-1 transition"
            :class="view === opt.value ? 'bg-surface-gray-3 font-medium text-ink-gray-9' : 'text-ink-gray-5'"
            @click="setView(opt.value)">{{ opt.label }}</button>
        </div>
      </div>

      <template v-if="d">
        <!-- RESPONSE TIME -->
        <SectionLabel :label="__('Response Time')" :hint="__('SLA bands · deals with a recorded response')" />
        <div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <div v-for="b in d.response.bands" :key="b.label" class="rounded-lg border border-outline-gray-1 bg-surface-white p-3">
            <div class="mb-1.5 flex items-center gap-1.5">
              <Dot :color="b.theme" /><span class="text-xs text-ink-gray-5">{{ b.label }}</span>
            </div>
            <div class="text-2xl font-semibold text-ink-gray-9">{{ b.count }}</div>
            <div class="text-xs text-ink-gray-4">{{ b.tag }}</div>
          </div>
        </div>

        <div class="mb-6 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Card :title="__('Response Time Distribution')">
            <div class="mb-3 flex h-3 w-full overflow-hidden rounded-full bg-surface-gray-2">
              <div v-for="b in d.response.bands" :key="b.label" :class="bandBg(b.theme)"
                :style="`width: ${pct(b.count, d.response.total)}%`" :title="`${b.label}: ${b.count}`"></div>
            </div>
            <div v-for="b in d.response.bands" :key="b.label" class="mb-1 flex items-center justify-between text-sm">
              <span class="flex items-center gap-2 text-ink-gray-7"><Dot :color="b.theme" />{{ b.label }} · {{ b.tag }}</span>
              <span class="font-medium text-ink-gray-8">{{ b.count }} · {{ pct(b.count, d.response.total) }}%</span>
            </div>
            <Empty v-if="!d.response.total" :text="__('No responses recorded yet')" />
          </Card>
          <div class="flex flex-col gap-3">
            <Tile :title="__('Average Response — {0}', [view === 'my' ? __('Mine') : __('Team')])"
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
          <div class="mb-5 grid grid-cols-2 gap-3">
            <Tile :title="__('My Open Assignments')" :value="String(d.open_assignments.open_count)" :sub="__('awaiting my response')" />
            <Tile :title="__('Overdue — Past 4h')" :value="String(d.open_assignments.overdue_count)" :sub="__('needs immediate action')" tone="red" />
          </div>

          <Card :title="__('My Open Assignments Right Now')" class="mb-6">
            <table v-if="d.open_assignments.open.length" class="w-full text-sm">
              <thead>
                <tr class="text-xs text-ink-gray-5">
                  <th class="py-1.5 text-left font-normal">{{ __('Assignment') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Customer') }}</th>
                  <th class="py-1.5 text-left font-normal">{{ __('Product') }}</th>
                  <th class="py-1.5 text-right font-normal">{{ __('Elapsed / SLA') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="o in d.open_assignments.open" :key="o.name"
                  class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1" @click="goDeal(o.name)">
                  <td class="py-1.5 font-medium text-ink-gray-8">{{ o.name }}</td>
                  <td class="py-1.5"><span class="flex items-center gap-2"><Avatar :label="o.organization_name" size="sm" /><span class="text-ink-gray-8">{{ o.organization_name }}</span></span></td>
                  <td class="py-1.5 text-ink-gray-5">{{ o.product }}</td>
                  <td class="py-1.5 text-right">
                    <Badge :theme="slaTheme(o.elapsed_hours)" :label="`${fmtElapsed(o.elapsed_hours)} · ${slaLabel(o.elapsed_hours)}`" variant="subtle" />
                  </td>
                </tr>
              </tbody>
            </table>
            <Empty v-else :text="__('No open assignments')" />
          </Card>

          <SectionLabel :label="__('Trial Performance')" :hint="__('my trials')" />
          <div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Tile :title="__('Trials I Managed')" :value="String(d.trials.total)" :sub="__('recorded outcome')" />
            <Tile :title="__('Successful')" :value="String(d.trials.first_attempt)" :sub="__('first attempt')" tone="green" />
            <Tile :title="__('Partially Successful')" :value="String(d.trials.partial)" :sub="__('review recommended')" tone="amber" />
            <Tile :title="__('Unsuccessful')" :value="String(d.trials.unsuccessful)" :sub="__('root-cause analysis')" tone="red" />
            <Tile :title="__('My Trial Conversion')" :value="`${d.trials.conversion_rate}%`" :sub="__('{0} of {1} → success', [d.trials.first_attempt, d.trials.total])" tone="green" />
            <Tile :title="__('Avg Trial Duration')" :value="`${d.trials.avg_duration_days} d`" :sub="__('start → outcome')" />
          </div>

          <Card :title="__('Trial Outcome Breakdown')" class="mb-4">
            <div class="mb-3 flex h-3 w-full overflow-hidden rounded-full bg-surface-gray-2">
              <div class="bg-green-500" :style="`width: ${pct(d.trials.first_attempt, d.trials.total)}%`"></div>
              <div class="bg-amber-500" :style="`width: ${pct(d.trials.partial, d.trials.total)}%`"></div>
              <div class="bg-red-500" :style="`width: ${pct(d.trials.unsuccessful, d.trials.total)}%`"></div>
            </div>
            <div class="mb-1 flex items-center justify-between text-sm"><span class="flex items-center gap-2 text-ink-gray-7"><Dot color="green" />{{ __('Successful (first attempt)') }}</span><span class="font-medium text-ink-gray-8">{{ d.trials.first_attempt }}</span></div>
            <div class="mb-1 flex items-center justify-between text-sm"><span class="flex items-center gap-2 text-ink-gray-7"><Dot color="amber" />{{ __('Partially successful') }}</span><span class="font-medium text-ink-gray-8">{{ d.trials.partial }}</span></div>
            <div class="flex items-center justify-between text-sm"><span class="flex items-center gap-2 text-ink-gray-7"><Dot color="red" />{{ __('Unsuccessful') }}</span><span class="font-medium text-ink-gray-8">{{ d.trials.unsuccessful }}</span></div>
            <Empty v-if="!d.trials.total" :text="__('No trials with a recorded outcome')" />
          </Card>
        </template>

        <!-- TEAM VIEW -->
        <template v-else-if="d.team">
          <SectionLabel :label="__('Team View')" :hint="__('head-only visibility')" />
          <Card :title="__('Team Response Time Distribution')" class="mb-6">
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

          <div class="mb-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
            <Card :title="__('Assignments by Sub-Category')">
              <BarRow v-for="s in d.team.by_sub_category" :key="s.label" :label="s.label"
                :value="String(s.count)" :ratio="ratio(s.count, maxSub)" color="blue" />
              <Empty v-if="!d.team.by_sub_category.length" :text="__('No sub-category data')" />
            </Card>
            <div class="flex flex-col gap-3">
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
import { Avatar, Badge, Breadcrumbs, createResource } from 'frappe-ui'
import { computed, h, ref } from 'vue'
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

const bandBg = (theme) => ({ green: 'bg-green-500', blue: 'bg-blue-500', amber: 'bg-amber-500', red: 'bg-red-500' })[theme] || 'bg-surface-gray-4'

// ---- tiny presentational components ----
const SectionLabel = (props) =>
  h('div', { class: 'mb-2 flex items-baseline gap-2' }, [
    h('span', { class: 'text-xs font-medium uppercase tracking-wide text-ink-gray-5' }, props.label),
    props.hint ? h('span', { class: 'text-xs text-ink-gray-4' }, props.hint) : null,
  ])
SectionLabel.props = ['label', 'hint']

const Dot = (props) =>
  h('span', { class: `inline-block h-2 w-2 rounded-full ${{ green: 'bg-green-500', blue: 'bg-blue-500', amber: 'bg-amber-500', red: 'bg-red-500' }[props.color] || 'bg-surface-gray-4'}` })
Dot.props = ['color']

const toneClass = { green: 'text-ink-green-3', red: 'text-ink-red-3', amber: 'text-ink-amber-3' }
const Tile = (props, { attrs }) =>
  h('div', { ...attrs, class: 'rounded-lg border border-outline-gray-1 bg-surface-white p-4' + (attrs.onClick ? ' cursor-pointer transition hover:border-outline-gray-3' : '') }, [
    h('div', { class: 'mb-1 flex items-center justify-between text-xs text-ink-gray-5' }, [props.title, attrs.onClick ? h('span', { class: 'text-ink-gray-4' }, '→') : null]),
    h('div', { class: `text-2xl font-semibold ${toneClass[props.tone] || 'text-ink-gray-9'}` }, props.value),
    h('div', { class: 'mt-0.5 text-xs text-ink-gray-4' }, props.sub),
  ])
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
