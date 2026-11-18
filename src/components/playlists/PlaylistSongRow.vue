<script setup>
import { computed } from 'vue'
import RowMenu from '@/components/ui/RowMenu.vue'

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

// Only ever link to http(s) addresses, never to anything like javascript:.
const safeUrl = computed(() =>
  /^https?:\/\//i.test(props.song.source_url) ? props.song.source_url : null,
)

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
  <tr :class="{ selected, movable: canMove }">
    <td class="check">
      <input
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${song.title}`"
        @change="$emit('toggle', song.song_id)"
      />
    </td>

    <td class="number">{{ number }}</td>

    <td class="song">
      <span class="title">{{ song.title }}</span>
      <a
        v-if="safeUrl"
        class="source"
        :href="safeUrl"
        target="_blank"
        rel="noopener noreferrer"
        draggable="false"
      >
        {{ safeUrl }}
      </a>
      <span v-else class="source">{{ song.source_url }}</span>
    </td>

    <td class="menu">
      <RowMenu :items="items" :label="`Actions for ${song.title}`" @select="onMenu" />
    </td>
  </tr>
</template>

<style scoped>
td {
  padding: 14px 16px;
  border-top: 1px solid var(--c-border);
  vertical-align: middle;
  background: var(--c-surface);
}

tr.selected td {
  background: var(--c-selected);
}

/* Rows can be grabbed anywhere, so show it. */
tr.movable td {
  cursor: grab;
}

tr.movable td.check,
tr.movable td.song a {
  cursor: pointer;
}

.check {
  width: 48px;
}

.number {
  width: 48px;
  padding-left: 0;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--c-muted);
}

.song {
  overflow-wrap: anywhere;
}

.title {
  display: block;
  font-weight: bold;
}

.source {
  display: block;
  margin-top: 2px;
  font-size: 13px;
  color: var(--c-muted);
}

.menu {
  width: 56px;
  padding-left: 0;
  text-align: right;
}

input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
</style>