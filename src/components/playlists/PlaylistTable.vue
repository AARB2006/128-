<!--
Table of the user's playlists with selection.
-->
<script setup>
import { ref, watchEffect } from 'vue'
import PlaylistRow from './PlaylistRow.vue'

const props = defineProps({
  playlists: { type: Array, required: true },
  selectedIds: { type: Set, required: true },
  allSelected: { type: Boolean, default: false },
  someSelected: { type: Boolean, default: false },
})
defineEmits(['toggle', 'toggle-all', 'export'])

// The look of every header cell.
const th = 'bg-head px-4 py-3 text-left text-[12px] font-semibold tracking-[0.06em] text-muted uppercase'

const selectAll = ref(null)
watchEffect(() => {
  if (selectAll.value) selectAll.value.indeterminate = props.someSelected
})
</script>

<template>
  <div class="table-wrap">
    <table class="w-full min-w-[560px] table-fixed border-collapse">
      <thead>
        <tr>
          <th :class="[th, 'check w-11 pr-0']">
            <input
              ref="selectAll"
              class="size-[18px] cursor-pointer"
              type="checkbox"
              :checked="allSelected"
              aria-label="Select all playlists"
              @change="$emit('toggle-all')"
            />
          </th>
          <th :class="th">Playlist</th>
          <th :class="[th, 'songs w-[90px]']">Songs</th>
          <th :class="[th, 'length w-[90px] phone:hidden']">Length</th>
          <th :class="[th, 'created w-[140px] phone:hidden']">Created</th>
          <th :class="[th, 'exported w-[150px] mobile:hidden']">Last exported</th>
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
          @export="$emit('export', $event)"
        />
      </tbody>
    </table>
  </div>
</template>
