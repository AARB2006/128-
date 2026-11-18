<script setup>
import { ref, watchEffect } from 'vue'
import PlaylistRow from './PlaylistRow.vue'

const props = defineProps({
  playlists: { type: Array, required: true },
  selectedIds: { type: Set, required: true },
  allSelected: { type: Boolean, default: false },
  someSelected: { type: Boolean, default: false },
})
defineEmits(['toggle', 'toggle-all'])

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
              aria-label="Select all playlists"
              @change="$emit('toggle-all')"
            />
          </th>
          <th>Name</th>
          <th class="created">Date/Time Created</th>
          <th class="songs">No. of Songs</th>
          <th class="menu"><span class="visually-hidden">Actions</span></th>
        </tr>
      </thead>
      <tbody>
        <PlaylistRow
          v-for="playlist in playlists"
          :key="playlist.playlist_id"
          :playlist="playlist"
          :selected="selectedIds.has(playlist.playlist_id)"
          @toggle="$emit('toggle', $event)"
        />
      </tbody>
    </table>
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

.created {
  width: 190px;
}

.songs {
  width: 130px;
}

.menu {
  width: 56px;
}

input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@media (max-width: 640px) {
  th.created {
    display: none;
  }
}
</style>