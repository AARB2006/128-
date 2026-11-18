import { ref } from 'vue'
import { getSongs } from '@/services/musicLibraryService.js'

// Loads the library songs that are not yet in a playlist, for the Add Song popup.
export function useSongPicker(getExcludedIds) {
  const open = ref(false)
  const songs = ref([])
  const loading = ref(false)
  const error = ref('')

  async function openPicker() {
    open.value = true
    loading.value = true
    error.value = ''
    songs.value = []
    try {
      const excluded = new Set(getExcludedIds())
      const all = await getSongs()
      songs.value = all.filter((song) => !excluded.has(song.song_id))
    } catch (e) {
      error.value = e.message || 'Could not load your library.'
    } finally {
      loading.value = false
    }
  }

  function close() {
    open.value = false
  }

  return { open, songs, loading, error, openPicker, close }
}