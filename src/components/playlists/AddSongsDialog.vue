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
        class="search"
        type="search"
        placeholder="Search songs"
        aria-label="Search songs to add"
        :disabled="busy"
      />

      <p v-if="!results.length" class="app-muted none">No songs match “{{ query }}”.</p>

      <template v-else>
        <label class="all">
          <input
            ref="selectAll"
            type="checkbox"
            :checked="allSelected"
            :disabled="busy"
            @change="toggleAll"
          />
          <span>Select all{{ query.trim() ? ' shown' : '' }}</span>
        </label>

        <ul class="list">
          <li v-for="song in results" :key="song.song_id">
            <label class="row" :class="{ selected: selectedIds.has(song.song_id) }">
              <input
                type="checkbox"
                :checked="selectedIds.has(song.song_id)"
                :disabled="busy"
                @change="toggle(song.song_id)"
              />
              <span class="text">
                <span class="title">{{ song.title }}</span>
                <span class="source">{{ song.source_url }}</span>
              </span>
            </label>
          </li>
        </ul>
      </template>
    </template>

    <p v-if="error" class="app-alert message" role="alert">{{ error }}</p>

    <div class="buttons">
      <span v-if="count" class="count" aria-live="polite">{{ count }} selected</span>
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

<style scoped>
.search {
  width: 100%;
  min-height: 44px;
  margin-bottom: 12px;
  padding: 0 16px;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  background: var(--c-surface);
  color: var(--c-text);
  font: inherit;
  font-size: 15px;
}

.none {
  margin: 0;
}

.all {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  font-size: 14px;
  color: var(--c-muted);
  cursor: pointer;
}

.list {
  max-height: min(48vh, 360px);
  margin: 0;
  padding: 0;
  overflow-y: auto;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  list-style: none;
}

.row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  border-top: 1px solid var(--c-border);
  cursor: pointer;
}

li:first-child .row {
  border-top: 0;
}

.row.selected {
  background: var(--c-selected);
}

.text {
  min-width: 0;
  overflow-wrap: anywhere;
}

.title {
  display: block;
  font-weight: bold;
}

.source {
  display: block;
  font-size: 13px;
  color: var(--c-muted);
}

input[type='checkbox'] {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  flex-shrink: 0;
  cursor: pointer;
}

.message {
  margin: 16px 0 0;
}

.buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.count {
  margin-right: auto;
  font-size: 14px;
  color: var(--c-muted);
}
</style>