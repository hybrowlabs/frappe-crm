<template>
  <Dialog v-model="show" :options="{ title: __('Import Leads'), size: '4xl' }">
    <template #body-content>
      <!-- Tab Switcher -->
      <div class="mb-5 flex w-fit gap-1 rounded-lg bg-surface-gray-2 p-1">
        <button
          v-for="tab in tabs"
          :key="tab.name"
          :class="[
            'flex items-center gap-2 rounded px-4 py-2 text-sm font-medium transition-all duration-200',
            activeTab === tab.name
              ? 'bg-surface-white text-ink-gray-9 shadow-sm'
              : 'text-ink-gray-5 hover:text-ink-gray-7',
          ]"
          @click="activeTab = tab.name"
        >
          <FeatherIcon :name="tab.icon" class="h-4 w-4" />
          {{ tab.label }}
        </button>
      </div>

      <!-- Export Template Tab -->
      <div v-if="activeTab === 'export'">
        <p class="mb-4 text-p-sm text-ink-gray-5">
          {{
            __(
              'Select the fields you want in the import template, then download as CSV.',
            )
          }}
        </p>

        <!-- Search + controls -->
        <div class="mb-3 flex items-center justify-between gap-4">
          <FormControl
            v-model="fieldSearch"
            type="text"
            :placeholder="__('Search fields...')"
            class="w-64"
          />
          <div class="flex items-center gap-3">
            <span class="text-xs tabular-nums text-ink-gray-4">
              {{ selectedFields.length }}/{{ availableFields.length }}
              {{ __('selected') }}
            </span>
            <Button
              variant="subtle"
              size="sm"
              :label="allSelected ? __('Deselect All') : __('Select All')"
              @click="toggleSelectAll"
            />
          </div>
        </div>

        <!-- Field grid -->
        <div
          class="max-h-72 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-white"
        >
          <div class="grid grid-cols-3 gap-0">
            <label
              v-for="field in filteredFields"
              :key="field.fieldname"
              class="flex cursor-pointer items-center gap-2.5 border-b border-outline-gray-1 px-3 py-2.5 transition-colors hover:bg-surface-gray-1"
            >
              <input
                type="checkbox"
                :checked="selectedFields.includes(field.fieldname)"
                class="h-3.5 w-3.5 rounded-sm border-outline-gray-3 text-surface-gray-7"
                @change="toggleField(field.fieldname)"
              />
              <span class="truncate text-sm text-ink-gray-7">
                {{ field.label }}
              </span>
            </label>
          </div>
        </div>

        <!-- Download -->
        <div class="mt-5 flex justify-end">
          <Button
            variant="solid"
            :label="__('Download Template')"
            :disabled="!selectedFields.length"
            @click="downloadTemplate"
          >
            <template #prefix>
              <FeatherIcon name="download" class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </div>

      <!-- Import Tab -->
      <div v-if="activeTab === 'import'">
        <!-- Upload Area (when no file selected) -->
        <div v-if="!uploadedFile && !importDocName">
          <p class="mb-4 text-p-sm text-ink-gray-5">
            {{ __('Upload a CSV or XLSX file to import leads into the system.') }}
          </p>

          <div
            class="relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-gray-3 bg-surface-gray-1 px-6 py-12 transition-colors"
            :class="{ 'border-outline-gray-4 bg-surface-gray-2': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <div
              class="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-surface-gray-2"
            >
              <FeatherIcon name="upload-cloud" class="h-7 w-7 text-ink-gray-4" />
            </div>
            <p class="mb-1 text-sm font-medium text-ink-gray-7">
              {{ __('Drag and drop your file here') }}
            </p>
            <p class="mb-4 text-xs text-ink-gray-4">
              {{ __('Supports CSV and XLSX files') }}
            </p>
            <Button
              variant="subtle"
              :label="__('Browse Files')"
              @click="fileInput.click()"
            />
            <input
              ref="fileInput"
              type="file"
              accept=".csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
              class="hidden"
              @change="handleFileSelect"
            />
          </div>
        </div>

        <!-- File Selected → ready to import -->
        <div v-else-if="uploadedFile && !importDocName">
          <div
            class="mb-4 flex items-center gap-3 rounded-lg border border-outline-gray-2 bg-surface-white p-4"
          >
            <div
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-gray-2"
            >
              <FeatherIcon name="file-text" class="h-5 w-5 text-ink-gray-5" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-ink-gray-8">
                {{ uploadedFile.name }}
              </p>
              <p class="text-xs text-ink-gray-4">
                {{ formatFileSize(uploadedFile.size) }}
              </p>
            </div>
            <Button variant="ghost" icon="x" class="w-7" @click="clearFile" />
          </div>

          <ErrorMessage v-if="importError" class="mb-4" :message="importError" />

          <div class="flex justify-end gap-2">
            <Button :label="__('Cancel')" @click="clearFile" />
            <Button
              variant="solid"
              :label="__('Start Import')"
              :loading="isImporting"
              @click="startImport"
            >
              <template #prefix>
                <FeatherIcon name="upload" class="h-4 w-4" />
              </template>
            </Button>
          </div>
        </div>

        <!-- Import in Progress / Complete -->
        <div v-else-if="importDocName">
          <div
            class="flex flex-col items-center justify-center rounded-xl border border-outline-gray-2 bg-surface-white px-6 py-10"
          >
            <!-- In progress -->
            <div v-if="importStatus === 'In Progress'" class="text-center">
              <div class="mb-4 flex justify-center">
                <LoadingIndicator class="h-10 w-10 text-ink-gray-5" />
              </div>
              <p class="text-sm font-medium text-ink-gray-7">
                {{ __('Import in progress...') }}
              </p>
              <p class="mt-1 text-xs text-ink-gray-4">
                {{ __('Please wait while your data is being imported.') }}
              </p>
            </div>

            <!-- Success -->
            <div v-else-if="importStatus === 'Success'" class="text-center">
              <div
                class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-surface-green-2"
              >
                <FeatherIcon
                  name="check-circle"
                  class="h-7 w-7 text-ink-green-3"
                />
              </div>
              <p class="text-sm font-medium text-ink-gray-9">
                {{ __('Import Successful!') }}
              </p>
              <p class="mt-1 text-xs text-ink-gray-4">
                {{ importMessage || __('Your data has been imported.') }}
              </p>
              <div class="mt-5 flex justify-center gap-2">
                <Button :label="__('Import Another')" @click="resetImport" />
                <Button
                  variant="solid"
                  :label="__('Close')"
                  @click="show = false"
                />
              </div>
            </div>

            <!-- Error / Partial -->
            <div
              v-else-if="
                importStatus === 'Error' || importStatus === 'Partial Success'
              "
              class="w-full text-center"
            >
              <div
                class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full"
                :class="
                  importStatus === 'Error'
                    ? 'bg-surface-red-2'
                    : 'bg-surface-amber-1'
                "
              >
                <FeatherIcon
                  :name="importStatus === 'Error' ? 'x-circle' : 'alert-triangle'"
                  class="h-7 w-7"
                  :class="
                    importStatus === 'Error'
                      ? 'text-ink-red-3'
                      : 'text-ink-amber-3'
                  "
                />
              </div>
              <p class="text-sm font-medium text-ink-gray-9">
                {{
                  importStatus === 'Error'
                    ? __('Import Failed')
                    : __('Partial Import')
                }}
              </p>
              <p class="mx-auto mt-1 max-w-md text-xs text-ink-gray-4">
                {{ importMessage }}
              </p>

              <!-- Import Logs -->
              <div v-if="importLogs.length" class="mt-6 w-full text-left">
                <p
                  class="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-gray-5"
                >
                  {{ __('Import Logs') }}
                </p>
                <div
                  class="max-h-48 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3"
                >
                  <div
                    v-for="(log, idx) in importLogs"
                    :key="idx"
                    class="mb-3 border-b border-outline-gray-1 pb-3 text-xs last:mb-0 last:border-0 last:pb-0"
                  >
                    <div class="mb-1.5 flex items-center gap-2">
                      <Badge
                        v-if="!log.success"
                        variant="subtle"
                        :theme="getLogTheme(log)"
                        size="sm"
                        :label="getLogStatusLabel(log)"
                      />
                      <FeatherIcon
                        v-else
                        name="check"
                        class="h-3 w-3 text-ink-green-3"
                      />
                      <span
                        v-if="log.docname"
                        class="font-semibold text-ink-gray-9"
                      >
                        {{ log.docname }}
                      </span>
                      <span
                        v-if="log.row_indexes"
                        class="font-medium text-ink-gray-4"
                      >
                        {{ __('Row {0}', [log.row_indexes]) }}
                      </span>
                    </div>
                    <div
                      v-if="log.messages"
                      class="whitespace-pre-wrap leading-relaxed text-ink-gray-7"
                    >
                      {{ parseLogMessages(log.messages) }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-5 flex justify-center gap-2">
                <Button :label="__('Try Again')" @click="resetImport" />
                <Button
                  variant="solid"
                  :label="__('Close')"
                  @click="show = false"
                />
              </div>
            </div>

            <!-- Pending (just created) -->
            <div v-else class="text-center">
              <div class="mb-4 flex justify-center">
                <LoadingIndicator class="h-10 w-10 text-ink-gray-5" />
              </div>
              <p class="text-sm font-medium text-ink-gray-7">
                {{ __('Preparing import...') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FilesUploadHandler from '@/components/FilesUploader/filesUploaderHandler'
import { getMeta } from '@/stores/meta'
import {
  Dialog,
  FeatherIcon,
  LoadingIndicator,
  ErrorMessage,
  Badge,
  call,
} from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const show = defineModel({ type: Boolean })

const activeTab = ref('export')
const fieldSearch = ref('')
const fileInput = ref(null)

const defaultTemplateFields = [
  'first_name',
  'last_name',
  'email',
  'mobile_no',
  'phone',
  'organization',
  'website',
  'source',
  'sub_source',
]
const selectedFields = ref([...defaultTemplateFields])

const tabs = [
  { name: 'export', label: __('Export Template'), icon: 'download' },
  { name: 'import', label: __('Import Data'), icon: 'upload' },
]

// --- Field selection for the template ---
const { getFields } = getMeta('CRM Lead')

const availableFields = computed(() => {
  let fields = getFields() || []
  return fields.filter(
    (f) => f.label && defaultTemplateFields.includes(f.fieldname),
  )
})

const filteredFields = computed(() => {
  if (!fieldSearch.value) return availableFields.value
  let q = fieldSearch.value.toLowerCase()
  return availableFields.value.filter(
    (f) =>
      f.label.toLowerCase().includes(q) ||
      f.fieldname.toLowerCase().includes(q),
  )
})

const allSelected = computed(
  () =>
    availableFields.value.length > 0 &&
    selectedFields.value.length === availableFields.value.length,
)

function toggleSelectAll() {
  selectedFields.value = allSelected.value
    ? []
    : availableFields.value.map((f) => f.fieldname)
}

function toggleField(fieldname) {
  let idx = selectedFields.value.indexOf(fieldname)
  if (idx > -1) {
    selectedFields.value.splice(idx, 1)
  } else {
    selectedFields.value.push(fieldname)
  }
}

// --- CSV template download ---
function downloadTemplate() {
  let fieldDefs = availableFields.value.filter((f) =>
    selectedFields.value.includes(f.fieldname),
  )
  let headers = fieldDefs.map((f) => escapeCSV(f.label))
  let csv = headers.join(',') + '\n'

  let blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  let url = URL.createObjectURL(blob)
  let link = document.createElement('a')
  link.href = url
  link.download = 'CRM_Lead_Import_Template.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function escapeCSV(value) {
  if (!value) return ''
  let str = String(value)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"'
  }
  return str
}

// --- File upload & import ---
const isDragging = ref(false)
const uploadedFile = ref(null)
const isImporting = ref(false)
const importError = ref(null)
const importDocName = ref(null)
const importStatus = ref(null)
const importMessage = ref(null)
const importLogs = ref([])
let pollInterval = null

const validTypes = [
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
]
const validExtensions = ['.csv', '.xlsx', '.xls']

function isValidFile(file) {
  if (!file) return false
  let ext = '.' + file.name.split('.').pop().toLowerCase()
  return validTypes.includes(file.type) || validExtensions.includes(ext)
}

function handleDrop(e) {
  isDragging.value = false
  let file = e.dataTransfer?.files?.[0]
  if (file && isValidFile(file)) {
    uploadedFile.value = file
    importError.value = null
  } else {
    importError.value = __('Please upload a CSV or XLSX file.')
  }
}

function handleFileSelect(e) {
  let file = e.target.files?.[0]
  if (file && isValidFile(file)) {
    uploadedFile.value = file
    importError.value = null
  } else {
    importError.value = __('Please upload a CSV or XLSX file.')
  }
  e.target.value = ''
}

function clearFile() {
  uploadedFile.value = null
  importError.value = null
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function startImport() {
  if (!uploadedFile.value) return
  isImporting.value = true
  importError.value = null

  try {
    // 1. Create a Data Import record for CRM Lead
    let doc = await call('frappe.client.insert', {
      doc: {
        doctype: 'Data Import',
        reference_doctype: 'CRM Lead',
        import_type: 'Insert New Records',
      },
    })
    importDocName.value = doc.name

    // 2. Upload the file and attach it to the Data Import doc
    let uploader = new FilesUploadHandler()
    let fileDoc = await uploader.upload(uploadedFile.value, {
      fileObj: uploadedFile.value,
      private: true,
      doctype: 'Data Import',
      docname: doc.name,
    })

    // 3. Point the Data Import at the uploaded file
    await call('frappe.client.set_value', {
      doctype: 'Data Import',
      name: doc.name,
      fieldname: 'import_file',
      value: fileDoc?.file_url,
    })

    // 4. Kick off the import and poll for completion
    importStatus.value = 'In Progress'
    await call('frappe.core.doctype.data_import.data_import.form_start_import', {
      data_import: doc.name,
    })
    startPolling(doc.name)
  } catch (err) {
    importError.value =
      err?.messages?.join('\n') || err?.message || __('Import failed')
    if (importDocName.value) {
      importStatus.value = 'Error'
      importMessage.value = importError.value
    }
  } finally {
    isImporting.value = false
  }
}

function startPolling(docName) {
  pollInterval = setInterval(async () => {
    try {
      let res = await call(
        'frappe.core.doctype.data_import.data_import.get_import_status',
        { data_import_name: docName },
      )

      if (res.status === 'Success') {
        importStatus.value = 'Success'
        importMessage.value = __('{0} records imported successfully.', [
          res.success || res.total_records || '',
        ])
        fetchLogs(docName)
        stopPolling()
      } else if (res.status === 'Partial Success') {
        importStatus.value = 'Partial Success'
        importMessage.value = __(
          '{0} of {1} records imported. Check the import log for details.',
          [res.success || 0, res.total_records || 0],
        )
        fetchLogs(docName)
        stopPolling()
      } else if (res.status === 'Error') {
        importStatus.value = 'Error'
        importMessage.value = __('Import failed. {0} records failed.', [
          res.failed || '',
        ])
        fetchLogs(docName)
        stopPolling()
      } else if (res.status === 'Timed Out') {
        importStatus.value = 'Error'
        importMessage.value = __('Import timed out. Please try again.')
        stopPolling()
      }
      // else still Pending / In Progress — keep polling
    } catch {
      importStatus.value = 'Error'
      importMessage.value = __('Failed to check import status.')
      stopPolling()
    }
  }, 2000)
}

async function fetchLogs(docName) {
  importLogs.value =
    (await call('frappe.core.doctype.data_import.data_import.get_import_logs', {
      data_import: docName,
    })) || []
}

function parseLogMessages(messages) {
  if (!messages) return ''
  try {
    let parsed = typeof messages === 'string' ? JSON.parse(messages) : messages

    // A single Frappe message object with a `message` field
    if (
      typeof parsed === 'object' &&
      parsed !== null &&
      !Array.isArray(parsed) &&
      parsed.message
    ) {
      return String(parsed.message)
        .replace(/<(?:.|\n)*?>/gm, '')
        .trim()
    }

    // An array of messages (common Frappe pattern)
    if (Array.isArray(parsed)) {
      return parsed
        .map((msg) => {
          try {
            let inner = typeof msg === 'string' ? JSON.parse(msg) : msg
            if (inner && inner.message) return inner.message
          } catch {
            // not json, fall through
          }
          if (typeof msg === 'string') {
            return msg.replace(/<(?:.|\n)*?>/gm, '').trim()
          }
          return JSON.stringify(msg)
        })
        .join('\n')
    }

    if (typeof parsed === 'object' && parsed !== null) {
      return JSON.stringify(parsed)
    }
    return String(parsed)
  } catch {
    return String(messages)
      .replace(/<(?:.|\n)*?>/gm, '')
      .trim()
  }
}

function getLogTheme(log) {
  if (log.success) return 'green'
  let msg = parseLogMessages(log.messages).toLowerCase()
  if (
    msg.includes('duplicate') ||
    msg.includes('skipped') ||
    msg.includes('contact added')
  ) {
    return 'orange'
  }
  return 'red'
}

function getLogStatusLabel(log) {
  if (log.success) return __('Success')
  let msg = parseLogMessages(log.messages).toLowerCase()
  if (msg.includes('duplicate')) return __('Duplicate')
  if (msg.includes('skipped')) return __('Skipped')
  if (msg.includes('contact added')) return __('Contact Added')
  return __('Error')
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

function resetImport() {
  stopPolling()
  uploadedFile.value = null
  importDocName.value = null
  importStatus.value = null
  importMessage.value = null
  importLogs.value = []
  importError.value = null
  isImporting.value = false
}

// Stop polling when the modal is closed
watch(show, (val) => {
  if (!val) stopPolling()
})
</script>
