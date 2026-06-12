<template>
  <LayoutHeader>
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <div class="absolute right-0">
        <Dropdown
          v-if="doc"
          :options="
            statusOptions(
              'deal',
              document.statuses?.length
                ? document.statuses
                : document._statuses,
              triggerStatusChange,
            )
          "
        >
          <template #default="{ open }">
            <Button
              v-if="doc.status"
              :label="statusLabel(doc.status)"
              :iconRight="open ? 'chevron-up' : 'chevron-down'"
            >
              <template #prefix>
                <IndicatorIcon :class="getDealStatus(doc.status).color" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>
    </header>
  </LayoutHeader>
  <div
    v-if="doc.name"
    class="flex h-12 items-center justify-between gap-2 border-b px-3 py-2.5"
  >
    <AssignTo v-model="assignees.data" doctype="CRM Deal" :docname="dealId" />
    <div class="flex items-center gap-2">
      <Button
        v-if="hasQuotation"
        :label="__('View Quotations')"
        @click="showQuotationsModal = true"
      >
        <template #prefix>
          <FileTextIcon class="h-4 w-4" />
        </template>
      </Button>
      <Button
        v-if="stageCta"
        variant="solid"
        :label="stageCta.label"
        @click="onStageAction"
      >
        <template #prefix>
          <component :is="stageCta.icon" class="h-4 w-4" />
        </template>
      </Button>
      <Button
        v-if="canApproveEvaluation"
        variant="solid"
        :label="__('Approve Evaluation')"
        @click="showApproveEvaluationModal = true"
      >
        <template #prefix><BeakerIcon class="h-4 w-4" /></template>
      </Button>
      <Button
        v-if="canPrepareQuotation"
        variant="solid"
        :label="__('Prepare for Quotation')"
        @click="prepareForQuotation"
      >
        <template #prefix><RupeeIcon class="h-4 w-4" /></template>
      </Button>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
    </div>
  </div>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-auto flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-3 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel="{ tab }">
        <div v-if="tab.name == 'Details'">
          <SLASection
            v-if="doc.sla_status"
            v-model="doc"
            @updateField="updateField"
          />
          <div
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="CRM Deal"
              :docname="dealId"
              @reload="sections.reload"
              @beforeFieldChange="beforeStatusChange"
              @afterFieldChange="reloadAssignees"
            >
              <template #actions="{ section }">
                <div v-if="section.name == 'contacts_section'" class="pr-2">
                  <Link
                    value=""
                    doctype="Contact"
                    :onCreate="
                      (value, close) => {
                        _contact = {
                          first_name: value,
                          company_name: doc.organization,
                        }
                        showContactModal = true
                        close()
                      }
                    "
                    @change="(e) => addContact(e)"
                  >
                    <template #target="{ togglePopover }">
                      <Button
                        class="h-7 px-3"
                        variant="ghost"
                        icon="plus"
                        @click="togglePopover()"
                      />
                    </template>
                  </Link>
                </div>
              </template>
              <template #default="{ section }">
                <div
                  v-if="section.name == 'contacts_section'"
                  class="contacts-area"
                >
                  <div
                    v-if="
                      dealContacts?.loading && dealContacts?.data?.length == 0
                    "
                    class="flex min-h-20 flex-1 items-center justify-center gap-3 text-base text-ink-gray-4"
                  >
                    <LoadingIndicator class="h-4 w-4" />
                    <span>{{ __('Loading...') }}</span>
                  </div>
                  <div
                    v-for="(contact, i) in section.contacts"
                    v-else-if="section.contacts.length"
                    :key="contact.name"
                  >
                    <div
                      class="px-2 pb-2.5"
                      :class="[i == 0 ? 'pt-5' : 'pt-2.5']"
                    >
                      <Section :opened="contact.opened">
                        <template #header="{ opened, toggle }">
                          <div
                            class="flex cursor-pointer items-center justify-between gap-2 pr-1 text-base leading-5 text-ink-gray-7"
                          >
                            <div
                              class="flex h-7 items-center gap-2 truncate"
                              @click="toggle()"
                            >
                              <Avatar
                                :label="contact.full_name"
                                :image="contact.image"
                                size="md"
                              />
                              <div class="truncate">
                                {{ contact.full_name }}
                              </div>
                              <Badge
                                v-if="contact.is_primary"
                                class="ml-2"
                                variant="outline"
                                :label="__('Primary')"
                                theme="green"
                              />
                            </div>
                            <div class="flex items-center">
                              <Dropdown :options="contactOptions(contact.name)">
                                <Button
                                  icon="more-horizontal"
                                  class="text-ink-gray-5"
                                  variant="ghost"
                                />
                              </Dropdown>
                              <Button
                                variant="ghost"
                                @click="
                                  router.push({
                                    name: 'Contact',
                                    params: { contactId: contact.name },
                                  })
                                "
                              >
                                <ArrowUpRightIcon class="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" @click="toggle()">
                                <FeatherIcon
                                  name="chevron-right"
                                  class="h-4 w-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                                  :class="{ 'rotate-90': opened }"
                                />
                              </Button>
                            </div>
                          </div>
                        </template>
                        <div
                          class="flex flex-col gap-1.5 text-base text-ink-gray-8"
                        >
                          <div class="flex items-center gap-3 pb-1.5 pl-1 pt-4">
                            <Email2Icon class="h-4 w-4" />
                            {{ contact.email }}
                          </div>
                          <div class="flex items-center gap-3 p-1 py-1.5">
                            <PhoneIcon class="h-4 w-4" />
                            {{ contact.mobile_no }}
                          </div>
                        </div>
                      </Section>
                    </div>
                    <div
                      v-if="i != section.contacts.length - 1"
                      class="mx-2 h-px border-t border-outline-gray-modals"
                    />
                  </div>
                  <div
                    v-else
                    class="flex h-20 items-center justify-center text-base text-ink-gray-5"
                  >
                    {{ __('No Contacts Added') }}
                  </div>
                </div>
              </template>
            </SidePanelLayout>
          </div>
        </div>
        <Activities
          v-else
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Deal"
          :docname="dealId"
          :tabs="tabs"
          @beforeSave="beforeStatusChange"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <OrganizationModal
    v-if="showOrganizationModal"
    v-model="showOrganizationModal"
    :data="_organization"
    :options="{
      redirect: false,
      afterInsert: (_doc) => updateField('organization', _doc.name),
    }"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="_contact"
    :options="{
      redirect: false,
      afterInsert: (_doc) => addContact(_doc.name),
    }"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Deal'"
    :docname="dealId"
    name="Deals"
  />
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="CRM Deal"
    :document="document"
  />
  <CaptureRequirementsModal
    v-if="showCaptureRequirementsModal"
    v-model="showCaptureRequirementsModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    :deal="doc"
    @save="saveRequirements"
  />
  <InitiateTrialModal
    v-if="showInitiateTrialModal"
    v-model="showInitiateTrialModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    :deal="doc"
    @save="saveRequirements"
  />
  <RecordEvaluationModal
    v-if="showRecordEvaluationModal"
    v-model="showRecordEvaluationModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    :deal="doc"
    @save="saveRequirements"
    @lab="showLabRequestModal = true"
  />
  <ApproveEvaluationModal
    v-if="showApproveEvaluationModal"
    v-model="showApproveEvaluationModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    :deal="doc"
    @save="saveRequirements"
  />
  <RetrialStageModal
    v-if="showRetrialStageModal"
    v-model="showRetrialStageModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    @ticket="showCreateServiceTicketModal = true"
  />
  <ProposalStageModal
    v-if="showProposalStageModal"
    v-model="showProposalStageModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    @view-quotations="showQuotationsModal = true"
  />
  <OrderHandoffModal
    v-if="showOrderHandoffModal"
    v-model="showOrderHandoffModal"
    :statusLabel="statusLabel(doc.status)"
    :subtitle="`${title} · ${dealId}`"
    :value="dealValueLabel"
  />
  <CreateServiceTicketModal
    v-if="showCreateServiceTicketModal"
    v-model="showCreateServiceTicketModal"
    :customer="title"
    :dealId="dealId"
  />
  <LabRequestModal
    v-if="showLabRequestModal"
    v-model="showLabRequestModal"
    :customer="title"
  />
  <QuotationsModal
    v-if="showQuotationsModal"
    v-model="showQuotationsModal"
    :org="title"
    :dealId="dealId"
    :value="doc.deal_value || 0"
  />
  <PreQuotationModal
    v-if="showPreQuotationModal"
    v-model="showPreQuotationModal"
    :org="title"
    :subtitle="`${title} · ${dealId}`"
    :deal="doc"
    @confirm="confirmPreQuotation"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import CaptureRequirementsModal from '@/components/Modals/CaptureRequirementsModal.vue'
