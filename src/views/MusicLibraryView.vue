<script setup>
import { onMounted, ref } from 'vue'
import { useMusicLibrary } from '@/composables/useMusicLibrary.js'
import { useSongSearch } from '@/composables/useSongSearch.js'
import { useSongSelection } from '@/composables/useSongSelection.js'
import LibraryToolbar from '@/components/library/LibraryToolbar.vue'
import SongList from '@/components/library/SongList.vue'
import LibraryEmptyState from '@/components/library/LibraryEmptyState.vue'
import DeleteSongsDialog from '@/components/library/DeleteSongsDialog.vue'

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

onMounted(() => load())

async function onConfirmDelete() {
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
    />

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
  </section>
</template>