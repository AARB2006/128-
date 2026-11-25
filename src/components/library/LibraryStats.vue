<!--
Summary cards above the Music Library table.
-->
<script setup>
import { computed } from 'vue'
import { formatDay, plural, totalDuration } from '@/lib/format.js'

const props = defineProps({
  // The whole library, newest first (as the library service returns it).
  songs: { type: Array, required: true },
})

const playlistCount = computed(
  () => new Set(props.songs.flatMap((song) => song.playlists.map((p) => p.playlist_id))).size,
)

// The newest song's day, and how many songs were added that day.
const lastAdded = computed(() => props.songs[0]?.date_added ?? null)
const addedThatDay = computed(() => {
  if (!lastAdded.value) return 0
  const day = new Date(lastAdded.value).toDateString()
  return props.songs.filter((song) => new Date(song.date_added).toDateString() === day).length
})

const stats = computed(() => [
  { label: 'Songs', value: props.songs.length, note: 'in your library' },
  {
    label: 'Playlists',
    value: playlistCount.value,
    note: playlistCount.value ? 'using these songs' : 'none use these songs yet',
  },
  { label: 'Total length', value: totalDuration(props.songs), note: 'of music' },
  {
    label: 'Last added',
    value: formatDay(lastAdded.value).replace(/,? \d{4}$/, ''),
    note: `${plural(addedThatDay.value, 'song')} that day`,
  },
])
</script>

<template>
  <ul class="stats m-0 grid list-none grid-cols-4 gap-3 p-0 mobile:grid-cols-2">
    <li
      v-for="stat in stats"
      :key="stat.label"
      class="min-w-0 rounded-card border border-border bg-surface px-5 py-4 phone:px-4 phone:py-3"
    >
      <span class="block text-[13px] text-muted">{{ stat.label }}</span>
      <span
        class="mt-1.5 block font-display text-[28px] leading-[1.1] font-extrabold tracking-[-0.02em] tabular-nums phone:text-[22px]"
      >
        {{ stat.value }}
      </span>
      <span class="mt-0.5 block text-[13px] text-muted">{{ stat.note }}</span>
    </li>
  </ul>
</template>