import InitiateTrialModal from '@/components/Modals/InitiateTrialModal.vue'
import RecordEvaluationModal from '@/components/Modals/RecordEvaluationModal.vue'
import ApproveEvaluationModal from '@/components/Modals/ApproveEvaluationModal.vue'
import RetrialStageModal from '@/components/Modals/RetrialStageModal.vue'
import ProposalStageModal from '@/components/Modals/ProposalStageModal.vue'
import OrderHandoffModal from '@/components/Modals/OrderHandoffModal.vue'
import CreateServiceTicketModal from '@/components/Modals/CreateServiceTicketModal.vue'
import LabRequestModal from '@/components/Modals/LabRequestModal.vue'
import QuotationsModal from '@/components/Modals/QuotationsModal.vue'
import PreQuotationModal from '@/components/Modals/PreQuotationModal.vue'
import PackageIcon from '@/components/Icons/PackageIcon.vue'
import BeakerIcon from '@/components/Icons/BeakerIcon.vue'
import HeadphonesIcon from '@/components/Icons/HeadphonesIcon.vue'
import RupeeIcon from '@/components/Icons/RupeeIcon.vue'
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import FileTextIcon from '@/components/Icons/FileTextIcon.vue'
import AssignTo from '@/components/AssignTo.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import Section from '@/components/Section.vue'
import Link from '@/components/Controls/Link.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupCustomizations, isTranslatable } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import {
  createResource,
  Dropdown,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, h, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { statusOptions, getDealStatus, dealStatuses } = statusesStore()
