<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Create {0} Deal', [vertical?.label || '']) }"
  >
    <template #body-content>
      <div class="mb-3 text-base text-ink-gray-7">
        {{
          __(
            "A Vault deal needs the client's shareholding documents. Confirm they have been shared to continue.",
          )
        }}
      </div>
      <div
        class="mb-3 flex items-center justify-between text-base text-ink-gray-9"
      >
        <div>{{ __('Documents received — mark as shared') }}</div>
        <Switch v-model="documentsShared" />
      </div>
      <FileUploader
        :uploadArgs="{
          doctype: 'CRM Lead',
          docname: lead,
          fieldname: 'vault_documents',
          private: true,
        }"
        @success="(file) => (fileUrl = file.file_url)"
      >
        <template #default="{ openFileSelector, uploading }">
          <div class="flex items-center gap-2">
            <Button
              :label="
                fileUrl ? __('Replace attachment') : __('Attach documents')
              "
              :loading="uploading"
              @click="openFileSelector"
            />
            <div v-if="fileUrl" class="truncate text-sm text-ink-gray-6">
              {{ fileUrl.split('/').pop() }}
            </div>
            <div v-else class="text-sm text-ink-gray-5">
              {{ __('(optional)') }}
            </div>
          </div>
        </template>
      </FileUploader>
      <ErrorMessage class="mt-3" :message="error" />
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create Deal')"
          :disabled="!documentsShared"
          :loading="creating"
          @click="createDeal"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  Switch,
  Button,
  FileUploader,
  ErrorMessage,
  call,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
  vertical: { type: Object, default: null },
})

const emit = defineEmits(['created'])
const show = defineModel({ type: Boolean })

const documentsShared = ref(false)
const fileUrl = ref('')
const error = ref('')
const creating = ref(false)

watch(show, (open) => {
  if (open) {
    documentsShared.value = false
    fileUrl.value = ''
    error.value = ''
  }
})

function createDeal() {
  error.value = ''
  creating.value = true
  call('endovia_finance.api.conversion.share_documents_and_convert', {
    lead: props.lead,
    vertical_field: props.vertical.field,
    file_url: fileUrl.value || null,
  })
    .then((deal) => emit('created', deal))
    .catch((err) => {
      error.value = err.messages?.[0] || __('Could not create the deal')
    })
    .finally(() => (creating.value = false))
}
</script>
