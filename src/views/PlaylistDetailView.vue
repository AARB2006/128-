<!--
One playlist's page: edit, add or remove songs, reorder, export.
-->
<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlaylistDetail } from '@/composables/usePlaylistDetail.js'
import { useLiveRefresh } from '@/composables/useLiveRefresh.js'
import { useSongPicker } from '@/composables/useSongPicker.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import PageHeader from '@/components/ui/PageHeader.vue'
import ListCard from '@/components/ui/ListCard.vue'
import SelectionBar from '@/components/ui/SelectionBar.vue'
import ListSkeleton from '@/components/ui/ListSkeleton.vue'
import { formatDay, plural, totalDuration } from '@/lib/format.js'
import PlaylistSongList from '@/components/playlists/PlaylistSongList.vue'
import EditPlaylistDialog from '@/components/playlists/EditPlaylistDialog.vue'
import AddSongsDialog from '@/components/playlists/AddSongsDialog.vue'
import DeletePlaylistsDialog from '@/components/playlists/DeletePlaylistsDialog.vue'
import ExportPlaylistDialog from '@/components/export/ExportPlaylistDialog.vue'
import { useExportJob } from '@/composables/useExportJob.js'

const route = useRoute()
const router = useRouter()

const {
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
} = usePlaylistDetail(() => route.params.playlistId)

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

// Moving songs would be ambiguous in a filtered list, and is paused while the
// page is adding or removing songs.
const searching = computed(() => query.value.trim() !== '')
const canMove = computed(() => !searching.value && !busy.value)

const notice = ref('')

// Load whenever the playlist in the address changes.
watch(
  () => route.params.playlistId,
  (id) => {
    if (!id) return
    query.value = ''
    clear()
    notice.value = ''
    load()
  },
  { immediate: true },
)

// ---- edit name / description -------------------------------------------------
const editing = ref(false)
const editFocus = ref('name')

function openEdit(field) {
  editError.value = ''
  editFocus.value = field
  editing.value = true
}

async function onSave(values) {
  if (await saveDetails(values)) editing.value = false
}

// ---- add songs ---------------------------------------------------------------
const picker = useSongPicker(() => songs.value.map((song) => song.song_id))

async function openPicker() {
  actionError.value = ''
  notice.value = ''
  await picker.openPicker()
}

async function onAdd(ids) {
  const result = await addSongs(ids)
  if (!result) return // the error is shown inside the popup
  picker.close()
  notice.value =
    result.skipped > 0
      ? `Added ${result.added} ${result.added === 1 ? 'song' : 'songs'}. ${result.skipped} ${result.skipped === 1 ? 'was' : 'were'} already in this playlist.`
      : `Added ${result.added} ${result.added === 1 ? 'song' : 'songs'} to this playlist.`
}

// ---- remove songs ------------------------------------------------------------
async function onRemove(ids) {
  notice.value = ''
  if (await removeSongs(ids)) clear()
}

// ---- delete the playlist -----------------------------------------------------
const confirmDelete = ref(false)

async function onConfirmDelete() {
  const ok = await deletePlaylist()
  confirmDelete.value = false
  if (ok) router.replace({ name: 'playlists' })
}

const description = computed(() => playlist.value?.description || '')

// Shared by the name and description buttons: plain text until hovered.
const edit =
  'edit font-inherit -ml-1.5 block max-w-full cursor-pointer rounded-[8px] border-0 bg-transparent px-1.5 py-0.5 text-left wrap-anywhere hover:bg-hover'

// The labels under the description.
const songsLabel = computed(() => plural(songs.value.length, 'song'))
const lengthLabel = computed(() => `${totalDuration(songs.value)} total`)
const createdLabel = computed(() => `Created ${formatDay(playlist.value?.created_at)}`)

// ---- export ----------------------------------------------------------------------
const exportJob = useExportJob()
const exportOpen = ref(false)

