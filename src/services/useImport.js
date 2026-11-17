import { computed, onScopeDispose, ref } from 'vue'
import { getActiveBatch, getBatch, startImport } from '@/services/importService.js'

export const MAX_LINKS = 10 // mirrors the backend and the database check

const POLL_MS = 1000
const MAX_POLL_FAILURES = 5

const DONE = ['completed', 'partial', 'failed']

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

export function useImport() {
  const text = ref('')
  const phase = ref('idle') // idle | starting | running | finished
  const batch = ref(null)
  const error = ref('')

  let timer = null
  let stopped = false
  let failures = 0

  // ---- what the user typed ---------------------------------------------------

  const links = computed(() =>
    text.value
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean),
  )
  const count = computed(() => links.value.length)
  const overLimit = computed(() => count.value > MAX_LINKS)
  const busy = computed(() => phase.value === 'starting' || phase.value === 'running')
  const canImport = computed(() => !busy.value && count.value > 0 && !overLimit.value)

  // ---- progress --------------------------------------------------------------

  const items = computed(() => batch.value?.import_items ?? [])
  const total = computed(() => batch.value?.total_links ?? 0)
  const processed = computed(
    () => items.value.filter((item) => item.status !== 'pending').length,
  )
  const percent = computed(() => {
    if (phase.value === 'finished') return 100
    return total.value ? Math.round((processed.value / total.value) * 100) : 0
  })

  const label = computed(() => {
    switch (phase.value) {
      case 'starting':
        return 'Starting import...'
      case 'running':
        // The link being worked on right now: 1-based, never past the total.
        return `Importing Music ${Math.min(processed.value + 1, total.value)}/${total.value}...`
      case 'finished':
        if (batch.value.status === 'failed') return 'Import failed'
        if (batch.value.status === 'partial') return 'Import finished with some problems'
        return 'Import complete'
      default:
        return 'Ready to import.'
    }
  })

  // ---- result summary --------------------------------------------------------

  const summary = computed(() => {
    if (phase.value !== 'finished' || !batch.value) return null

    const added = items.value.filter((item) => item.status === 'success').length
    const duplicates = items.value.filter((item) => item.status === 'duplicate').length
    const problems = items.value
      .filter((item) => item.status === 'failed' || item.status === 'invalid')
      .map((item) => ({
        line: item.line_no,
        url: item.submitted_url,
        reason: item.error_message || 'This link could not be imported.',
      }))

    return {
      added,
      duplicates,
      problems,
      headline:
        added > 0
          ? `${plural(added, 'song')} added to your library.`
          : 'No new songs were added.',
    }
  })

  // ---- polling ---------------------------------------------------------------

  function stopPolling() {
    clearTimeout(timer)
    timer = null
  }

  function finish() {
    stopPolling()
    phase.value = 'finished'

    // Put the links that failed back in the box so they can be fixed and retried.
    text.value = items.value
      .filter((item) => item.status === 'failed' || item.status === 'invalid')
      .map((item) => item.submitted_url)
      .join('\n')
  }

  async function poll(batchId) {
    stopPolling()

    try {
      const latest = await getBatch(batchId)
      if (stopped) return

      if (!latest) throw new Error('Import not found')

      failures = 0
      batch.value = latest

      if (DONE.includes(latest.status)) {
        finish()
        return
      }
    } catch {
      if (stopped) return

      failures += 1
      if (failures >= MAX_POLL_FAILURES) {
        error.value =
          'Lost connection while checking progress. Your import may still be ' +
          'running; reload this page to check.'
        phase.value = 'idle'
        return
      }
    }

    timer = setTimeout(() => poll(batchId), POLL_MS)
  }

  // ---- actions ---------------------------------------------------------------

  async function start() {
    if (!canImport.value) return

    error.value = ''
    batch.value = null
    failures = 0
    phase.value = 'starting'

    try {
      const started = await startImport(links.value)
      if (stopped) return

      // Show "Importing Music 1/N" straight away, before the first poll.
      batch.value = {
        batch_id: started.batch_id,
        status: 'processing',
        total_links: started.total_links,
        import_items: [],
      }
      phase.value = 'running'
      await poll(started.batch_id)
    } catch (e) {
      error.value = e.message || 'The import could not be started.'
      phase.value = 'idle'
      batch.value = null
    }
  }

  // If an import is still running (page reloaded, or opened on another device),
  // pick its progress back up instead of showing an idle page.
  async function resume() {
    try {
      const active = await getActiveBatch()
      if (stopped || !active || busy.value) return

      batch.value = active
      phase.value = 'running'
      await poll(active.batch_id)
    } catch {
      // Not being able to resume is harmless: the page just starts idle.
    }
  }

  onScopeDispose(() => {
    stopped = true
    stopPolling()
  })

  return {
    text,
    phase,
    error,
    count,
    overLimit,
    busy,
    canImport,
    total,
    processed,
    percent,
    label,
    summary,
    start,
    resume,
  }
}