import { ref } from 'vue'
import { deleteSongs, getSongs } from '@/services/musicLibraryService.js'

export function useMusicLibrary() {
  const songs = ref([])
  const loading = ref(true)
  const error = ref('') // the library could not be loaded
  const actionError = ref('') // a delete failed
  const deleting = ref(false)

  // `silent` reloads without flashing the loading state.
  async function load({ silent = false } = {}) {
    if (!silent) loading.value = true
    error.value = ''
    try {
      songs.value = await getSongs()
    } catch (e) {
      error.value = e.message || 'Could not load your library.'
    } finally {
      loading.value = false
    }
  }

  async function remove(ids) {
    deleting.value = true
    actionError.value = ''
    try {
      const deleted = new Set(await deleteSongs(ids))
      songs.value = songs.value.filter((song) => !deleted.has(song.song_id))

      if (deleted.size !== ids.length) {
        actionError.value = `Only ${deleted.size} of ${ids.length} songs could be deleted. Your library has been refreshed.`
        await load({ silent: true })
        return false
      }
      return true
    } catch (e) {
      actionError.value = e.message || 'Could not delete the selected songs.'
      // A later chunk may have failed after an earlier one succeeded.
      await load({ silent: true })
      return false
    } finally {
      deleting.value = false
    }
  }

  return { songs, loading, error, actionError, deleting, load, remove }
}