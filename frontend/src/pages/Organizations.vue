<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Organizations" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="organizationsListView?.customListActions"
        :actions="organizationsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showOrganizationModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="organizations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Organization"
  >
    <template #prefix-filters>
      <div class="m-1 min-w-40">
        <FormControl
          type="select"
          v-model="signal"
          :options="signalOptions"
          :placeholder="__('Signal')"
        />
      </div>
    </template>
  </ViewControls>
  <OrganizationsListView
    v-if="organizations.data && rows.length"
    ref="organizationsListView"
    v-model="organizations.data.page_length_count"
    v-model:list="organizations"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: organizations.data.row_count,
      totalCount: organizations.data.total_count,
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
    v-else-if="organizations.data && !rows.length"
    name="Organizations"
    :icon="OrganizationsIcon"
  />
  <OrganizationModal
    v-if="showOrganizationModal"
    v-model="showOrganizationModal"
  />
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo, website } from '@/utils'
import { ref, computed } from 'vue'
import EmptyState from '../components/ListViews/EmptyState.vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Organization')

const organizationsListView = ref(null)
const showOrganizationModal = ref(false)

const signalOptions = [
  { label: __('All'), value: 'all' },
  { label: __('Ordering below average'), value: 'below' },
  { label: __('Declining order value'), value: 'declining' },
  { label: __('No order 20–29 days'), value: 'no_order_20_29' },
  { label: __('Dormant 30+ days'), value: 'dormant' },
]

function daysAgo(days) {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

// Derived from the live filters so it stays in sync on reload and resets to
// 'all' when filters are cleared elsewhere.
const signal = computed({
  get() {
    const f = organizations.value?.params?.filters || {}
    if (f.ordering_below_average) return 'below'
    if (f.declining_order_value) return 'declining'
    const lo = f.last_order
    if (Array.isArray(lo) && String(lo[0]).toLowerCase() === 'between') {
      return lo[1]?.[0] === '1900-01-01' ? 'dormant' : 'no_order_20_29'
    }
    return 'all'
  },
  set(value) {
    const filters = { ...(organizations.value?.params?.filters || {}) }
    delete filters.ordering_below_average
    delete filters.declining_order_value
    delete filters.last_order
    if (value === 'below') filters.ordering_below_average = 1
    else if (value === 'declining') filters.declining_order_value = 1
    else if (value === 'no_order_20_29')
      filters.last_order = ['between', [daysAgo(29), daysAgo(20)]]
    else if (value === 'dormant')
      filters.last_order = ['between', ['1900-01-01', daysAgo(30)]]
    viewControls.value?.updateFilter(filters)
  },
})

// organizations data is loaded in the ViewControls component
const organizations = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !organizations.value?.data?.data ||
    !['list', 'group_by'].includes(organizations.value.data.view_type)
  )
    return []
  return organizations.value?.data.data.map((organization) => {
    let _rows = {}
    organizations.value?.data.rows.forEach((row) => {
      _rows[row] = organization[row]

      let fieldType = organizations.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          organization[row],
          '',
          true,
          fieldType == 'Datetime',
        )
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, organization)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, organization)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, organization)
      }

      if (row === 'organization_name') {
        _rows[row] = {
          label: organization.organization_name,
          logo: organization.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = website(organization.website)
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(organization[row]),
          timeAgo: __(timeAgo(organization[row])),
        }
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = organizations.value?.data?.columns || []

  // Set align right for last column
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
</script>
