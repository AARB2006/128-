<!--
A playlist's songs, with drag-and-drop reordering.
-->
<script setup>
import { computed, ref, watch, watchEffect } from 'vue'
import { useDraggable } from 'vue-draggable-plus'
import PlaylistSongRow from './PlaylistSongRow.vue'

// The songs of one playlist. Rows can be dragged by their body or by the ⋮
// button; each drop emits `reorder` with the full new list of song ids, which
// the page saves automatically.
const props = defineProps({
  songs: { type: Array, required: true }, // what to show, in order
  selectedIds: { type: Set, required: true },
  allSelected: { type: Boolean, default: false },
  someSelected: { type: Boolean, default: false },
  // False while a search is active or a save is running.
  canMove: { type: Boolean, default: true },
})
const emit = defineEmits(['toggle', 'toggle-all', 'reorder', 'move', 'remove'])

// A local copy that the drag library may reorder. It is refilled whenever the
// page hands down a new list, which is also how a failed save snaps back.
const rows = ref([...props.songs])
watch(
  () => props.songs,
  (songs) => {
    rows.value = [...songs]
  },
)

const body = ref(null)

// The look of every header cell (each adds its own left padding).
const th = 'bg-bg py-3 pr-4 text-left text-[13px] font-bold tracking-[0.04em] text-muted uppercase'

const reduceMotion =
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

// The options are a computed so `disabled` follows `canMove` as it changes.
const options = computed(() => ({
  animation: reduceMotion ? 0 : 150,
  // Links and checkboxes keep working normally. Everything else, including
  // the ⋮ button, starts a drag.
  filter: 'a, input',
  preventOnFilter: false,
  ghostClass: 'ghost',
  chosenClass: 'chosen',
  // On touch screens a short press starts the drag so scrolling still works.
  delay: 180,
  delayOnTouchOnly: true,
  touchStartThreshold: 4,
  disabled: !props.canMove,
  onUpdate: () => emit('reorder', rows.value.map((song) => song.song_id)),
}))

useDraggable(body, rows, options)

// "Some but not all" can only be shown by setting the DOM property.
const selectAll = ref(null)
watchEffect(() => {
  if (selectAll.value) selectAll.value.indeterminate = props.someSelected
})

const lastIndex = computed(() => rows.value.length - 1)
</script>

<template>
  <div class="table-wrap overflow-hidden rounded-card border border-border bg-surface">
    <table class="w-full border-collapse">
      <thead>
        <tr>
          <th :class="[th, 'check w-12 pl-4']">
            <input
              ref="selectAll"
              class="size-[18px] cursor-pointer"
              type="checkbox"
              :checked="allSelected"
              aria-label="Select all songs"
              @change="$emit('toggle-all')"
            />
          </th>
          <th :class="[th, 'number w-12 pl-0']">#</th>
          <th :class="[th, 'pl-4']">Song</th>
          <th :class="[th, 'menu w-14 pl-4']"><span class="visually-hidden">Actions</span></th>
        </tr>
      </thead>
      <tbody ref="body">
        <PlaylistSongRow
          v-for="(song, index) in rows"
          :key="song.song_id"
          :song="song"
          :number="index + 1"
          :selected="selectedIds.has(song.song_id)"
          :can-move="canMove"
          :is-first="index === 0"
          :is-last="index === lastIndex"
          @toggle="$emit('toggle', $event)"
          @move-up="emit('move', { id: $event, step: -1 })"
          @move-down="emit('move', { id: $event, step: 1 })"
          @remove="emit('remove', $event)"
        />
      </tbody>
    </table>
  </div>
</template>
