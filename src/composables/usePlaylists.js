import { ref } from 'vue'
import { deletePlaylists, getPlaylists } from '@/services/playlistService.js'

// State for the Playlists page: the list, plus deleting selected playlists.
export function usePlaylists() {
  const playlists = ref([])
  const loading = ref(true)
  const error = ref('') // the list could not be loaded
  const actionError = ref('') // a delete failed
  const deleting = ref(false)

  async function load({ silent = false } = {}) {
    if (!silent) loading.value = true
    error.value = ''
    try {
      playlists.value = await getPlaylists()
    } catch (e) {
      error.value = e.message || 'Could not load your playlists.'
    } finally {
      loading.value = false
    }
  }

  async function remove(ids) {
    deleting.value = true
    actionError.value = ''
    try {
      const deleted = new Set(await deletePlaylists(ids))
      playlists.value = playlists.value.filter((p) => !deleted.has(p.playlist_id))

      if (deleted.size !== ids.length) {
        actionError.value = `Only ${deleted.size} of ${ids.length} playlists could be deleted. Your list has been refreshed.`
        await load({ silent: true })
        return false
      }
      return true
    } catch (e) {
      actionError.value = e.message || 'Could not delete the selected playlists.'
      await load({ silent: true })
      return false
    } finally {
      deleting.value = false
    }
  }

  return { playlists, loading, error, actionError, deleting, load, remove }
}