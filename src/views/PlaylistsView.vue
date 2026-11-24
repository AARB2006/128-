<!--
Playlists page: list, delete and export playlists.
-->
<script setup>
import { onMounted, ref, computed } from 'vue'
import { usePlaylists } from '@/composables/usePlaylists.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import PageToolbar from '@/components/ui/PageToolbar.vue'
import PlaylistTable from '@/components/playlists/PlaylistTable.vue'
import DeletePlaylistsDialog from '@/components/playlists/DeletePlaylistsDialog.vue'
import ExportPlaylistDialog from '@/components/export/ExportPlaylistDialog.vue'

const { playlists, loading, error, actionError, deleting, load, remove } = usePlaylists()
const { query, results } = useSongSearch(playlists, ['name', 'description'])
const {
  selectedIds,
  count: selectedCount,
  allSelected,
  someSelected,
  toggle,
  toggleAll,
  clear,
} = useSongSelection(results, 'playlist_id')

const confirmOpen = ref(false)
const exportTarget = ref(null) // the playlist chosen from a row's ⋮ menu

// With exactly one playlist ticked, the confirmation names it.
const singleName = computed(() =>
  selectedCount.value === 1
    ? (playlists.value.find((p) => selectedIds.value.has(p.playlist_id))?.name ?? '')
    : '',
)

onMounted(() => load())

async function onConfirmDelete() {
  const ok = await remove([...selectedIds.value])
  confirmOpen.value = false
  if (ok) clear()
}
</script>

<template>
  <section class="app-page">
    <h1 class="app-page-title">Playlists</h1>

    <PageToolbar v-model:query="query" placeholder="Search playlists">
      <template #left>
        <RouterLink :to="{ name: 'playlist-new' }" class="app-btn app-btn-primary">
          Add Playlist
        </RouterLink>
      </template>

      <template #right>
        <span v-if="selectedCount" class="count text-[14px] text-muted" aria-live="polite">
          {{ selectedCount }} selected
        </span>
        <button
          class="app-btn app-btn-danger"
          type="button"
          :disabled="!selectedCount"
          @click="confirmOpen = true"
        >
          Delete Playlist
        </button>
      </template>
    </PageToolbar>

    <p v-if="actionError" class="app-alert" role="alert">{{ actionError }}</p>

    <p v-if="loading" class="app-muted">Loading your playlists…</p>

    <div v-else-if="error" class="app-alert" role="alert">
      <span>{{ error }}</span>
      <button class="app-btn" type="button" @click="load()">Try again</button>
    </div>

    <div
      v-else-if="!playlists.length"
      class="app-card empty flex flex-col items-center gap-2 px-6 py-12 text-center"
    >
      <h2 class="m-0 text-[20px]">No playlists yet</h2>
      <p class="app-muted mt-0 mb-3">Create a playlist, then add songs from your Music Library.</p>
      <RouterLink :to="{ name: 'playlist-new' }" class="app-btn app-btn-primary">
        Add Playlist
      </RouterLink>
    </div>

    <p v-else-if="!results.length" class="app-muted">No playlists match “{{ query }}”.</p>

    <PlaylistTable
      v-else
      :playlists="results"
      :selected-ids="selectedIds"
      :all-selected="allSelected"
      :some-selected="someSelected"
      @toggle="toggle"
      @toggle-all="toggleAll"
      @export="exportTarget = $event"
    />

    <ExportPlaylistDialog
      :open="Boolean(exportTarget)"
      :playlist="exportTarget"
      @close="exportTarget = null"
    />

    <DeletePlaylistsDialog
      :open="confirmOpen"
      :count="selectedCount"
      :name="singleName"
      :busy="deleting"
      @confirm="onConfirmDelete"
      @cancel="confirmOpen = false"
    />
  </section>
</template>
