/*
Keeps a page in step with changes made in other tabs or browsers.

Two parts working together:
- Live: Supabase Realtime tells this tab when a watched table changes.
- Catch-up: when the tab is shown again or the window gets focus, reload.
  Live messages are lost while a laptop sleeps or the connection drops, so
  this covers whatever was missed.

Either way the page reloads its data quietly (its own `refresh`), at most
once per burst of changes, and never while `paused()` is true (a dialog is
open, a save is running, a row is being dragged).
*/

import { onBeforeUnmount, onMounted, watch } from 'vue'
import { supabase } from '@/lib/supabase.js'
import { useAuth } from './useAuth.js'

const DEBOUNCE_MS = 400 // many changes at once → one reload
const CATCH_UP_GAP_MS = 2000 // don't reload on every focus flicker

let channelCount = 0

/**
 * @param {object} options
 * @param {string} options.name        Short label for the channel ('library').
 * @param {Array}  options.tables      [{ table, ownerFilter?, accept?(payload) }]
 *   ownerFilter: only hear about this user's rows (inserts and updates; Supabase
 *   can't filter deletes). accept: return false to ignore a message.
 * @param {Function} options.refresh   Reloads the page's data without a spinner.
 * @param {Function} [options.paused]  Returns true while a reload must wait.
 */
export function useLiveRefresh({ name, tables, refresh, paused = () => false }) {
  const { user } = useAuth()

  let timer = null
  let running = false
  let pending = false // a reload was asked for while it couldn't run
  let lastRun = Date.now() // the page has just loaded
  let channel = null
  let wasDisconnected = false

  function schedule() {
    clearTimeout(timer)
    timer = setTimeout(run, DEBOUNCE_MS)
  }

  async function run() {
    // Hidden tabs wait until they're shown; busy pages wait until they're free.
    if (document.hidden || paused() || running) {
      pending = true
      return
    }
    pending = false
    running = true
    try {
      await refresh()
    } catch {
      // The page's own load() shows its errors.
    } finally {
      running = false
      lastRun = Date.now()
    }
    if (pending) schedule()
  }

  // A reload that waited for a dialog or a save runs once that's done.
  watch(paused, (isPaused) => {
    if (!isPaused && pending) schedule()
  })

  function catchUp() {
    if (document.hidden) return
    if (pending || Date.now() - lastRun > CATCH_UP_GAP_MS) schedule()
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', catchUp)
    window.addEventListener('focus', catchUp)

    const ownerId = user.value?.id
    channel = supabase.channel(`live-${name}-${++channelCount}`)

    for (const { table, ownerFilter = false, accept = () => true } of tables) {
      channel.on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table,
          ...(ownerFilter && ownerId ? { filter: `owner_id=eq.${ownerId}` } : {}),
        },
        (payload) => {
          if (accept(payload)) schedule()
        },
      )
    }

    channel.subscribe((status) => {
      if (status === 'SUBSCRIBED') {
        // Back after a dropped connection: changes may have been missed.
        if (wasDisconnected) schedule()
        wasDisconnected = false
      } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') {
        wasDisconnected = true
      }
    })
  })

  onBeforeUnmount(() => {
    clearTimeout(timer)
    document.removeEventListener('visibilitychange', catchUp)
    window.removeEventListener('focus', catchUp)
    if (channel) supabase.removeChannel(channel)
  })
}

// ---- helpers for `accept` ---------------------------------------------------------

/**
 * For a delete, Supabase sends only the row's id, and sends it to everyone
 * watching the table (it can't check who owned a deleted row). Only react if
 * the id is one this page is showing.
 */
export function deleteIsOurs(payload, idKey, knownIds) {
  if (payload.eventType !== 'DELETE') return true
  return knownIds().has(payload.old?.[idKey])
}

// Export progress updates arrive every few percent; only finished exports
// change what the lists show.
const RUNNING = new Set(['pending', 'processing', 'packaging'])
export function exportChangeMatters(payload) {
  return payload.eventType !== 'UPDATE' || !RUNNING.has(payload.new?.status)
}