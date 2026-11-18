<script setup>
import { onMounted, ref } from 'vue'
import { useMusicLibrary } from '@/composables/useMusicLibrary.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import LibraryToolbar from '@/components/library/LibraryToolbar.vue'
import SongList from '@/components/library/SongList.vue'
import LibraryEmptyState from '@/components/library/LibraryEmptyState.vue'
import DeleteSongsDialog from '@/components/library/DeleteSongsDialog.vue'
import ChoosePlaylistDialog from '@/components/playlists/ChoosePlaylistDialog.vue'
import { useAddToPlaylist } from '@/composables/useAddToPlaylist.js'

const { songs, loading, error, actionError, deleting, load, remove } =
  useMusicLibrary()
const { query, results } = useSongSearch(songs)
const {
  selectedIds,
  count: selectedCount,
  allSelected,
  someSelected,
  toggle,
  toggleAll,
  clear,
} = useSongSelection(results)

const confirmOpen = ref(false)

const playlistDialog = useAddToPlaylist()
const notice = ref('')

onMounted(() => load())

async function onChoosePlaylist(playlistId) {
  // Songs are added in the order the library lists them.
  const ids = songs.value
    .filter((song) => selectedIds.value.has(song.song_id))
    .map((song) => song.song_id)

  const result = await playlistDialog.submit(playlistId, ids)
  if (!result) return // the error is shown inside the popup

  const plural = (n) => `${n} ${n === 1 ? 'song' : 'songs'}`
  notice.value =
    result.skipped > 0
      ? `Added ${plural(result.added)} to “${result.name}”. ${result.skipped} ${result.skipped === 1 ? 'was' : 'were'} already in it.`
      : `Added ${plural(result.added)} to “${result.name}”.`
  clear()
  await load({ silent: true }) // refresh the Playlist column
}

async function onConfirmDelete() {
  notice.value = ''
  const ok = await remove([...selectedIds.value])
  confirmOpen.value = false
  if (ok) clear()
}
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">Music Library</h1>

    <LibraryToolbar
      v-model:query="query"
      :selected-count="selectedCount"
      @delete="confirmOpen = true"
      @add-to-playlist="notice = ''; playlistDialog.openDialog()"
    />

    <p v-if="notice" class="app-success" role="status">{{ notice }}</p>
    <p v-if="actionError" class="app-alert" role="alert">{{ actionError }}</p>

    <p v-if="loading" class="app-muted">Loading your library…</p>

    <div v-else-if="error" class="app-alert" role="alert">
      <span>{{ error }}</span>
      <button class="app-btn" type="button" @click="load()">Try again</button>
    </div>

    <LibraryEmptyState v-else-if="!songs.length" />

    <p v-else-if="!results.length" class="app-muted">
      No songs match “{{ query }}”.
    </p>

    <SongList
      v-else
      :songs="results"
      :selected-ids="selectedIds"
      :all-selected="allSelected"
      :some-selected="someSelected"
      @toggle="toggle"
      @toggle-all="toggleAll"
    />

    <DeleteSongsDialog
      :open="confirmOpen"
      :count="selectedCount"
      :busy="deleting"
      @confirm="onConfirmDelete"
      @cancel="confirmOpen = false"
    />

    <ChoosePlaylistDialog
      :open="playlistDialog.open.value"
      :count="selectedCount"
      :playlists="playlistDialog.playlists.value"
      :loading="playlistDialog.loading.value"
      :load-error="playlistDialog.loadError.value"
      :busy="playlistDialog.busy.value"
      :error="playlistDialog.submitError.value"
      @choose="onChoosePlaylist"
      @retry="playlistDialog.openDialog"
      @cancel="playlistDialog.close"
    />
  </section>
</template>