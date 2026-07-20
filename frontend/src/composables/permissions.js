import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

// `${doctype}:${ptype}` -> true | false, undefined while the check is in flight
const permissions = reactive({})
const requested = {}

/**
 * Whether the current user has `ptype` permission on `doctype`.
 *
 * Resolves to false until the server answers, so an action is never offered to
 * someone who turns out not to be allowed. Cached per doctype+ptype, so this
 * hits the server once per session.
 */
export function hasPermission(doctype, ptype) {
  if (!doctype) return false
  const key = `${doctype}:${ptype}`

  if (!requested[key]) {
    requested[key] = true
    createResource({
      url: 'frappe.client.has_permission',
      params: { doctype, docname: '', perm_type: ptype },
      cache: ['permission', doctype, ptype],
      auto: true,
      onSuccess: (r) => (permissions[key] = Boolean(r?.has_permission)),
      onError: () => (permissions[key] = false),
    })
  }

  return permissions[key] === true
}

export const canDelete = (doctype) => hasPermission(doctype, 'delete')
