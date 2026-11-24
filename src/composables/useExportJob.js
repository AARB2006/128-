import { computed, ref } from 'vue'
import {
  cancelExport,
  downloadExport,
  getActiveExport,
  getExport,
  startExport,
} from '@/services/exportService.js'

// One export runs at a time per user, so this state is shared by the whole app
// (it lives outside the function): the progress card, the playlist pages and
// Export History all see the same job.

const POLL_MS = 1000
const MAX_POLL_FAILURES = 5
const ACTIVE = ['pending', 'processing', 'packaging']
const WITH_FILE = ['completed', 'partial']

const job = ref(null) // the `exports` row, with export_items
const phase = ref('idle') // idle | starting | running | finished
const error = ref('') // lost connection while polling
const downloadError = ref('')
const downloading = ref(false)
const cancelling = ref(false)
const finishedCount = ref(0) // bumps each time an export ends (Export History reloads)

let timer = null
let failures = 0
let startedHere = false // only the tab that started an export downloads it automatically

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

function stopPolling() {
  clearTimeout(timer)
  timer = null
}

async function poll() {
  stopPolling()
  const id = job.value?.export_id
  if (!id) return

  try {
    const latest = await getExport(id)
    if (job.value?.export_id !== id) return // dismissed or replaced meanwhile
    if (!latest) throw new Error('Export not found')

    failures = 0
    // If the playlist is deleted mid-export its name disappears from the
    // join; keep showing the name the card started with.
    job.value = { ...latest, playlist_name: latest.playlist_name ?? job.value.playlist_name }

    if (!ACTIVE.includes(latest.status)) {
      finish()
      return
    }
  } catch {
    if (job.value?.export_id !== id) return
    failures += 1
    if (failures >= MAX_POLL_FAILURES) {
      error.value =
        'Lost connection while checking progress. Your export may still be ' +
        'running; reload the page to check.'
      phase.value = 'finished'
      return
    }
  }

  timer = setTimeout(poll, POLL_MS)
}

function finish() {
  stopPolling()
  phase.value = 'finished'
  cancelling.value = false
  finishedCount.value += 1

  if (startedHere && WITH_FILE.includes(job.value.status)) {
    download()
  }
  startedHere = false
}

/** Start exporting `playlist` ({ playlist_id, name }). Throws ApiError if refused. */
async function start(playlist) {
  if (phase.value === 'starting' || phase.value === 'running') return

  stopPolling()
  error.value = ''
  downloadError.value = ''
  failures = 0
  phase.value = 'starting'
  job.value = {
    export_id: null,
    playlist_id: playlist.playlist_id,
    playlist_name: playlist.name,
    status: 'pending',
    percent: 0,
    total_songs: 0,
    exported_songs: 0,
    export_items: [],
  }

  try {
    const started = await startExport(playlist.playlist_id)
    job.value = { ...job.value, export_id: started.export_id, total_songs: started.total_songs }
    phase.value = 'running'
    startedHere = true
    await poll()
  } catch (e) {
    job.value = null
    phase.value = 'idle'
    throw e
  }
}

// Pick up an export that is still running (page reloaded, or another tab).
async function resume() {
  if (phase.value !== 'idle') return
  try {
    const active = await getActiveExport()
    if (!active || phase.value !== 'idle') return
    job.value = active
    phase.value = 'running'
    await poll()
  } catch {
    // Not being able to resume is harmless: the card just stays hidden.
  }
}

async function cancel() {
  if (!job.value?.export_id || cancelling.value) return
  cancelling.value = true
  try {
    await cancelExport(job.value.export_id)
  } catch (e) {
    cancelling.value = false
    // 409: it finished in the meantime; the next poll shows the result.
    if (e.status !== 409) error.value = e.message
  }
}

async function download() {
  if (!job.value?.export_id || downloading.value) return
  downloading.value = true
  downloadError.value = ''
  try {
    await downloadExport(job.value.export_id)
  } catch (e) {
    downloadError.value = e.message || 'The download could not be started.'
  } finally {
    downloading.value = false
  }
}

// Hide the card. Only allowed once the export has ended.
function dismiss() {
  if (phase.value === 'starting' || phase.value === 'running') return
  reset()
}

// Forget everything (also used when signing out).
function reset() {
  stopPolling()
  job.value = null
  phase.value = 'idle'
  error.value = ''
  downloadError.value = ''
  cancelling.value = false
  startedHere = false
}

const busy = computed(() => phase.value === 'starting' || phase.value === 'running')
const status = computed(() => job.value?.status ?? null)
const percent = computed(() => {
  if (!job.value) return 0
  if (phase.value === 'finished' && WITH_FILE.includes(status.value)) return 100
  return job.value.percent ?? 0
})
const items = computed(() => job.value?.export_items ?? [])
const skipped = computed(() => items.value.filter((item) => item.status === 'failed'))
const processed = computed(
  () => items.value.filter((item) => item.status !== 'pending').length,
)

const title = computed(() => {
  const name = job.value?.playlist_name || 'playlist'
  if (phase.value !== 'finished' || error.value) return `Exporting ${name}`
  if (WITH_FILE.includes(status.value)) return `${name} exported`
  if (status.value === 'cancelled') return 'Export cancelled'
  return 'Export failed'
})

const detail = computed(() => {
  if (!job.value) return ''
  if (error.value) return error.value

  const total = job.value.total_songs

  if (phase.value === 'starting') return 'Starting…'

  if (phase.value === 'running') {
    if (cancelling.value) return 'Stopping…'
    if (status.value === 'pending') return 'Waiting for another export to finish…'
    if (status.value === 'packaging') return 'Creating ZIP…'
    return `Song ${Math.min(processed.value + 1, total)} of ${total}`
  }

  if (status.value === 'completed') {
    return `${plural(job.value.exported_songs, 'song')} exported.`
  }
  if (status.value === 'partial') {
    return `${job.value.exported_songs} of ${total} songs included. ${skipped.value.length} skipped.`
  }
  if (status.value === 'cancelled') return 'Nothing was downloaded.'
  return job.value.error_message || 'Something went wrong while creating the export.'
})

export function useExportJob() {
  return {
    job,
    phase,
    status,
    busy,
    percent,
    title,
    detail,
    skipped,
    error,
    downloadError,
    downloading,
    cancelling,
    finishedCount,
    start,
    resume,
    cancel,
    download,
    dismiss,
    reset,
  }
}
