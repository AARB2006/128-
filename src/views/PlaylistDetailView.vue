<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlaylistDetail } from '@/composables/usePlaylistDetail.js'
import { useSongPicker } from '@/composables/useSongPicker.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import PageToolbar from '@/components/ui/PageToolbar.vue'
import PlaylistSongList from '@/components/playlists/PlaylistSongList.vue'
import EditPlaylistDialog from '@/components/playlists/EditPlaylistDialog.vue'
import AddSongsDialog from '@/components/playlists/AddSongsDialog.vue'
import DeletePlaylistsDialog from '@/components/playlists/DeletePlaylistsDialog.vue'

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
</script>

<template>
  <section class="app-page">
    <RouterLink
      :to="{ name: 'playlists' }"
      class="back mb-4 inline-block text-[14px] text-muted no-underline hover:text-text hover:underline"
    >
      ← Playlists
    </RouterLink>

    <p v-if="loading" class="app-muted">Loading this playlist…</p>

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
      <header class="head mb-5">
        <h1 class="name m-0 text-[32px] leading-[1.2]">
          <button
            :class="[edit, 'name-button text-[32px] leading-[1.2] font-bold text-inherit']"
            type="button"
            title="Edit name"
            @click="openEdit('name')"
          >
            {{ playlist.name }}
          </button>
        </h1>
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
      </header>

      <PageToolbar v-model:query="query" placeholder="Search songs">
        <template #left>
          <button class="app-btn app-btn-primary" type="button" @click="openPicker">
            Add Song
          </button>
        </template>

        <template #right>
          <span v-if="selectedCount" class="count text-[14px] text-muted" aria-live="polite">
            {{ selectedCount }} selected
          </span>
          <button
            v-if="selectedCount"
            class="app-btn"
            type="button"
            :disabled="busy"
            @click="onRemove([...selectedIds])"
          >
            Remove Songs
          </button>
          <button class="app-btn app-btn-danger" type="button" @click="confirmDelete = true">
            Delete Playlist
          </button>
          <button
            class="app-btn"
            type="button"
            disabled
            title="Exporting is coming in a later update"
          >
            Export Playlist
          </button>
        </template>
      </PageToolbar>

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

      <p v-else-if="!results.length" class="app-muted">No songs match “{{ query }}”.</p>

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
        @move="({ id, step }) => moveSong(id, step)"
        @remove="onRemove([$event])"
      />

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
