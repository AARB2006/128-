<!--
Playlists page: list, delete and export playlists.
-->
<script setup>
import { onMounted, ref, computed } from 'vue'
import { usePlaylists } from '@/composables/usePlaylists.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import { deleteIsOurs, exportChangeMatters, useLiveRefresh } from '@/composables/useLiveRefresh.js'
import PageHeader from '@/components/ui/PageHeader.vue'
import ListCard from '@/components/ui/ListCard.vue'
import SelectionBar from '@/components/ui/SelectionBar.vue'
import ListSkeleton from '@/components/ui/ListSkeleton.vue'
import { plural } from '@/lib/format.js'
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

// Stay in step with other tabs and browsers.
const playlistIds = () => new Set(playlists.value.map((p) => p.playlist_id))
useLiveRefresh({
  name: 'playlists',
  tables: [
    { table: 'playlists', ownerFilter: true, accept: (p) => deleteIsOurs(p, 'playlist_id', playlistIds) },
    { table: 'playlist_songs' }, // song counts and lengths
    { table: 'exports', ownerFilter: true, accept: exportChangeMatters }, // Last exported
  ],
  refresh: () => load({ silent: true }),
  paused: () => confirmOpen.value || deleting.value || Boolean(exportTarget.value),
})

async function onConfirmDelete() {
  const ok = await remove([...selectedIds.value])
  confirmOpen.value = false
  if (ok) clear()
}
</script>

<template>
  <section class="app-page">
    <PageHeader
      title="Playlists"
      description="Group songs from your library, put them in order, and export them as MP3s."
    >
      <template #actions>
        <RouterLink
          :to="{ name: 'playlist-new' }"
          class="app-btn app-btn-primary min-h-11 px-[18px]"
        >
          <svg
            class="size-[18px]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.2"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add Playlist
        </RouterLink>
      </template>
    </PageHeader>

    <p v-if="actionError" class="app-alert" role="alert">{{ actionError }}</p>

    <ListSkeleton
      v-if="loading"
      label="Loading your playlists"
      :rows="4"
      lead="tile"
      :columns="['90px', '90px', '140px', '150px']"
    />

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

    <ListCard v-else v-model:query="query" placeholder="Search playlists">
      <template #tools>
        <SelectionBar v-if="selectedCount" :count="selectedCount" @clear="clear">
          <button class="app-btn app-btn-danger min-h-9" type="button" @click="confirmOpen = true">
            Delete
          </button>
        </SelectionBar>
        <span v-else class="hint pr-1 text-[14px] text-muted phone:hidden">
          Tick playlists to delete them
        </span>
      </template>

      <p v-if="!results.length" class="m-0 px-4 py-10 text-center text-muted">
        No playlists match “{{ query }}”.
      </p>
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

      <template #footer>
        <span>{{ plural(playlists.length, 'playlist') }}</span>
        <span>Showing {{ results.length }} of {{ playlists.length }}</span>
      </template>
    </ListCard>

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
