// Shared state and actions for the import/export screen.
// State lives at module level, so every component that calls useLinks()
// sees the same values (no prop-drilling for a one-screen app).

import { computed, ref } from 'vue'
import * as api from '../api/index.js'

const playlistName = ref('') // names the exported zip; optional
const draft = ref('') // raw textarea content
const links = ref([]) // stored links, in playlist order
const max = ref(10) // replaced by the API's value on first load
const status = ref('') // '' = idle
const error = ref(null) // { message, problems } or null
const busy = ref(false)

const draftLines = computed(() => draft.value.split(/\r?\n/).filter((line) => line.trim()))
// How many links the list would hold if the draft were imported as-is.
const total = computed(() => links.value.length + draftLines.value.length)
const overLimit = computed(() => total.value > max.value)
const canImport = computed(() => !busy.value && draftLines.value.length > 0)
const canExport = computed(() => !busy.value && links.value.length > 0)

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

function showError(err, fallback) {
  error.value = {
    message: err?.message || fallback,
    problems: err?.problems ?? [],
  }
}

async function refresh() {
  try {
    const result = await api.listLinks()
    links.value = result.links
    max.value = result.max
  } catch (err) {
    showError(err, 'Could not load the link list.')
  }
}

async function importDraft() {
  if (!canImport.value) return
  busy.value = true
  error.value = null
  status.value = 'Importing...'
  try {
    // Send every line, blanks included, so reported line numbers match the textarea.
    const result = await api.importLinks(draft.value.split(/\r?\n/))
    await refresh()
    draft.value = ''

    const skipped = result.skipped.length
    status.value =
      `Imported ${plural(result.added.length, 'link')}` +
      (skipped ? ` (${plural(skipped, 'duplicate')} skipped)` : '') +
      '.'
  } catch (err) {
    showError(err, 'Import failed.')
    status.value = 'Import failed.'
  } finally {
    busy.value = false
  }
}

async function exportZip() {
  if (!canExport.value) return
  busy.value = true
  error.value = null
  status.value = 'Exporting...'
  try {
    const result = await api.exportLinks(playlistName.value.trim())
    status.value = `Exported ${result.filename}` + (result.note ? ` (${result.note})` : '') + '.'
  } catch (err) {
    showError(err, 'Export failed.')
    status.value = 'Export failed.'
  } finally {
    busy.value = false
  }
}

export function useLinks() {
  return {
    playlistName,
    draft,
    links,
    max,
    status,
    error,
    busy,
    total,
    overLimit,
    canImport,
    canExport,
    refresh,
    importDraft,
    exportZip,
  }
}