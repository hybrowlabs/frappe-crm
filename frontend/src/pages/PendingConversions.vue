<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          {
            label: __('Pending Conversions'),
            route: { name: 'PendingConversions' },
          },
        ]"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="leads"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Lead"
    :filters="{ pending_verticals: ['is', 'set'] }"
    :options="{
      allowedViews: ['list'],
      defaultViewName: 'Pending Conversions',
    }"
  />
  <LeadsListView
    v-if="leads.data && rows.length"
    ref="leadsListView"
    v-model="leads.data.page_length_count"
    v-model:list="leads"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: leads.data.row_count,
      totalCount: leads.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="leads.data && !rows.length"
    name="Pending Conversions"
    :icon="ConvertIcon"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import ConvertIcon from '@/components/Icons/ConvertIcon.vue'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { viewsStore } from '@/stores/views'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { Breadcrumbs } from 'frappe-ui'
import { ref, computed, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { getPublicViews } = viewsStore()

// Load the seeded "Pending Conversions" saved view (columns + filters) via
// the stock view mechanism — same as clicking a public view on the Leads page.
watchEffect(() => {
  if (route.query.view) return
  const view = getPublicViews().find(
    (v) => v.label === 'Pending Conversions' && v.dt === 'CRM Lead',
  )
  if (view) {
    router.replace({ query: { ...route.query, view: view.name } })
  }
})

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Lead')
const { getUser } = usersStore()
const { getLeadStatus } = statusesStore()

const leadsListView = ref(null)

// leads data is loaded in the ViewControls component
const leads = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// Rows — same parsing as pages/Leads.vue (list view only)
const rows = computed(() => {
  if (!leads.value?.data?.data) return []
  return parseRows(leads.value?.data.data, leads.value.data.columns)
})

const columns = computed(() => {
  let _columns = leads.value?.data?.columns || []

  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

function parseRows(rows, columns = []) {
  return rows.map((lead) => {
    let _rows = {}
    leads.value?.data.rows.forEach((row) => {
      _rows[row] = lead[row]

      let fieldType = columns?.find((col) => (col.key || col.value) == row)
        ?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(lead[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, lead)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, lead)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, lead)
      }

      if (row == 'lead_name') {
        _rows[row] = {
          label: lead.lead_name,
          image: lead.image,
          image_label: lead.first_name,
        }
      } else if (row == 'organization') {
        _rows[row] = lead.organization
      } else if (row === 'website') {
        _rows[row] = website(lead.website)
      } else if (row == 'status') {
        _rows[row] = {
          label: lead.status,
          color: getLeadStatus(lead.status)?.color,
        }
      } else if (row == 'sla_status') {
        let value = lead.sla_status
        let tooltipText = value
        let color =
          lead.sla_status == 'Failed'
            ? 'red'
            : lead.sla_status == 'Fulfilled'
              ? 'green'
              : 'orange'
        if (value == 'First Response Due' || value == 'Rolling Response Due') {
          value = __(timeAgo(lead.response_by))
          tooltipText = formatDate(lead.response_by)
          if (new Date(lead.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'lead_owner') {
        _rows[row] = {
          label: lead.lead_owner && getUser(lead.lead_owner).full_name,
          ...(lead.lead_owner && getUser(lead.lead_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(lead._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(lead[row]),
          timeAgo: __(timeAgo(lead[row])),
        }
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row,
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: lead[field] ? formatDate(lead[field]) : '',
          timeAgo: lead[row]
            ? row == 'first_response_time'
              ? formatTime(lead[row])
              : __(timeAgo(lead[row]))
            : '',
        }
      }
    })
    _rows['_email_count'] = lead._email_count
    _rows['_note_count'] = lead._note_count
    _rows['_task_count'] = lead._task_count
    _rows['_comment_count'] = lead._comment_count
    return _rows
  })
}
</script>
