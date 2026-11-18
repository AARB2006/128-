import { ref } from 'vue'
import { getPlaylists, addSongsToPlaylist } from '@/services/playlistService.js'

// The Music Library's "Add to Playlist" popup: load the user's playlists, then
// add the ticked songs to the one they choose.
export function useAddToPlaylist() {
  const open = ref(false)
  const playlists = ref([])
  const loading = ref(false)
  const loadError = ref('')
  const busy = ref(false)
  const submitError = ref('')

  async function openDialog() {
    open.value = true
    loading.value = true
    loadError.value = ''
    submitError.value = ''
    try {
      playlists.value = await getPlaylists()
    } catch (e) {
      loadError.value = e.message || 'Could not load your playlists.'
    } finally {
      loading.value = false
    }
  }

  function close() {
    if (!busy.value) open.value = false
  }

  /** Resolves to { name, added, skipped } on success, or null (submitError is set). */
  async function submit(playlistId, songIds) {
    busy.value = true
    submitError.value = ''
    try {
      const added = await addSongsToPlaylist(playlistId, songIds)
      const name = playlists.value.find((p) => p.playlist_id === playlistId)?.name ?? ''
      open.value = false
      return { name, added, skipped: songIds.length - added }
    } catch (e) {
      submitError.value = e.message || 'Could not add the songs to that playlist.'
      return null
    } finally {
      busy.value = false
    }
  }

  return { open, playlists, loading, loadError, busy, submitError, openDialog, close, submit }
}