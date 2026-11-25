<!--
Music Library page: browse, search, delete songs and add them to playlists.
-->
<script setup>
import { onMounted, ref } from 'vue'
import { useMusicLibrary } from '@/composables/useMusicLibrary.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import PageHeader from '@/components/ui/PageHeader.vue'
import ListCard from '@/components/ui/ListCard.vue'
import SelectionBar from '@/components/ui/SelectionBar.vue'
import ListSkeleton from '@/components/ui/ListSkeleton.vue'
import LibraryStats from '@/components/library/LibraryStats.vue'
import SongList from '@/components/library/SongList.vue'
import LibraryEmptyState from '@/components/library/LibraryEmptyState.vue'
import DeleteSongsDialog from '@/components/library/DeleteSongsDialog.vue'
import ChoosePlaylistDialog from '@/components/playlists/ChoosePlaylistDialog.vue'
import { useAddToPlaylist } from '@/composables/useAddToPlaylist.js'
import { plural } from '@/lib/format.js'

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

  const added = plural(result.added, 'song')
  notice.value =
    result.skipped > 0
      ? `Added ${added} to “${result.name}”. ${result.skipped} ${result.skipped === 1 ? 'was' : 'were'} already in it.`
      : `Added ${added} to “${result.name}”.`
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
    <PageHeader
      title="Music Library"
      description="Every song you've imported. Select songs to add them to a playlist."
    >
      <template #actions>
        <RouterLink :to="{ name: 'import' }" class="app-btn app-btn-primary min-h-11 px-[18px]">
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
          Import Music
        </RouterLink>
      </template>
    </PageHeader>

    <p v-if="notice" class="app-success" role="status">{{ notice }}</p>
    <p v-if="actionError" class="app-alert" role="alert">{{ actionError }}</p>

    <!-- Placeholders shaped like the page while the library loads. -->
    <div v-if="loading" class="loading">
      <ul class="m-0 mb-6 grid list-none grid-cols-4 gap-3 p-0 mobile:grid-cols-2" aria-hidden="true">
        <li
          v-for="n in 4"
          :key="n"
          class="rounded-card border border-border bg-surface px-5 py-4 phone:px-4 phone:py-3"
        >
          <span class="app-skeleton h-3 w-16"></span>
          <span class="app-skeleton mt-3 h-7 w-12"></span>
          <span class="app-skeleton mt-2.5 h-3 w-24"></span>
        </li>
      </ul>
      <ListSkeleton
        label="Loading your library"
        :rows="6"
        lead="thumb"
        :columns="['90px', '150px', '140px']"
      />
    </div>

    <div v-else-if="error" class="app-alert" role="alert">
      <span>{{ error }}</span>
      <button class="app-btn" type="button" @click="load()">Try again</button>
    </div>

    <LibraryEmptyState v-else-if="!songs.length" />

    <template v-else>
      <LibraryStats :songs="songs" class="mb-6" />

      <ListCard v-model:query="query" placeholder="Search songs">
        <template #tools>
          <SelectionBar v-if="selectedCount" :count="selectedCount" @clear="clear">
            <button
              class="app-btn min-h-9"
              type="button"
              @click="notice = ''; playlistDialog.openDialog()"
            >
              Add to Playlist
            </button>
            <button class="app-btn app-btn-danger min-h-9" type="button" @click="confirmOpen = true">
              Delete
            </button>
          </SelectionBar>
          <span v-else class="hint pr-1 text-[14px] text-muted phone:hidden">
            Tick songs to add them to a playlist or delete them
          </span>
        </template>

        <p v-if="!results.length" class="m-0 px-4 py-10 text-center text-muted">
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

        <template #footer>
          <span>{{ plural(songs.length, 'song') }}</span>
          <span>Showing {{ results.length }} of {{ songs.length }}</span>
        </template>
      </ListCard>
    </template>

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