const { isManager } = usersStore()
const { doctypeMeta } = getMeta('CRM Deal')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  dealId: { type: String, required: true },
})

const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  document,
  scripts,
  error,
} = useDocument('CRM Deal', props.dealId)

const doc = computed(() => document.doc || {})

onMounted(async () => {
  if (document.doc) await triggerOnRender()
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? __('Document not found')
        : __('Error occurred'),
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteDeal,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const reload = ref(false)
const showOrganizationModal = ref(false)
const _organization = ref({})

// Stage-wise contextual action shown in the header, keyed by status name (PK).
const STAGE_CTA = {
  'Req. Discussion': { label: __('Capture Requirements'), icon: PackageIcon },
  Qualification: { label: __('Initiate Trial'), icon: BeakerIcon },
  'Demo/Making': { label: __('Record Evaluation'), icon: BeakerIcon },
  Retrial: { label: __('Record Evaluation'), icon: BeakerIcon },
  'Proposal/Quotation': { label: __('Create Quotation'), icon: RupeeIcon },
}

const stageCta = computed(() => {
  if (!doc.value.status) return null
  return STAGE_CTA[doc.value.status] || null
})

// Quotations are reviewable directly from the header on the Proposal & Won stages.
const hasQuotation = computed(() => {
  if (!doc.value.status) return false
  return ['Proposal/Quotation', 'Won'].includes(doc.value.status)
})

const dealValueLabel = computed(() =>
  doc.value?.deal_value
    ? '₹' + Number(doc.value.deal_value).toLocaleString('en-IN')
    : '',
)

// Each pipeline stage's header CTA opens its own stage-form modal (keyed by status name).
const STAGE_MODALS = {
  'Req. Discussion': 'showCaptureRequirementsModal',
  Qualification: 'showInitiateTrialModal',
  'Demo/Making': 'showRecordEvaluationModal',
  Retrial: 'showRecordEvaluationModal',
  'Proposal/Quotation': 'showProposalStageModal',
}

const showCaptureRequirementsModal = ref(false)
const showInitiateTrialModal = ref(false)
const showRecordEvaluationModal = ref(false)
const showApproveEvaluationModal = ref(false)

// Sales Managers can approve a partially-successful evaluation awaiting their decision.
const canApproveEvaluation = computed(
  () =>
    doc.value?.status === 'Evaluation Completed' &&
    doc.value?.sales_manager_approval_required &&
    !doc.value?.sales_manager_approved &&
    isManager(),
)

// Once approval isn't required (or is already granted), proceed to the quotation.
const canPrepareQuotation = computed(
  () =>
    doc.value?.status === 'Evaluation Completed' &&
    (!doc.value?.sales_manager_approval_required ||
      doc.value?.sales_manager_approved),
)

// Open the same pre-quotation gate that fires when moving into Proposal/Quotation.
function prepareForQuotation() {
  triggerStatusChange('Proposal/Quotation')
}
const showRetrialStageModal = ref(false)
const showProposalStageModal = ref(false)
const showOrderHandoffModal = ref(false)
const showCreateServiceTicketModal = ref(false)
const showLabRequestModal = ref(false)
const showQuotationsModal = ref(false)
const showPreQuotationModal = ref(false)

const stageModals = {
  showCaptureRequirementsModal,
  showInitiateTrialModal,
  showRecordEvaluationModal,
  showRetrialStageModal,
  showProposalStageModal,
  showOrderHandoffModal,
}

function onStageAction() {
  let status = doc.value.status


  // Quotations live in ERPNext — jump straight to the Desk create page,
  // prefilling the custom_deal link back to this deal.
  if (status === 'Proposal/Quotation') {
    window.open(`/app/quotation/new?custom_deal=${encodeURIComponent(props.dealId)}`, '_blank')
    return
  }

  let modal = STAGE_MODALS[status]
  if (modal && stageModals[modal]) {
    stageModals[modal].value = true
    return
  }
  toast(stageCta.value?.label)
}

// Find the next pipeline stage (by position) after the current status.
function nextStageName() {
  let ordered = dealStatuses.data || []
  let idx = ordered.findIndex((s) => s.name === doc.value.status)
  let next = idx > -1 ? ordered[idx + 1] : null
  return next?.name || null
}

function saveRequirements({ values, advance, status }) {
  Object.assign(doc.value, values)
  // Advance to the next stage in the same save so the status reliably persists.
  // `status`, when provided, is a status name (PK).
  if (status) {
    doc.value.status = status
  } else if (advance) {
    let next = nextStageName()
    if (next) doc.value.status = next
  }
  document.save.submit(null, {
    onSuccess: () => {
      reload.value = true
      toast.success(__('Requirements saved'))
    },
    onError: (err) => {
      toast.error(err.messages?.[0] || __('Error saving requirements'))
    },
  })
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Deals'), route: { name: 'Deals' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Deal')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Deals',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Deal', params: { dealId: props.dealId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[t] || props.dealId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Details',
      label: __('Details'),
      icon: DetailsIcon,
      condition: () => isMobileView.value,
    },
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
      condition: () => callEnabled.value,
    },
    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})
