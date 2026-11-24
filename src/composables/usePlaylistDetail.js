/*
State for one playlist: load, edit, add, remove and reorder songs.
*/

import { ref } from 'vue'
import {
  addSongsToPlaylist,
  deletePlaylists,
  getPlaylist,
  getPlaylistSongs,
  removeSongsFromPlaylist,
  reorderPlaylistSongs,
  updatePlaylist,
} from '@/services/playlistService.js'

// Puts `list` into the order given by `ids`. Returns `list` unchanged if the
// ids don't match it, so a mismatch can never lose a song from the screen.
function applyOrder(list, ids) {
  const byId = new Map(list.map((song) => [song.song_id, song]))
  const ordered = ids.map((id) => byId.get(id)).filter(Boolean)
  return ordered.length === list.length ? ordered : list
}

/**
 * Everything the playlist page needs: the playlist, its songs in order, and the
 * actions on them. `getPlaylistId` is a function so it always reads the
 * current route.
 *
 * Reordering is saved automatically and optimistically: the screen changes
 * straight away, one request saves it, and if that fails the list snaps back.
 * Every change that touches the playlist's songs runs through one queue, so
 * requests can never overtake each other.
 */
export function usePlaylistDetail(getPlaylistId) {
  const playlist = ref(null)
  const songs = ref([]) // in playlist order
  const loading = ref(true)
  const loadError = ref('')
  const notFound = ref(false)
  const actionError = ref('')
  const busy = ref(false) // adding or removing songs: dragging is paused
  const saving = ref(false) // renaming
  const editError = ref('')
  const deleting = ref(false)

  // The order the server is known to have; what to snap back to on failure.
  let confirmedIds = []
  let loadToken = 0

  async function load({ silent = false, id = getPlaylistId() } = {}) {
    if (!id) return // the page is being left
    const token = ++loadToken
    if (!silent) loading.value = true
    loadError.value = ''

    try {
      const [found, rows] = await Promise.all([getPlaylist(id), getPlaylistSongs(id)])
      if (token !== loadToken) return // a newer load replaced this one

      if (!found) {
        notFound.value = true
        playlist.value = null
        songs.value = []
        confirmedIds = []
        return
      }
      notFound.value = false
      playlist.value = found
      songs.value = rows
      confirmedIds = rows.map((song) => song.song_id)
    } catch (e) {
      if (token !== loadToken) return
      const message = e.message || 'Could not load this playlist.'
      if (silent) actionError.value = message
      else loadError.value = message
    } finally {
      if (token === loadToken) loading.value = false
    }
  }

  // ---- the queue -------------------------------------------------------------
  let tail = Promise.resolve()
  let pendingIds = null

  function queue(job) {
    const run = tail.then(job)
    tail = run.catch(() => {}) // one failed job must not block the next
    return run
  }

  /** Call with the full new order after the user has moved a song. */
  function reorder(newIds) {
    const id = getPlaylistId()
    actionError.value = ''
    songs.value = applyOrder(songs.value, newIds)
    pendingIds = newIds

    return queue(async () => {
      // Several quick drags collapse into one request: the newest order wins.
      const ids = pendingIds
      if (!ids) return
      pendingIds = null

      try {
        await reorderPlaylistSongs(id, ids)
        confirmedIds = ids
      } catch (e) {
        pendingIds = null // anything queued after this was built on the failed order
        songs.value = applyOrder(songs.value, confirmedIds)
        actionError.value = /has changed/i.test(e.message)
          ? 'This playlist was changed somewhere else, so it has been reloaded.'
          : "Couldn't save the new order, so the playlist was put back as it was."
        await load({ silent: true, id })
      }
    })
  }

  /** Moves one song up (-1) or down (+1). The keyboard alternative to dragging. */
  function moveSong(songId, step) {
    const ids = songs.value.map((song) => song.song_id)
    const from = ids.indexOf(songId)
    const to = from + step
    if (from === -1 || to < 0 || to >= ids.length) return Promise.resolve()

    ;[ids[from], ids[to]] = [ids[to], ids[from]]
    return reorder(ids)
  }

  /** Takes songs out of this playlist (they stay in the library). */
  function removeSongs(songIds) {
    const id = getPlaylistId()
    busy.value = true
    actionError.value = ''

    return queue(async () => {
      try {
        const removed = new Set(await removeSongsFromPlaylist(id, songIds))
        songs.value = songs.value.filter((song) => !removed.has(song.song_id))
        confirmedIds = songs.value.map((song) => song.song_id)

        if (removed.size !== songIds.length) {
          actionError.value = `Only ${removed.size} of ${songIds.length} songs could be removed. The playlist has been refreshed.`
          await load({ silent: true, id })
          return false
        }
        return true
      } catch (e) {
        actionError.value = e.message || 'Could not remove the selected songs.'
        await load({ silent: true, id })
        return false
      } finally {
        busy.value = false
      }
    })
  }

  /** Adds library songs to the end. Resolves to { added, skipped }, or null on failure. */
  function addSongs(songIds) {
    const id = getPlaylistId()
    busy.value = true
    actionError.value = ''

    return queue(async () => {
      try {
        const added = await addSongsToPlaylist(id, songIds)
        await load({ silent: true, id }) // pick up the positions the database chose
        return { added, skipped: songIds.length - added }
      } catch (e) {
        actionError.value = e.message || 'Could not add those songs.'
        return null
      } finally {
        busy.value = false
      }
    })
  }

  /** Saves the name and description. Resolves to true, or false with editError set. */
  async function saveDetails({ name, description }) {
    saving.value = true
    editError.value = ''
    try {
      playlist.value = await updatePlaylist(getPlaylistId(), { name, description })
      return true
    } catch (e) {
      editError.value = e.message || 'Could not save your changes.'
      return false
    } finally {
      saving.value = false
    }
  }

  async function deletePlaylist() {
    deleting.value = true
    actionError.value = ''
    try {
      const deleted = await deletePlaylists([getPlaylistId()])
      if (deleted.length !== 1) throw new Error('This playlist could not be deleted.')
      return true
    } catch (e) {
      actionError.value = e.message || 'Could not delete this playlist.'
      return false
    } finally {
      deleting.value = false
    }
  }

  return {
    playlist,
    songs,
    loading,
    loadError,
    notFound,
    actionError,
    busy,
    saving,
    editError,
    deleting,
    load,
    reorder,
    moveSong,
    removeSongs,
    addSongs,
    saveDetails,
    deletePlaylist,
  }
}