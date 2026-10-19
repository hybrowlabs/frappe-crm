import { computed, ref } from 'vue'

export const mobileSidebarOpened = ref(false)

// Below this width the app switches to the mobile layout and mobile pages.
export const MOBILE_BREAKPOINT = 768
// Below this width the desktop sidebar starts collapsed so content has room.
export const TABLET_BREAKPOINT = 1024

export const windowWidth = ref(window.innerWidth)
window.addEventListener('resize', () => {
  windowWidth.value = window.innerWidth
})

export const isMobileView = computed(
  () => windowWidth.value < MOBILE_BREAKPOINT,
)
export const isTabletView = computed(
  () => !isMobileView.value && windowWidth.value < TABLET_BREAKPOINT,
)

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')