const { tabIndex } = useActiveTabManager(tabs, 'lastDealTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Deal'],
  params: { doctype: 'CRM Deal' },
  auto: true,
  transform: (data) => getParsedFields(data),
})

function getParsedFields(sections) {
  sections.forEach((section) => {
    if (section.name == 'contacts_section') return
    section.columns[0].fields.forEach((field) => {
      if (field.name == 'organization') {
        field.create = (value, close) => {
          _organization.value.organization_name = value
          showOrganizationModal.value = true
          close()
        }
        field.link = (org) =>
          router.push({
            name: 'Organization',
            params: { organizationId: org },
          })
      }
    })
  })
  return sections
}

const showContactModal = ref(false)
const _contact = ref({})

function contactOptions(contact) {
  let options = [
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => removeContact(contact),
    },
  ]

  if (!contact.is_primary) {
    options.push({
      label: __('Set as Primary Contact'),
      icon: h(SuccessIcon, { class: 'h-4 w-4' }),
      onClick: () => setPrimaryContact(contact.name),
    })
  }

  return options
}

async function addContact(contact) {
  if (dealContacts.data?.find((c) => c.name === contact)) {
    toast.error(__('Contact Already Added'))
    return
  }

  let d = await call('crm.fcrm.doctype.crm_deal.crm_deal.add_contact', {
    deal: props.dealId,
    contact,
  })
  if (d) {
    dealContacts.reload()
    toast.success(__('Contact Added'))
  }
}

async function removeContact(contact) {
  let d = await call('crm.fcrm.doctype.crm_deal.crm_deal.remove_contact', {
    deal: props.dealId,
    contact,
  })
  if (d) {
    dealContacts.reload()
    toast.success(__('Contact Removed'))
  }
}

async function setPrimaryContact(contact) {
  let d = await call('crm.fcrm.doctype.crm_deal.crm_deal.set_primary_contact', {
    deal: props.dealId,
    contact,
  })
  if (d) {
    dealContacts.reload()
    toast.success(__('Primary Contact Set'))
  }
}

