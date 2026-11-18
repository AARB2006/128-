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

// The look of every header cell.
const th = 'bg-bg px-4 py-3 text-left text-[13px] font-bold tracking-[0.04em] text-muted uppercase'

const selectAll = ref(null)
watchEffect(() => {
  if (selectAll.value) selectAll.value.indeterminate = props.someSelected
})
</script>

<template>
  <div class="table-wrap overflow-hidden rounded-card border border-border bg-surface">
    <table class="w-full border-collapse">
      <thead>
        <tr>
          <th :class="[th, 'check w-12']">
            <input
              ref="selectAll"
              class="size-[18px] cursor-pointer"
              type="checkbox"
              :checked="allSelected"
              aria-label="Select all playlists"
              @change="$emit('toggle-all')"
            />
          </th>
          <th :class="th">Name</th>
          <th :class="[th, 'created w-[190px] phone:hidden']">Date/Time Created</th>
          <th :class="[th, 'songs w-[130px]']">No. of Songs</th>
          <th :class="[th, 'menu w-14']"><span class="visually-hidden">Actions</span></th>
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