// Stay in step with other tabs and browsers. The page can switch between
// playlists without remounting, so each message is checked against the
// playlist shown right now.
const dragging = ref(false)
const currentId = () => route.params.playlistId
const shownSongIds = () => new Set(songs.value.map((song) => song.song_id))
useLiveRefresh({
  name: 'playlist',
  tables: [
    // Renamed, or deleted elsewhere (the page then shows "Playlist not found").
    {
      table: 'playlists',
      ownerFilter: true,
      accept: (p) => (p.new?.playlist_id ?? p.old?.playlist_id) === currentId(),
    },
    // Songs added, removed or reordered. Deletes carry no playlist id, so any
    // delete triggers a quiet reload.
    {
      table: 'playlist_songs',
      accept: (p) => p.eventType === 'DELETE' || p.new?.playlist_id === currentId(),
    },
    // A song in this playlist changed (deleting a song also deletes its
    // playlist_songs row, which is caught above).
    {
      table: 'songs',
      ownerFilter: true,
      accept: (p) => p.eventType !== 'DELETE' && shownSongIds().has(p.new?.song_id),
    },
  ],
  refresh: () => load({ silent: true }),
  paused: () =>
    busy.value ||
    saving.value ||
    deleting.value ||
    editing.value ||
    confirmDelete.value ||
    exportOpen.value ||
    dragging.value,
})

const exportingThis = computed(
  () =>
    exportJob.busy.value && exportJob.job.value?.playlist_id === playlist.value?.playlist_id,
)
const exportTitle = computed(() => {
  if (!songs.value.length) return 'Add songs to export this playlist'
  if (exportJob.busy.value && !exportingThis.value) return 'Another export is running'
  return undefined
})
const exportTarget = computed(() =>
  playlist.value
    ? {
        playlist_id: playlist.value.playlist_id,
        name: playlist.value.name,
        song_count: songs.value.length,
      }
    : null,
)
</script>

