<script setup>
import { ref, watchEffect } from 'vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import SongRow from './SongRow.vue'

const props = defineProps({
  songs: { type: Array, required: true },
  selectedIds: { type: Set, required: true },
  allSelected: { type: Boolean, default: false },
  someSelected: { type: Boolean, default: false },
})
defineEmits(['toggle', 'toggle-all'])

// One popup shared by all rows: which playlists contain the clicked song.
const shown = ref(null)

// "Some but not all" can only be shown by setting the DOM property.
const selectAll = ref(null)
watchEffect(() => {
  if (selectAll.value) selectAll.value.indeterminate = props.someSelected
})
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th class="check">
            <input
              ref="selectAll"
              type="checkbox"
              :checked="allSelected"
              aria-label="Select all songs"
              @change="$emit('toggle-all')"
            />
          </th>
          <th>Song</th>
          <th class="playlists">Playlists</th>
          <th class="added">Date added</th>
        </tr>
      </thead>
      <tbody>
        <SongRow
          v-for="song in songs"
          :key="song.song_id"
          :song="song"
          :selected="selectedIds.has(song.song_id)"
          @toggle="$emit('toggle', $event)"
          @show-playlists="shown = $event"
        />
      </tbody>
    </table>

    <AppDialog
      :open="!!shown"
      title="Playlists with this song"
      @close="shown = null"
    >
      <template v-if="shown">
        <p class="song-name">{{ shown.title }}</p>
        <ul class="names">
          <li v-for="playlist in shown.playlists" :key="playlist.playlist_id">
            <RouterLink
              :to="{ name: 'playlist', params: { playlistId: playlist.playlist_id } }"
            >
              {{ playlist.name }}
            </RouterLink>
          </li>
        </ul>
        <div class="close">
          <button class="app-btn" type="button" @click="shown = null">Close</button>
        </div>
      </template>
    </AppDialog>
  </div>
</template>

<style scoped>
.table-wrap {
  overflow: hidden;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-surface);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 12px 16px;
  background: var(--c-bg);
  font-size: 13px;
  font-weight: bold;
  color: var(--c-muted);
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.check {
  width: 48px;
}

.playlists {
  width: 200px;
}

.added {
  width: 190px;
}

input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

@media (max-width: 640px) {
  th.added {
    display: none;
  }

  th.playlists {
    width: 110px;
  }
}

.song-name {
  margin: 0 0 12px;
  color: var(--c-muted);
  overflow-wrap: anywhere;
}

.names {
  max-height: min(48vh, 320px);
  margin: 0;
  padding: 0;
  overflow-y: auto;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  list-style: none;
}

.names li + li {
  border-top: 1px solid var(--c-border);
}

.names a {
  display: block;
  padding: 12px;
  color: var(--c-text);
  font-weight: bold;
  text-decoration: none;
  overflow-wrap: anywhere;
}

.names a:hover {
  background: var(--c-hover);
}

.close {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>