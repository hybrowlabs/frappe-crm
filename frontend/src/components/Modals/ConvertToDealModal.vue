<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-header>
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Convert to Deal') }}
          </h3>
        </div>
        <div class="flex items-center gap-1">
          <Button
            v-if="isManager() && !isMobileView"
            variant="ghost"
            :tooltip="__('Edit deal\'s mandatory fields layout')"
            :icon="EditIcon"
            @click="openQuickEntryModal"
          />
          <Button icon="x" variant="ghost" @click="show = false" />
        </div>
      </div>
    </template>
    <template #body-content>
      <div
        v-if="vaultDocsPending"
        class="rounded-md border border-outline-gray-2 bg-surface-gray-2 p-3"
      >
        <div class="mb-1 text-base font-medium text-ink-gray-8">
          {{ __('Vault — shareholding documents not shared') }}
        </div>
        <div class="mb-3 text-sm text-ink-gray-6">
          {{
            vaultOnly
              ? __(
                  'This lead cannot be converted until the client shares their shareholding documents.',
                )
              : __(
                  'The Vault deal will be skipped — the other verticals will convert now, and you can create the Vault deal from them once documents are shared.',
                )
          }}
        </div>
        <div class="flex items-center justify-between text-base text-ink-gray-9">
          <div>{{ __('Documents received — mark as shared') }}</div>
          <Switch v-model="markDocumentsShared" />
        </div>
      </div>

      <div v-if="dealTabs.data?.length" class="h-px w-full border-t my-6" />

      <FieldLayout
        v-if="dealTabs.data?.length"
        :tabs="dealTabs.data"
        :data="deal.doc"
        doctype="CRM Deal"
      />
      <ErrorMessage class="mt-4" :message="error" />
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="__('Convert')"
          variant="solid"
          :disabled="vaultOnly && vaultDocsPending && !markDocumentsShared"
          @click="convertToDeal"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { useDocument } from '@/data/document'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { isMobileView } from '@/composables/settings'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Switch, Dialog, createResource, call, toast } from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: { type: Object, required: true },
})

// Endovia Vault gate — a Vault deal needs the client's shareholding
// documents shared on the lead (see endovia_finance conversion cases plan)
const VERTICAL_FIELDS = ['wealth_management', 'quant', 'vault', 'books']
const markDocumentsShared = ref(false)
const documentsSaved = ref(false)

const vaultDocsPending = computed(
  () =>
    props.lead.vault &&
    !props.lead.vault_documents_shared &&
    !documentsSaved.value,
)
const vaultOnly = computed(
  () =>
    props.lead.vault &&
    !VERTICAL_FIELDS.some((f) => f !== 'vault' && props.lead[f]),
)

const show = defineModel({ type: Boolean })

const router = useRouter()

const { isManager } = usersStore()
const { user } = sessionStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const error = ref('')
const { capture } = useTelemetry()

const { triggerConvertToDeal } = useDocument('CRM Lead', props.lead.name)
const { document: deal } = useDocument('CRM Deal')

async function convertToDeal() {
  error.value = ''

  if (vaultDocsPending.value && markDocumentsShared.value) {
    try {
      await call('frappe.client.set_value', {
        doctype: 'CRM Lead',
        name: props.lead.name,
        fieldname: 'vault_documents_shared',
        value: 1,
      })
      documentsSaved.value = true
    } catch (err) {
      error.value = __('Could not mark documents as shared: {0}', [
        err.messages?.[0],
      ])
      return
    }
  }

  await triggerConvertToDeal?.(props.lead, deal.doc, () => (show.value = false))

  let _deal = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
    lead: props.lead.name,
    deal: deal.doc,
  }).catch((err) => {
    if (err.exc_type == 'MandatoryError') {
      const errorMessage = err.messages
        .map((msg) => {
          let arr = msg.split(': ')
          return arr[arr.length - 1].trim()
        })
        .join(', ')

      if (errorMessage.toLowerCase().includes('required')) {
        error.value = __(errorMessage)
      } else {
        error.value = __('{0} is required', [errorMessage])
      }
      return
    }
    error.value = __('Error converting to deal: {0}', [err.messages?.[0]])
  })
  if (_deal) {
    show.value = false
    error.value = ''
    updateOnboardingStep('convert_lead_to_deal', true, false, () => {
      localStorage.setItem('firstDeal' + user, _deal)
    })
    capture('convert_lead_to_deal')
    notifySkippedVerticals()
    router.push({ name: 'Deal', params: { dealId: _deal } })
  }
}

function notifySkippedVerticals() {
  call('endovia_finance.api.conversion.get_pending_verticals', {
    lead: props.lead.name,
  })
    .then((pending) => {
      if (!pending?.length) return
      const labels = pending.map((v) => __(v.label)).join(', ')
      toast.info(
        __('{0} deal not created — documents pending. Create it from the deal once shared.', [labels]),
      )
    })
    .catch(() => {})
}


const dealTabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['RequiredFields', 'CRM Deal'],
  params: { doctype: 'CRM Deal', type: 'Required Fields' },
  auto: true,
  transform: (_tabs) => {
    let hasFields = false
    let parsedTabs = _tabs?.forEach((tab) => {
      tab.sections?.forEach((section) => {
        section.columns?.forEach((column) => {
          // Endovia: no status picker on convert — each vertical's deal
          // starts in its configured default status (server-side,
          // CRM Deal Status.custom_default_for_verticals)
          column.fields = column.fields?.filter(
            (field) => field.fieldname !== 'status',
          )
          column.fields?.forEach((field) => {
            hasFields = true
            if (field.fieldtype === 'Table') {
              deal.doc[field.fieldname] = []
            }
          })
        })
      })
    })
    return hasFields ? parsedTabs : []
  },
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = {
    doctype: 'CRM Deal',
    onlyRequired: true,
  }
  show.value = false
}
</script>
