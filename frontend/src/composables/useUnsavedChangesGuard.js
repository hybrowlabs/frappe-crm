import { globalStore } from '@/stores/global'
import { onMounted, onUnmounted } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'

export function useUnsavedChangesGuard(document) {
  const { $dialog } = globalStore()

  function confirmLeave(to, from) {
    // tab/view switches change only hash or query — the edit buffer survives those
    if (to && from && to.path === from.path) return true
    if (!document.isDirty) return true

    return new Promise((resolve) => {
      $dialog({
        title: __('Unsaved Changes'),
        message: __(
          'You have unsaved changes on this page. Discard them and leave?',
        ),
        actions: [
          {
            label: __('Discard & Leave'),
            variant: 'solid',
            theme: 'red',
            onClick: (close) => {
              document.doc = JSON.parse(JSON.stringify(document.originalDoc))
              close()
              resolve(true)
            },
          },
          {
            label: __('Stay'),
            onClick: (close) => {
              close()
              resolve(false)
            },
          },
        ],
      })
    })
  }

  onBeforeRouteLeave(confirmLeave)
  onBeforeRouteUpdate(confirmLeave)

  const beforeUnloadHandler = (event) => {
    if (!document.isDirty) return
    event.preventDefault()
    event.returnValue = true
  }

  onMounted(() => addEventListener('beforeunload', beforeUnloadHandler))
  onUnmounted(() => removeEventListener('beforeunload', beforeUnloadHandler))
}
