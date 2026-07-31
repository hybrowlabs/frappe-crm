import { useDebounceFn } from '@vueuse/core'

// Stage-form drafts are cached so closing and reopening the popup on the same page
// visit doesn't lose what was typed. They are deliberately short-lived: a tab switch,
// a page reload or opening another deal all clear them (see Deal.vue / App.vue).
const PREFIX = 'stageFormDraft:'

// Bump when the shape of a stage form's captured values changes — drafts written by
// an older build are then discarded instead of applied to fields that moved.
const VERSION = 1

// Read from the cookie rather than the session store: this module is also used at
// app boot, before Pinia is installed.
function currentUser() {
  let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
  return cookies.get('user_id') || 'guest'
}

function draftKey(docname, status) {
  return `${PREFIX}${currentUser()}:CRM Deal:${docname}:${status}`
}

/**
 * Draft cache for one deal's stage form.
 *
 * `docname` and `status` are part of the key so a draft can never be applied to a
 * different deal, or to the same deal after it has moved to another stage.
 */
export function useStageFormDraft(docname, status) {
  const key = draftKey(docname, status)

  function read() {
    let raw = localStorage.getItem(key)
    if (!raw) return null
    try {
      let draft = JSON.parse(raw)
      // Reject anything we can't trust: a stale schema, or a payload that names a
      // different deal than the key it was found under.
      if (draft?.v !== VERSION || draft?.docname !== docname) {
        localStorage.removeItem(key)
        return null
      }
      return draft
    } catch (e) {
      localStorage.removeItem(key)
      return null
    }
  }

  function write(payload) {
    try {
      localStorage.setItem(
        key,
        JSON.stringify({ v: VERSION, docname, ...payload }),
      )
    } catch (e) {
      // Out of quota or storage disabled — the form must keep working regardless.
    }
  }

  function clear() {
    localStorage.removeItem(key)
  }

  return {
    key,
    read,
    // Typing shouldn't hit localStorage on every keystroke.
    save: useDebounceFn(write, 400),
    // The debounced save loses the last few hundred ms when the popup unmounts.
    flush: write,
    clear,
  }
}

/**
 * Drop every stage-form draft except the given deal's.
 *
 * Passing `null` clears all of them. Used to enforce that at most one deal's draft
 * exists at a time, and to wipe drafts on tab change and page load.
 */
export function purgeOtherStageDrafts(keepDocname) {
  let keepPrefix = keepDocname
    ? `${PREFIX}${currentUser()}:CRM Deal:${keepDocname}:`
    : null
  // Snapshot the keys first — removing while iterating localStorage skips entries.
  for (let key of Object.keys(localStorage)) {
    if (!key.startsWith(PREFIX)) continue
    if (keepPrefix && key.startsWith(keepPrefix)) continue
    localStorage.removeItem(key)
  }
}
