<script setup>
import { computed } from 'vue'

const props = defineProps({
  song: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle'])

// Only ever link to http(s) addresses, never to anything like javascript:.
const safeUrl = computed(() =>
  /^https?:\/\//i.test(props.song.source_url) ? props.song.source_url : null,
)

const added = computed(() =>
  new Date(props.song.date_added).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }),
)
</script>

<template>
  <tr :class="{ selected }">
    <td class="check">
      <input
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${song.title}`"
        @change="$emit('toggle', song.song_id)"
      />
    </td>

    <td class="song">
      <span class="title">{{ song.title }}</span>
      <a
        v-if="safeUrl"
        class="source"
        :href="safeUrl"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ safeUrl }}
      </a>
      <span v-else class="source">{{ song.source_url }}</span>
    </td>

    <td class="added">{{ added }}</td>
  </tr>
</template>

<style scoped>
td {
  padding: 14px 16px;
  border-top: 1px solid var(--c-border);
  vertical-align: middle;
}

tr.selected td {
  background: var(--c-selected);
}

.check {
  width: 48px;
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

.added {
  width: 190px;
  font-size: 14px;
  color: var(--c-muted);
  white-space: nowrap;
}

input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

@media (max-width: 640px) {
  .added {
    display: none;
  }
}
</style>