import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'
import router from '@/router'

export const visible = ref(false)

export const notifications = createResource({
  url: 'crm.api.notifications.get_notifications',
  initialData: [],
  auto: true,
  onSuccess: (data) => showDesktopNotifications(data),
})

export const unreadNotificationsCount = computed(
  () => notifications.data?.filter((n) => !n.read).length || 0,
)

export function getNotificationRoute(notification) {
  let params = {
    leadId: notification.reference_name,
  }
  if (notification.route_name === 'Deal') {
    params = {
      dealId: notification.reference_name,
    }
  }

  return {
    name: notification.route_name,
    params: params,
    hash: notification.hash,
  }
}

// desktop popups for incoming notifications (assignments, mentions, tasks)
let desktopBaseline = null

if (
  typeof window !== 'undefined' &&
  'Notification' in window &&
  Notification.permission === 'default'
) {
  // permission prompt needs a user gesture in most browsers
  window.addEventListener('click', () => Notification.requestPermission(), {
    once: true,
  })
}

function stripHtml(html) {
  if (!html) return ''
  const el = document.createElement('div')
  el.innerHTML = html
  return (el.textContent || '').trim()
}

function showDesktopNotifications(data) {
  if (!('Notification' in window)) return

  const newest = (data || []).reduce(
    (max, n) => (n.creation > max ? n.creation : max),
    '',
  )

  if (desktopBaseline === null) {
    // first load after opening the app — don't replay old notifications
    desktopBaseline = newest
    return
  }

  const fresh = (data || []).filter(
    (n) => !n.read && n.creation > desktopBaseline,
  )
  desktopBaseline = newest

  if (Notification.permission !== 'granted') return

  fresh.forEach((n) => {
    const body =
      stripHtml(n.notification_text) ||
      `${n.from_user?.full_name || ''} mentioned you in ${
        n.reference_doctype
      } ${n.reference_name}`.trim()

    const popup = new Notification(n.from_user?.full_name || 'CRM', {
      body,
      tag: n.comment || n.notification_type_doc || n.creation,
    })

    popup.onclick = () => {
      window.focus()
      router.push(getNotificationRoute(n))
      popup.close()
    }
  })
}

export const notificationsStore = defineStore('crm-notifications', () => {
  const mark_as_read = createResource({
    url: 'crm.api.notifications.mark_as_read',
    onSuccess: () => {
      mark_as_read.params = {}
      notifications.reload()
    },
  })

  function toggle() {
    visible.value = !visible.value
  }

  function mark_doc_as_read(doc) {
    mark_as_read.params = { doc: doc }
    mark_as_read.reload()
    toggle()
  }

  return {
    unreadNotificationsCount,
    mark_as_read,
    mark_doc_as_read,
    toggle,
  }
})
