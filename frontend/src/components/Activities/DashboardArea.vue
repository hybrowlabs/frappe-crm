<template>
  <div class="flex flex-col gap-5 px-3 pb-5 sm:px-10">
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
      <button
        v-for="section in sections"
        :key="section.key"
        class="flex flex-col items-start gap-1 rounded-lg border border-outline-gray-modals bg-surface-cards p-3 text-left hover:bg-surface-gray-2"
        @click="scrollToSection(section.key)"
      >
        <component :is="section.icon" class="h-4 w-4 text-ink-gray-5" />
        <div class="text-xl font-semibold text-ink-gray-9">
          {{ section.items.length }}
        </div>
        <div class="text-sm text-ink-gray-5">{{ section.label }}</div>
      </button>
    </div>

    <div
      v-for="section in sections"
      :key="section.key"
      :id="'dashboard-section-' + section.key"
      class="flex flex-col gap-3"
    >
      <div class="flex items-center justify-between border-b pb-2">
        <div class="flex items-center gap-2 text-lg font-semibold text-ink-gray-8">
          <component :is="section.icon" class="h-4 w-4" />
          {{ section.label }}
          <Badge :label="String(section.items.length)" variant="subtle" />
        </div>
        <Button
          variant="ghost"
          :label="__('View all')"
          iconRight="arrow-right"
          @click="emit('changeTab', section.tab)"
        />
      </div>

      <div
        v-if="!section.items.length"
        class="py-2 text-base text-ink-gray-4"
      >
        {{ section.emptyText }}
      </div>

      <div v-else-if="section.key == 'emails'">
        <EmailArea
          v-for="email in section.items"
          :key="email.name"
          class="mb-4"
          :activity="email"
          :emailBox="emailBox"
        />
      </div>

      <div v-else-if="section.key == 'comments'">
        <CommentArea
          v-for="comment in section.items"
          :key="comment.name"
          class="mb-4"
          :activity="comment"
          @reload="allActivities.reload()"
        />
      </div>

      <div v-else-if="section.key == 'tasks'">
        <TaskArea
          :modalRef="modalRef"
          :tasks="section.items"
          :doctype="doctype"
        />
      </div>

      <div
        v-else-if="section.key == 'notes'"
        class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3"
      >
        <div
          v-for="note in section.items"
          :key="note.name"
          @click="modalRef.showNote(note)"
        >
          <NoteArea v-model="allActivities" :note="note" />
        </div>
      </div>

      <div v-else-if="section.key == 'calls'">
        <CallArea
          v-for="call in section.items"
          :key="call.name"
          class="mb-4"
          :activity="call"
        />
      </div>

      <div v-else-if="section.key == 'events'" class="flex flex-col gap-3">
        <div
          v-for="event in section.items"
          :key="event.name"
          class="flex cursor-pointer gap-2 rounded-lg border border-outline-gray-modals bg-surface-cards px-2.5 py-2.5 text-ink-gray-9"
          @click="showEvent(event)"
        >
          <div
            class="flex w-[2px] rounded-lg"
            :style="{ backgroundColor: event.color || '#30A66D' }"
          />
          <div class="flex flex-1 flex-col gap-1 text-base">
            <div
              class="flex items-center justify-between gap-2 font-medium text-ink-gray-7"
            >
              <div>{{ event.subject }}</div>
              <MultipleAvatar
                v-if="event.participants?.length > 1"
                :avatars="event.participants"
                size="sm"
              />
            </div>
            <div class="flex items-center justify-between gap-2 text-ink-gray-6">
              <div>
                {{ startEndTime(event.starts_on, event.ends_on, event.all_day) }}
              </div>
              <div>{{ startDate(event.starts_on) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="section.key == 'attachments'">
        <AttachmentArea
          :attachments="section.items"
          @reload="allActivities.reload()"
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import EmailArea from '@/components/Activities/EmailArea.vue'
import CommentArea from '@/components/Activities/CommentArea.vue'
import TaskArea from '@/components/Activities/TaskArea.vue'
import NoteArea from '@/components/Activities/NoteArea.vue'
import CallArea from '@/components/Activities/CallArea.vue'
import AttachmentArea from '@/components/Activities/AttachmentArea.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import { useEvent, showEventModal, activeEvent } from '@/composables/event'
import { usersStore } from '@/stores/users'
import { Badge, Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
  modalRef: { type: Object, default: () => ({}) },
  emailBox: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['changeTab'])

const allActivities = defineModel({ type: Object })

const { getUser } = usersStore()

const { events, startEndTime, startDate } = useEvent({
  doctype: props.doctype,
  docname: props.docname,
})

function showEvent(event) {
  showEventModal.value = true
  activeEvent.value = event
}

function byCreationDesc(list) {
  return [...list].sort((a, b) => new Date(b.creation) - new Date(a.creation))
}

function byModifiedDesc(list) {
  return [...list].sort((a, b) => new Date(b.modified) - new Date(a.modified))
}

const emails = computed(() =>
  byCreationDesc(
    (allActivities.value?.data?.versions || []).filter(
      (activity) => activity.activity_type === 'communication',
    ),
  ),
)

const comments = computed(() =>
  byCreationDesc(
    (allActivities.value?.data?.versions || []).filter(
      (activity) => activity.activity_type === 'comment',
    ),
  ).map((comment) => ({
    ...comment,
    owner_name: getUser(comment.owner).full_name,
  })),
)

const sections = computed(() => [
  {
    key: 'emails',
    tab: 'emails',
    label: __('Emails'),
    icon: Email2Icon,
    items: emails.value,
    emptyText: __('No Emails Found'),
  },
  {
    key: 'comments',
    tab: 'comments',
    label: __('Comments'),
    icon: CommentIcon,
    items: comments.value,
    emptyText: __('No Comments Found'),
  },
  {
    key: 'tasks',
    tab: 'tasks',
    label: __('Tasks'),
    icon: TaskIcon,
    items: byModifiedDesc(allActivities.value?.data?.tasks || []),
    emptyText: __('No Tasks Found'),
  },
  {
    key: 'notes',
    tab: 'notes',
    label: __('Notes'),
    icon: NoteIcon,
    items: byModifiedDesc(allActivities.value?.data?.notes || []),
    emptyText: __('No Notes Found'),
  },
  {
    key: 'calls',
    tab: 'calls',
    label: __('Calls'),
    icon: PhoneIcon,
    items: byCreationDesc(allActivities.value?.data?.calls || []),
    emptyText: __('No Calls Found'),
  },
  {
    key: 'events',
    tab: 'events',
    label: __('Events'),
    icon: EventIcon,
    items: events.value || [],
    emptyText: __('No Events Scheduled'),
  },
  {
    key: 'attachments',
    tab: 'attachments',
    label: __('Attachments'),
    icon: AttachmentIcon,
    items: byModifiedDesc(allActivities.value?.data?.attachments || []),
    emptyText: __('No Attachments Found'),
  },
])

function scrollToSection(key) {
  document
    .getElementById('dashboard-section-' + key)
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>
