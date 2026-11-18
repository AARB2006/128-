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
          <th class="number">#</th>
          <th>Song</th>
          <th class="menu"><span class="visually-hidden">Actions</span></th>
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

th.number {
  width: 48px;
  padding-left: 0;
}

.menu {
  width: 56px;
}

input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

/* The row being dragged: a faint placeholder where it will land. */
:deep(tr.ghost td) {
  opacity: 0.4;
  background: var(--c-selected);
}

:deep(tr.chosen td) {
  box-shadow: 0 2px 10px rgba(17, 24, 39, 0.12);
}
</style>