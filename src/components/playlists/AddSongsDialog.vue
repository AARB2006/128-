<script setup>
import { computed, ref, watch, watchEffect } from 'vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'

// "Add Song" on a playlist: pick any library songs that aren't in it yet.
const props = defineProps({
  open: { type: Boolean, default: false },
  songs: { type: Array, default: () => [] }, // only songs not already in the playlist
  loading: { type: Boolean, default: false },
  loadError: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['add', 'cancel', 'retry'])

const songsRef = computed(() => props.songs)
const { query, results } = useSongSearch(songsRef)
const { selectedIds, count, allSelected, someSelected, toggle, toggleAll, clear } =
  useSongSelection(results)

// Every time the popup opens it starts clean.
watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return
    query.value = ''
    clear()
  },
)

// Songs are added in the order they are listed, not the order they were ticked.
function addSelected() {
  emit(
    'add',
    props.songs.filter((song) => selectedIds.value.has(song.song_id)).map((song) => song.song_id),
  )
}

// Every checkbox in the popup, including "Select all".
const checkbox = 'mt-0.5 size-[18px] shrink-0 cursor-pointer'

const selectAll = ref(null)
watchEffect(() => {
  if (selectAll.value) selectAll.value.indeterminate = someSelected.value
})
</script>

<template>
  <AppDialog :open="open" title="Add songs" :busy="busy" wide @close="emit('cancel')">
    <p v-if="loading" class="app-muted">Loading your library…</p>

    <div v-else-if="loadError" class="app-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="app-btn" type="button" @click="emit('retry')">Try again</button>
    </div>

    <p v-else-if="!songs.length" class="app-muted">
      There are no songs left to add. Every song in your library is already in this
      playlist.
    </p>

    <template v-else>
      <input
        v-model="query"
        class="search font-inherit mb-3 min-h-11 w-full rounded-[10px] border border-border bg-surface px-4 py-0 text-[15px] text-text"
        type="search"
        placeholder="Search songs"
        aria-label="Search songs to add"
        :disabled="busy"
      />

      <p v-if="!results.length" class="app-muted none m-0">No songs match “{{ query }}”.</p>

      <template v-else>
        <label class="all flex cursor-pointer items-center gap-3 px-3 py-1.5 text-[14px] text-muted">
          <input
            ref="selectAll"
            :class="checkbox"
            type="checkbox"
            :checked="allSelected"
            :disabled="busy"
            @change="toggleAll"
          />
          <span>Select all{{ query.trim() ? ' shown' : '' }}</span>
        </label>

        <ul
          class="list m-0 max-h-[min(48vh,360px)] list-none overflow-y-auto rounded-[10px] border border-border p-0"
        >
          <li v-for="(song, index) in results" :key="song.song_id">
            <label
              class="row flex cursor-pointer items-start gap-3 border-border px-3 py-2.5 [&.selected]:bg-selected"
              :class="{ selected: selectedIds.has(song.song_id), 'border-t': index > 0 }"
            >
              <input
                :class="checkbox"
                type="checkbox"
                :checked="selectedIds.has(song.song_id)"
                :disabled="busy"
                @change="toggle(song.song_id)"
              />
              <span class="text min-w-0 wrap-anywhere">
                <span class="title block font-bold">{{ song.title }}</span>
                <span class="source block text-[13px] text-muted">{{ song.source_url }}</span>
              </span>
            </label>
          </li>
        </ul>
      </template>
    </template>

    <p v-if="error" class="app-alert message mt-4 mb-0" role="alert">{{ error }}</p>

    <div class="buttons mt-5 flex items-center justify-end gap-2">
      <span v-if="count" class="count mr-auto text-[14px] text-muted" aria-live="polite">
        {{ count }} selected
      </span>
      <button class="app-btn" type="button" :disabled="busy" @click="emit('cancel')">
        Cancel
      </button>
      <button
        class="app-btn app-btn-primary"
        type="button"
        :disabled="busy || !count"
        @click="addSelected"
      >
        {{ busy ? 'Adding…' : count ? `Add ${count} ${count === 1 ? 'song' : 'songs'}` : 'Add songs' }}
      </button>
    </div>
  </AppDialog>
</template>
