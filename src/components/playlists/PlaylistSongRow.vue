<!--
One song row inside a playlist.
-->
<script setup>
import { computed } from 'vue'
import RowMenu from '@/components/ui/RowMenu.vue'
import SongThumb from '@/components/ui/SongThumb.vue'
import { formatDuration, shortUrl } from '@/lib/format.js'

const props = defineProps({
  song: { type: Object, required: true },
  number: { type: Number, required: true }, // 1-based place in the playlist
  selected: { type: Boolean, default: false },
  // False while searching or saving: moving songs is paused.
  canMove: { type: Boolean, default: true },
  isFirst: { type: Boolean, default: false },
  isLast: { type: Boolean, default: false },
})
const emit = defineEmits(['toggle', 'move-up', 'move-down', 'remove'])

// Shared by every cell (each adds its own left padding). The row is a `group`:
// cells turn blue when it's selected, and the drag library's `ghost` (the
// placeholder where the row will land) and `chosen` (the row being dragged)
// classes on the row style the cells too.
const cell =
  'border-t border-border bg-surface py-3 pr-4 align-middle group-[.selected]:bg-selected ' +
  'group-[.ghost]:bg-selected group-[.ghost]:opacity-40 ' +
  'group-[.chosen]:shadow-[0_4px_16px_rgba(0,0,0,0.5)]'

// Rows can be grabbed anywhere (except the checkbox and link), so show it.
const grab = 'group-[.movable]:cursor-grab'

// Only ever link to http(s) addresses, never to anything like javascript:.
const safeUrl = computed(() =>
  /^https?:\/\//i.test(props.song.source_url) ? props.song.source_url : null,
)

const length = computed(() => formatDuration(props.song.duration_seconds))

// "Move up/down" are the keyboard-friendly alternative to dragging.
const items = computed(() => {
  const paused = 'Clear the search to reorder songs'
  return [
    {
      key: 'up',
      label: 'Move up',
      disabled: !props.canMove || props.isFirst,
      title: props.canMove ? undefined : paused,
    },
    {
      key: 'down',
      label: 'Move down',
      disabled: !props.canMove || props.isLast,
      title: props.canMove ? undefined : paused,
    },
    { key: 'remove', label: 'Delete song', danger: true },
  ]
})

function onMenu(key) {
  if (key === 'up') emit('move-up', props.song.song_id)
  if (key === 'down') emit('move-down', props.song.song_id)
  if (key === 'remove') emit('remove', props.song.song_id)
}
</script>

<template>
  <tr class="group" :class="{ selected, movable: canMove }">
    <td :class="[cell, 'check w-11 pl-4 pr-0 group-[.movable]:cursor-pointer']">
      <input
        class="size-[18px] cursor-pointer"
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${song.title}`"
        @change="$emit('toggle', song.song_id)"
      />
    </td>

    <td :class="[cell, grab, 'number w-16 pl-4 text-[14px] text-muted tabular-nums']">
      <span class="inline-flex items-center gap-2">
        <!-- A grip shows the row can be dragged (hidden while moving is paused). -->
        <svg
          class="size-4 opacity-0 group-[.movable]:opacity-70"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <circle cx="9" cy="6" r="1.6" />
          <circle cx="15" cy="6" r="1.6" />
          <circle cx="9" cy="12" r="1.6" />
          <circle cx="15" cy="12" r="1.6" />
          <circle cx="9" cy="18" r="1.6" />
          <circle cx="15" cy="18" r="1.6" />
        </svg>
        {{ number }}
      </span>
    </td>

    <td :class="[cell, grab, 'song pl-4']">
      <div class="flex min-w-0 items-center gap-3.5">
        <SongThumb :video-id="song.video_id" />
        <div class="min-w-0">
          <span class="title block truncate font-semibold" :title="song.title">{{ song.title }}</span>
          <a
            v-if="safeUrl"
            class="source mt-0.5 block truncate text-[13px] text-muted no-underline hover:text-text hover:underline group-[.movable]:cursor-pointer"
            :href="safeUrl"
            target="_blank"
            rel="noopener noreferrer"
            draggable="false"
          >
            {{ shortUrl(safeUrl) }}
          </a>
          <span v-else class="source mt-0.5 block truncate text-[13px] text-muted">
            {{ song.source_url }}
          </span>
        </div>
      </div>
    </td>

    <td :class="[cell, grab, 'length w-[90px] pl-4 text-[14px] text-muted tabular-nums phone:hidden']">
      {{ length }}
    </td>

    <td :class="[cell, grab, 'menu w-14 pl-0 text-right']">
      <RowMenu :items="items" :label="`Actions for ${song.title}`" @select="onMenu" />
    </td>
  </tr>
</template>
