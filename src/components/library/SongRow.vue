<script setup>
import { computed } from 'vue'

const props = defineProps({
  song: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle', 'show-playlists'])

// Shared by every cell. The row is a `group`, so cells turn blue when it's selected.
const cell = 'border-t border-border px-4 py-3.5 align-middle group-[.selected]:bg-selected'

// Only ever link to http(s) addresses, never to anything like javascript:.
const safeUrl = computed(() =>
  /^https?:\/\//i.test(props.song.source_url) ? props.song.source_url : null,
)

// "1 playlist", "3 playlists"
const playlistCount = computed(() => {
  const n = props.song.playlists?.length ?? 0
  return `${n} ${n === 1 ? 'playlist' : 'playlists'}`
})

const added = computed(() =>
  new Date(props.song.date_added).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }),
)
</script>

<template>
  <tr class="group" :class="{ selected }">
    <td :class="[cell, 'check w-12']">
      <input
        class="size-[18px] cursor-pointer"
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${song.title}`"
        @change="$emit('toggle', song.song_id)"
      />
    </td>

    <td :class="[cell, 'song wrap-anywhere']">
      <span class="title block font-bold">{{ song.title }}</span>
      <a
        v-if="safeUrl"
        class="source mt-0.5 block text-[13px] text-muted"
        :href="safeUrl"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ safeUrl }}
      </a>
      <span v-else class="source mt-0.5 block text-[13px] text-muted">{{ song.source_url }}</span>
    </td>

    <td :class="[cell, 'playlists w-[200px] text-[14px] wrap-anywhere phone:w-[110px]']">
      <button
        v-if="song.playlists?.length"
        class="count font-inherit -ml-2.5 cursor-pointer rounded-full border-0 bg-transparent px-2.5 py-1 text-[14px] text-text underline decoration-border underline-offset-3 hover:bg-hover hover:decoration-current"
        type="button"
        :aria-label="`${playlistCount}. Show playlist names`"
        @click="$emit('show-playlists', song)"
      >
        {{ playlistCount }}
      </button>
      <span v-else class="none text-muted" aria-label="Not in any playlist">-</span>
    </td>

    <td :class="[cell, 'added w-[190px] text-[14px] whitespace-nowrap text-muted phone:hidden']">
      {{ added }}
    </td>
  </tr>
</template>
