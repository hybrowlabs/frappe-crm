<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Sales Orders" />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="salesOrders"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Sales Order"
  />
  <SalesOrdersListView
    v-if="salesOrders.data && rows.length"
    v-model="salesOrders.data.page_length_count"
    v-model:list="salesOrders"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: salesOrders.data.row_count,
      totalCount: salesOrders.data.total_count,
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
    v-else-if="salesOrders.data && !rows.length"
    name="Sales Orders"
    :icon="SalesOrderIcon"
    :description="__('Sales Orders you create from a CRM order will appear here.')"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import SalesOrdersListView from '@/components/ListViews/SalesOrdersListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import SalesOrderIcon from '~icons/lucide/package-check'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { indicatorClass } from '@/utils/quotation'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Sales Order')

// sales orders data is loaded in the ViewControls component
const salesOrders = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !salesOrders.value?.data?.data ||
    !['list', 'group_by'].includes(salesOrders.value.data.view_type)
  )
    return []
  return salesOrders.value.data.data.map((order) => {
    let _rows = {}
    salesOrders.value.data.rows.forEach((row) => {
      _rows[row] = order[row]

      let fieldType = salesOrders.value.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(order[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, order)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, order)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, order)
      }

      if (row === 'customer') {
        _rows[row] = order.customer_name || order.customer
      } else if (row === 'status') {
        // The order state (Draft / Confirmed / Dispatched / Delivered ...).
        const indicator = order._indicator || { label: order.status }
        _rows[row] = {
          label: __(indicator.label),
          color: indicatorClass(indicator.color),
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(order[row]),
          timeAgo: __(timeAgo(order[row])),
        }
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = salesOrders.value?.data?.columns || []

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
