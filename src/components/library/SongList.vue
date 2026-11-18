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

// The look of every header cell.
const th = 'bg-bg px-4 py-3 text-left text-[13px] font-bold tracking-[0.04em] text-muted uppercase'

// One popup shared by all rows: which playlists contain the clicked song.
const shown = ref(null)

// "Some but not all" can only be shown by setting the DOM property.
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
              aria-label="Select all songs"
              @change="$emit('toggle-all')"
            />
          </th>
          <th :class="th">Song</th>
          <th :class="[th, 'playlists w-[200px] phone:w-[110px]']">Playlists</th>
          <th :class="[th, 'added w-[190px] phone:hidden']">Date added</th>
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
        <p class="song-name mt-0 mb-3 text-muted wrap-anywhere">{{ shown.title }}</p>
        <ul
          class="names m-0 max-h-[min(48vh,320px)] list-none overflow-y-auto rounded-[10px] border border-border p-0"
        >
          <li
            v-for="playlist in shown.playlists"
            :key="playlist.playlist_id"
            class="border-border not-first:border-t"
          >
            <RouterLink
              class="block p-3 font-bold text-text no-underline wrap-anywhere hover:bg-hover"
              :to="{ name: 'playlist', params: { playlistId: playlist.playlist_id } }"
            >
              {{ playlist.name }}
            </RouterLink>
          </li>
        </ul>
        <div class="close mt-5 flex justify-end">
          <button class="app-btn" type="button" @click="shown = null">Close</button>
        </div>
      </template>
    </AppDialog>
  </div>
</template>