<template>
  <section class="app-page">
    <RouterLink
      :to="{ name: 'playlists' }"
      class="back mb-3.5 inline-flex items-center gap-1.5 text-[14px] text-muted no-underline hover:text-text"
    >
      <svg
        class="size-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M19 12H5M12 19l-7-7 7-7" />
      </svg>
      Playlists
    </RouterLink>

    <!-- Placeholders shaped like the page while the playlist loads. -->
    <div v-if="loading" class="loading">
      <div class="mb-6" aria-hidden="true">
        <span class="app-skeleton h-10 w-[min(360px,80%)] rounded-[8px]"></span>
        <span class="app-skeleton mt-3 h-4 w-40"></span>
        <span class="mt-3.5 flex gap-2">
          <span class="app-skeleton h-6 w-20 rounded-full"></span>
          <span class="app-skeleton h-6 w-24 rounded-full"></span>
          <span class="app-skeleton h-6 w-40 rounded-full"></span>
        </span>
      </div>
      <ListSkeleton label="Loading this playlist" :rows="5" lead="thumb" :columns="['90px']" />
    </div>

    <div v-else-if="loadError" class="app-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="app-btn" type="button" @click="load()">Try again</button>
    </div>

    <div
      v-else-if="notFound"
      class="app-card missing flex flex-col items-center gap-2 px-6 py-12 text-center"
    >
      <h1 class="m-0 text-[20px]">Playlist not found</h1>
      <p class="app-muted mt-0 mb-3">It may have been deleted, or the link is wrong.</p>
      <RouterLink :to="{ name: 'playlists' }" class="app-btn app-btn-primary">
        Back to Playlists
      </RouterLink>
    </div>

    <template v-else-if="playlist">
      <!-- The name and description look like text but can be clicked to edit. -->
      <PageHeader>
        <template #title>
          <h1 class="name m-0">
            <button
              :class="[
                edit,
                'name-button font-display text-[40px] leading-[1.15] font-extrabold tracking-[-0.02em] text-inherit phone:text-[30px]',
              ]"
              type="button"
              title="Edit name"
              @click="openEdit('name')"
            >
              {{ playlist.name }}
            </button>
          </h1>
        </template>
        <template #below>
          <button
            :class="[
              edit,
              'description-button mt-1 text-[15px] leading-[1.5] whitespace-pre-line text-muted [&.is-empty]:italic',
              { 'is-empty': !description },
            ]"
            type="button"
            :title="description ? 'Edit description' : 'Add a description'"
            @click="openEdit('description')"
          >
            {{ description || 'Add a description' }}
          </button>
          <p class="meta mt-2.5 mb-0 flex flex-wrap gap-2">
            <span class="app-pill app-pill-accent">{{ songsLabel }}</span>
            <span class="app-pill">{{ lengthLabel }}</span>
            <span class="app-pill">{{ createdLabel }}</span>
          </p>
        </template>
        <template #actions>
          <button
            class="app-btn app-btn-danger min-h-11"
            type="button"
            @click="confirmDelete = true"
          >
            Delete Playlist
          </button>
          <button
            class="app-btn min-h-11"
            type="button"
            :disabled="!songs.length || exportJob.busy.value"
            :title="exportTitle"
            @click="exportOpen = true"
          >
            {{ exportingThis ? 'Exporting…' : 'Export Playlist' }}
          </button>
          <button
            class="app-btn app-btn-primary min-h-11 px-[18px]"
            type="button"
            @click="openPicker"
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
            Add Song
          </button>
        </template>
      </PageHeader>

      <p v-if="notice" class="app-success" role="status">{{ notice }}</p>
      <p v-if="actionError && !picker.open.value" class="app-alert" role="alert">
        {{ actionError }}
      </p>

      <div
        v-if="!songs.length"
        class="app-card empty flex flex-col items-center gap-2 px-6 py-12 text-center"
      >
        <h2 class="m-0 text-[20px]">This playlist is empty</h2>
        <p class="app-muted mt-0 mb-3">Add songs from your Music Library.</p>
        <button class="app-btn app-btn-primary" type="button" @click="openPicker">
          Add Song
        </button>
      </div>

      <ListCard v-else v-model:query="query" placeholder="Search songs">
        <template #tools>
          <SelectionBar v-if="selectedCount" :count="selectedCount" @clear="clear">
            <button
              class="app-btn min-h-9"
              type="button"
              :disabled="busy"
              @click="onRemove([...selectedIds])"
            >
              Remove Songs
            </button>
          </SelectionBar>
          <span v-else class="hint pr-1 text-[14px] text-muted phone:hidden">
            {{ searching ? 'Clear the search to reorder songs' : 'Drag rows to reorder' }}
          </span>
        </template>

        <p v-if="!results.length" class="m-0 px-4 py-10 text-center text-muted">
          No songs match “{{ query }}”.
        </p>
        <PlaylistSongList
          v-else
          :songs="results"
          :selected-ids="selectedIds"
          :all-selected="allSelected"
          :some-selected="someSelected"
          :can-move="canMove"
          @toggle="toggle"
          @toggle-all="toggleAll"
          @reorder="reorder"
          @drag-start="dragging = true"
          @drag-end="dragging = false"
          @move="({ id, step }) => moveSong(id, step)"
          @remove="onRemove([$event])"
        />

        <template #footer>
          <span>{{ songsLabel }}</span>
          <span>Changes save automatically</span>
        </template>
      </ListCard>

      <EditPlaylistDialog
        :open="editing"
        :playlist="playlist"
        :focus="editFocus"
        :busy="saving"
        :error="editError"
        @save="onSave"
        @cancel="editing = false"
      />

      <AddSongsDialog
        :open="picker.open.value"
        :songs="picker.songs.value"
        :loading="picker.loading.value"
        :load-error="picker.error.value"
        :busy="busy"
        :error="actionError"
        @add="onAdd"
        @retry="picker.openPicker"
        @cancel="picker.close"
      />

      <ExportPlaylistDialog
        :open="exportOpen"
        :playlist="exportTarget"
        @close="exportOpen = false"
      />

      <DeletePlaylistsDialog
        :open="confirmDelete"
        :count="1"
        :name="playlist.name"
        :busy="deleting"
        @confirm="onConfirmDelete"
        @cancel="confirmDelete = false"
      />
    </template>
  </section>
</template>
