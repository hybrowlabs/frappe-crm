<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Quotations" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="router.push({ name: 'New Quotation' })"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="quotations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Quotation"
  />
  <QuotationsListView
    v-if="quotations.data && rows.length"
    v-model="quotations.data.page_length_count"
    v-model:list="quotations"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: quotations.data.row_count,
      totalCount: quotations.data.total_count,
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
    v-else-if="quotations.data && !rows.length"
    name="Quotations"
    :icon="QuotationIcon"
    :description="__('Quotations you create in ERPNext will appear here.')"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import QuotationsListView from '@/components/ListViews/QuotationsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import QuotationIcon from '~icons/lucide/file-text'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { indicatorClass } from '@/utils/quotation'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Quotation')

// quotations data is loaded in the ViewControls component
const quotations = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !quotations.value?.data?.data ||
    !['list', 'group_by'].includes(quotations.value.data.view_type)
  )
    return []
  return quotations.value.data.data.map((quotation) => {
    let _rows = {}
    quotations.value.data.rows.forEach((row) => {
      _rows[row] = quotation[row]

      let fieldType = quotations.value.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(quotation[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, quotation)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, quotation)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, quotation)
      }

      if (row === 'party_name') {
        _rows[row] = quotation.customer_name || quotation.party_name
      } else if (row === 'status') {
        // ERPNext's displayed status (workflow / Draft / Cancelled / status).
        const indicator = quotation._indicator || { label: quotation.status }
        _rows[row] = {
          label: __(indicator.label),
          color: indicatorClass(indicator.color),
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(quotation[row]),
          timeAgo: __(timeAgo(quotation[row])),
        }
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = quotations.value?.data?.columns || []

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
