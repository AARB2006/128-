<script setup>
import { ref, watchEffect } from 'vue'
import SongRow from './SongRow.vue'

const props = defineProps({
  songs: { type: Array, required: true },
  selectedIds: { type: Set, required: true },
  allSelected: { type: Boolean, default: false },
  someSelected: { type: Boolean, default: false },
})
defineEmits(['toggle', 'toggle-all'])

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
}
</style>