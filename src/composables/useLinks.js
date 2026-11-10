
import { computed, ref } from 'vue'
import * as api from '../api/index.js'

const playlistName = ref('')
const draft = ref('')

const playlists = ref([])
const selectedPlaylistId = ref(null)

const max = ref(10)

const status = ref('')
const error = ref(null)
const busy = ref(false)
const exporting = ref(false)

// Flatten playlists for compatibility with existing components.
const links = computed(() =>
  playlists.value.flatMap((playlist) =>
    playlist.tracks.map((track) => ({
      id: `${playlist.playlist_id}-${track.song_id}`,
      url: track.source_url,
      title: track.title,
      position: track.position,
      playlist_name: playlist.name,
    })),
  ),
)

const selectedPlaylist = computed(() =>
  playlists.value.find(
    (playlist) => playlist.playlist_id === selectedPlaylistId.value,
  ) || null,
)

const draftLines = computed(() =>
  draft.value.split(/\r?\n/).filter((line) => line.trim()),
)

const draftCount = computed(() => draftLines.value.length)
const overLimit = computed(() => draftCount.value > max.value)

const canImport = computed(
  () =>
    !busy.value &&
    playlistName.value.trim().length > 0 &&
    draftCount.value > 0 &&
    !overLimit.value,
)

const canExport = computed(
  () =>
    !busy.value &&
    selectedPlaylist.value !== null &&
    selectedPlaylist.value.track_count > 0,
)

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

function showError(err, fallback) {
  error.value = {
    message: err?.message || fallback,
    problems: err?.problems ?? [],
  }
}

async function refresh() {
  try {
    const result = await api.listPlaylists()

    playlists.value = result.playlists
    max.value = result.max_links_per_import

    // Clear the selection if the selected playlist no longer exists.
    if (
      !playlists.value.some(
        (playlist) => playlist.playlist_id === selectedPlaylistId.value,
      )
    ) {
      selectedPlaylistId.value = null
    }
  } catch (err) {
    showError(err, 'Could not load playlist history.')
  }
}

async function importDraft() {
  if (!canImport.value) return

  busy.value = true
  error.value = null
  status.value = 'Importing...'

  try {
    const result = await api.importPlaylist(
      playlistName.value.trim(),
      draft.value.split(/\r?\n/),
    )

    await refresh()

    // Select the newly created playlist.
    selectedPlaylistId.value = result.playlist_id

    draft.value = ''

    const skipped = result.skipped.length

    status.value =
      `Created "${result.name}" with ${plural(result.track_count, 'track')}` +
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
  exporting.value = true
  error.value = null
  status.value = 'Preparing your MP3 files and ZIP archive...'

  try {
    const result = await api.exportPlaylist(
      selectedPlaylistId.value,
    )

    status.value = `Download started: ${result.filename}`
  } catch (err) {
    showError(err, 'Export failed.')
    status.value = 'Export failed.'
  } finally {
    exporting.value = false
    busy.value = false
  }
}

export function useLinks() {
  return {
    playlistName,
    draft,
    playlists,
    selectedPlaylistId,
    selectedPlaylist,
    links,
    max,
    status,
    error,
    busy,
    exporting,
    draftCount,
    overLimit,
    canImport,
    canExport,
    refresh,
    importDraft,
    exportZip,
  }
}