const dealContacts = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_contacts',
  params: { name: props.dealId },
  cache: ['deal_contacts', props.dealId],
  auto: true,
  onSuccess: (data) => {
    let contactSection = sections.data?.find(
      (section) => section.name == 'contacts_section',
    )
    if (!contactSection) return
    contactSection.contacts = data.map((contact) => {
      return {
        name: contact.name,
        full_name: contact.full_name,
        email: contact.email,
        mobile_no: contact.mobile_no,
        image: contact.image,
        is_primary: contact.is_primary,
        opened: false,
      }
    })
  },
})

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteDeal() {
  showDeleteLinkedDocModal.value = true
}

function statusLabel(status) {
  let label = getDealStatus(status)?.label || status
  if (isTranslatable('CRM Deal Status')) return __(label)
  return label
}

// A forward move is "single step" when no required stage sits between the current
// and target status. Retrial is an optional branch, so it may be skipped.
const SKIPPABLE_STAGES = ['Retrial']
function isSingleStepForward(current, target) {
  const ordered = dealStatuses.data || []
  const positions = Object.fromEntries(ordered.map((s) => [s.name, s.position]))
  const oldPos = positions[current] ?? 0
  const newPos = positions[target] ?? 0
  if (newPos <= oldPos) return false
  const intermediate = ordered.filter(
    (s) =>
      s.position > oldPos &&
      s.position < newPos &&
      !SKIPPABLE_STAGES.includes(s.name),
  )
  return intermediate.length === 0
}

async function triggerStatusChange(value) {
  const current = doc.value.status
  const singleStep = isSingleStepForward(current, value)

  // On a single-step forward move, open the stage form (which captures the data
  // and advances the status itself) instead of changing the status immediately.
  // Multi-step jumps fall through to a direct change (validated on the backend).
  if (singleStep) {
    // Entering Proposal/Quotation runs the pre-quotation customer gate.
    if (value === 'Proposal/Quotation' && current !== 'Proposal/Quotation') {
      pendingProposalStatus.value = value
      showPreQuotationModal.value = true
      return
    }
    // The Proposal stage form doesn't advance the deal, so skip it here.
    if (current !== 'Proposal/Quotation') {
      const modal = STAGE_MODALS[current]
      if (modal && stageModals[modal]) {
        stageModals[modal].value = true
        return
      }
    }
  }

  await triggerOnChange('status', value)
  setLostReason()
}

const pendingProposalStatus = ref(null)

async function confirmPreQuotation(payload) {
  let value = pendingProposalStatus.value
  pendingProposalStatus.value = null
  if (!value) return
  if (payload) await createDealAddresses(payload)
  await triggerOnChange('status', value)
  setLostReason()
}

async function createDealAddresses(payload) {
  doc.value.legal_name = payload.legalName
  doc.value.gstin = payload.gstin
  doc.value.freight_terms = payload.freight_terms
  const addressTitle = payload.legalName || title.value || props.dealId
  const links = [{ link_doctype: 'CRM Deal', link_name: props.dealId }]
  try {
    const billingAddress = await call('frappe.client.insert', {
      doc: {
        doctype: 'Address',
        address_title: addressTitle,
        address_type: 'Billing',
        gstin: payload.gstin,
        ...payload.billing,
        links,
      },
    })
    doc.value.billing_address = billingAddress.name
    if (!payload.sameAsBilling) {
      const shippingAddress = await call('frappe.client.insert', {
        doc: {
          doctype: 'Address',
          address_title: addressTitle,
          address_type: 'Shipping',
          gstin: payload.gstin,
          ...payload.shipping,
          links,
        },
      })
      doc.value.shipping_address = shippingAddress.name
    } else {
      doc.value.shipping_address = billingAddress.name
    }
  } catch (err) {
    toast.error(err.messages?.[0] || __('Error creating address'))
  }
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getDealStatus(doc.value.status).type !== 'Lost' ||
    (doc.value.lost_reason && doc.value.lost_reason !== 'Other') ||
    (doc.value.lost_reason === 'Other' && doc.value.lost_notes)
  ) {
    document.save.submit()
    return
  }

  showLostReasonModal.value = true
}

function beforeStatusChange(data) {
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getDealStatus(data.status).type == 'Lost'
  ) {
    setLostReason()
  } else {
    document.save.submit(null, {
      onSuccess: () => reloadAssignees(data),
    })
  }
}

function reloadAssignees(data) {
  if (Object.hasOwn(data ?? {}, 'deal_owner')) {
    assignees.reload()
  }
}
</script>
