<!--
One row of the library song table.
-->
<script setup>
import { computed } from 'vue'
import SongThumb from '@/components/ui/SongThumb.vue'
import { formatDay, formatDuration, shortUrl } from '@/lib/format.js'

const props = defineProps({
  song: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle', 'show-playlists'])

// Shared by every cell. The row is a `group`, so cells turn blue when it's selected.
const cell = 'border-t border-border px-4 py-3 align-middle group-[.selected]:bg-selected'

// Only ever link to http(s) addresses, never to anything like javascript:.
const safeUrl = computed(() =>
  /^https?:\/\//i.test(props.song.source_url) ? props.song.source_url : null,
)

// "1 playlist", "3 playlists"
const playlistCount = computed(() => {
  const n = props.song.playlists?.length ?? 0
  return `${n} ${n === 1 ? 'playlist' : 'playlists'}`
})

const added = computed(() => formatDay(props.song.date_added))
const length = computed(() => formatDuration(props.song.duration_seconds))
</script>

<template>
  <tr class="group" :class="{ selected }">
    <td :class="[cell, 'check w-11 pr-0']">
      <input
        class="size-[18px] cursor-pointer"
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${song.title}`"
        @change="$emit('toggle', song.song_id)"
      />
    </td>

    <td :class="[cell, 'song']">
      <div class="flex min-w-0 items-center gap-3.5">
        <SongThumb :video-id="song.video_id" />
        <div class="min-w-0">
          <span class="title block truncate font-semibold" :title="song.title">{{ song.title }}</span>
          <a
            v-if="safeUrl"
            class="source mt-0.5 block truncate text-[13px] text-muted no-underline hover:text-text hover:underline"
            :href="safeUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ shortUrl(safeUrl) }}
          </a>
          <span v-else class="source mt-0.5 block truncate text-[13px] text-muted">
            {{ song.source_url }}
          </span>
        </div>
      </div>
    </td>

    <td :class="[cell, 'length w-[90px] text-[14px] text-muted tabular-nums phone:hidden']">
      {{ length }}
    </td>

    <td :class="[cell, 'playlists w-[150px] phone:w-[120px]']">
      <button
        v-if="song.playlists?.length"
        class="count app-pill app-pill-accent font-inherit cursor-pointer hover:border-accent"
        type="button"
        :aria-label="`${playlistCount}. Show playlist names`"
        @click="$emit('show-playlists', song)"
      >
        {{ playlistCount }}
      </button>
      <span v-else class="none text-muted" aria-label="Not in any playlist">-</span>
    </td>

    <td :class="[cell, 'added w-[140px] text-[14px] whitespace-nowrap text-muted phone:hidden']">
      {{ added }}
    </td>
  </tr>
</template>
