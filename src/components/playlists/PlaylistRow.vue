<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import RowMenu from '@/components/ui/RowMenu.vue'

const props = defineProps({
  playlist: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle'])

const router = useRouter()

const created = computed(() =>
  new Date(props.playlist.created_at).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }),
)

// Export arrives in a later update, so it is shown but switched off.
const menuItems = [
  { key: 'edit', label: 'Edit playlist' },
  {
    key: 'export',
    label: 'Export playlist',
    disabled: true,
    title: 'Exporting is coming in a later update',
  },
]

function onMenu(key) {
  if (key === 'edit') {
    router.push({ name: 'playlist', params: { playlistId: props.playlist.playlist_id } })
  }
}
</script>

<template>
  <tr :class="{ selected }">
    <td class="check">
      <input
        type="checkbox"
        :checked="selected"
        :aria-label="`Select ${playlist.name}`"
        @change="$emit('toggle', playlist.playlist_id)"
      />
    </td>

    <td class="name-cell">
      <RouterLink
        class="name"
        :to="{ name: 'playlist', params: { playlistId: playlist.playlist_id } }"
      >
        {{ playlist.name }}
      </RouterLink>
      <span v-if="playlist.description" class="description">{{ playlist.description }}</span>
    </td>

    <td class="created">{{ created }}</td>
    <td class="songs">{{ playlist.song_count }}</td>

    <td class="menu">
      <RowMenu :items="menuItems" :label="`Actions for ${playlist.name}`" @select="onMenu" />
    </td>
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

.name-cell {
  overflow-wrap: anywhere;
}

.name {
  display: block;
  color: var(--c-text);
  font-weight: bold;
  text-decoration: none;
}

.name:hover {
  text-decoration: underline;
}

.description {
  display: -webkit-box;
  margin-top: 2px;
  overflow: hidden;
  font-size: 13px;
  color: var(--c-muted);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
}

.created {
  width: 190px;
  font-size: 14px;
  color: var(--c-muted);
  white-space: nowrap;
}

.songs {
  width: 130px;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
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

@media (max-width: 640px) {
  .created {
    display: none;
  }
}
</style>