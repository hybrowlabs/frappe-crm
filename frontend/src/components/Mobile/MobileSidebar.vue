<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" class="fixed inset-0" @close="sidebarOpened = false">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="relative z-10 flex h-full w-[260px] flex-col justify-between border-r bg-surface-menu-bar transition-all duration-300 ease-in-out"
        >
          <div>
            <UserDropdown class="p-2" :isCollapsed="!sidebarOpened" />
          </div>
          <div class="flex-1 overflow-y-auto">
            <div class="mb-3 flex flex-col">
              <SidebarLink
                id="notifications-btn"
                :label="__('Notifications')"
                :icon="NotificationsIcon"
                :to="{ name: 'Notifications' }"
                class="relative mx-2 my-0.5"
              >
                <template #right>
                  <Badge
                    v-if="unreadNotificationsCount"
                    :label="unreadNotificationsCount"
                    variant="subtle"
                  />
                </template>
              </SidebarLink>
            </div>
            <div v-for="view in allViews" :key="view.label">
              <Section
                :label="view.name"
                :hideLabel="view.hideLabel"
                :opened="view.opened"
              >
                <template #header="{ opened, hide, toggle }">
                  <div
                    v-if="!hide"
                    class="ml-2 mt-4 flex h-7 w-auto cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 opacity-100 transition-all duration-300 ease-in-out"
                    @click="toggle()"
                  >
                    <FeatherIcon
                      name="chevron-right"
                      class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                      :class="{ 'rotate-90': opened }"
                    />
                    <span>{{ __(view.name) }}</span>
                  </div>
                </template>
                <nav class="flex flex-col">
                  <template v-for="link in view.views" :key="link.label">
                    <div v-if="link.sepBefore" class="pa-nav-sep" />
                    <SidebarLink
                      :icon="link.icon"
                      :label="__(link.label)"
                      :to="link.to"
                      class="mx-2 my-0.5"
                    />
                  </template>
                </nav>
              </Section>
            </div>
          </div>
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-surface-gray-5 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>
<script setup>
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogOverlay,
} from '@headlessui/vue'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideCrown from '~icons/lucide/crown'
import LucideCompass from '~icons/lucide/compass'
import LucideRepeat from '~icons/lucide/repeat'
import LucideFlaskConical from '~icons/lucide/flask-conical'
import LucideUsers from '~icons/lucide/users'
import LucideZap from '~icons/lucide/zap'
import LucideContact from '~icons/lucide/contact'
import LucideBuilding from '~icons/lucide/building'
import LucideNotepadText from '~icons/lucide/notepad-text'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucidePhone from '~icons/lucide/phone'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucideFileText from '~icons/lucide/file-text'
import LucidePackageCheck from '~icons/lucide/package-check'
import Section from '@/components/Section.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { viewsStore } from '@/stores/views'
import { usersStore } from '@/stores/users'
import { unreadNotificationsCount } from '@/stores/notifications'
import { computed, h } from 'vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'

const { getPinnedViews, getPublicViews } = viewsStore()
const {
  isCEO,
  isSalesManager,
  isSalesperson,
  isTechnicalTeam,
  isMarketingTeam,
} = usersStore()

// Keep in sync with the links in Layouts/AppSidebar.vue
const links = [
  {
    label: 'Dashboard',
    icon: LucideSparkles,
    to: 'Dashboard',
  },
  {
    label: 'CEO Dashboard',
    icon: LucideCrown,
    to: 'CEODashboard',
    condition: () => isCEO(),
  },
  {
    label: 'Sales Manager',
    icon: LucideCompass,
    to: 'SalesManagerDashboard',
    condition: () => isSalesManager(),
  },
  {
    label: 'Repeat Business',
    icon: LucideRepeat,
    to: 'RepeatBusinessDashboard',
    condition: () => isSalesManager() || isCEO(),
  },
  {
    label: 'Technical Pre-Sale',
    icon: LucideFlaskConical,
    to: 'TechnicalPresaleDashboard',
    condition: () => isTechnicalTeam(),
  },
  {
    label: 'My Dashboard',
    icon: LucideSparkles,
    to: 'MyDashboard',
    condition: () => isSalesperson(),
  },
  {
    label: 'Marketing',
    icon: LucideMegaphone,
    to: 'MarketingDashboard',
    condition: () => isMarketingTeam(),
  },
  {
    label: 'Leads',
    icon: LucideUsers,
    sepBefore: true,
    to: 'Leads',
  },
  {
    label: 'Deals',
    icon: LucideZap,
    to: 'Deals',
  },
  {
    label: 'Quotations',
    icon: LucideFileText,
    to: 'Quotations',
  },
  {
    label: 'Sales Orders',
    icon: LucidePackageCheck,
    to: 'Sales Orders',
  },
  {
    label: 'Contacts',
    icon: LucideContact,
    to: 'Contacts',
  },
  {
    label: 'Organizations',
    icon: LucideBuilding,
    to: 'Organizations',
  },
  {
    label: 'Notes',
    icon: LucideNotepadText,
    to: 'Notes',
  },
  {
    label: 'Tasks',
    icon: LucideCircleCheck,
    to: 'Tasks',
  },
  {
    label: 'Call Logs',
    icon: LucidePhone,
    to: 'Call Logs',
  },
]

const allViews = computed(() => {
  let _views = [
    {
      name: 'All Views',
      hideLabel: true,
      opened: true,
      views: links.filter((link) => {
        if (link.condition) {
          return link.condition()
        }
        return true
      }),
    },
  ]
  if (getPublicViews().length) {
    _views.push({
      name: 'Public Views',
      opened: true,
      views: parseView(getPublicViews()),
    })
  }

  if (getPinnedViews().length) {
    _views.push({
      name: 'Pinned Views',
      opened: true,
      views: parseView(getPinnedViews()),
    })
  }
  return _views
})

function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) return h('div', { class: 'size-auto' }, icon)

  switch (routeName) {
    case 'Leads':
      return LucideUsers
    case 'Deals':
      return LucideZap
    case 'Quotations':
      return LucideFileText
    case 'Sales Orders':
      return LucidePackageCheck
    case 'Contacts':
      return LucideContact
    case 'Organizations':
      return LucideBuilding
    case 'Notes':
      return LucideNotepadText
    case 'Call Logs':
      return LucidePhone
    default:
      return PinIcon
  }
}
</script>
